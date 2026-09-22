"""One final-test evaluation of a frozen local artifact. Never tunes using test results."""
import argparse
import hashlib
import json
import pickle
from pathlib import Path
import time
import numpy as np
from sklearn.metrics import (precision_score, recall_score, f1_score, average_precision_score,
    precision_recall_curve, auc, roc_auc_score, confusion_matrix, brier_score_loss, log_loss, cohen_kappa_score)
from .data import read_dataset
from .train import margin, transform, write_json

def metrics(y, probabilities, threshold):
    y, p = np.asarray(y), np.asarray(probabilities)
    if y.ndim != 1 or p.shape != y.shape or not len(y) or not np.isin(y,[0,1]).all() or not np.isfinite(p).all() or ((p<0)|(p>1)).any() or not 0<=threshold<=1:
        raise ValueError("Expected nonempty binary labels and finite probabilities/threshold in [0,1]")
    pred = p >= threshold
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0,1]).ravel()
    both = len(np.unique(y)) == 2
    precision, recall, _ = precision_recall_curve(y, p) if both else (None,None,None)
    bins = []
    for i in range(10):
        mask = (p >= i/10) & ((p < (i+1)/10) if i < 9 else (p <= 1))
        bins.append(dict(count=int(mask.sum()), mean_probability=float(p[mask].mean()) if mask.any() else None,
                         observed_positive_rate=float(y[mask].mean()) if mask.any() else None))
    fpr, fnr = (float(fp/(fp+tn)) if fp+tn else None), (float(fn/(fn+tp)) if fn+tp else None)
    return dict(accuracy=float(np.mean(pred==y)),specificity=1-fpr if fpr is not None else None,
        precision=float(precision_score(y,pred,zero_division=0)), recall=1-fnr if fnr is not None else None,
        f1=float(f1_score(y,pred,zero_division=0)), pr_auc=float(auc(recall,precision)) if both else None, average_precision=float(average_precision_score(y,p)) if both else None,
        roc_auc=float(roc_auc_score(y,p)) if both else None, false_positive_rate=fpr, false_negative_rate=fnr,
        brier=float(brier_score_loss(y,p)), log_loss=float(log_loss(y,p,labels=[0,1])), reliability_bins=bins,
        expected_calibration_error=sum(b["count"]/len(y)*abs(b["mean_probability"]-b["observed_positive_rate"]) for b in bins if b["count"]),
        confusion=dict(tn=int(tn),fp=int(fp),fn=int(fn),tp=int(tp)),
        hypothetical_base_rates=[dict(prevalence=r, estimated_positive_predictive_value=(1-fnr)*r/max(1e-15,(1-fnr)*r+fpr*(1-r))) for r in (.001,.01,.05)] if both else [])

def language_metrics(rows, probabilities, threshold):
    result={}
    for language in ("en","taglish","fil"):
        indices=[i for i,r in enumerate(rows) if r.get("language")==language]
        labels=[int(rows[i]["label"]) for i in indices]
        support={"ham":labels.count(0),"smishing":labels.count(1)}
        adequate=len(indices)>=20 and min(support.values())>=5
        result[language]=dict(records=len(indices),support=support,
            metrics=metrics(labels,np.asarray(probabilities)[indices],threshold) if adequate else None,
            note="Descriptive small-sample metrics; no precision/representativeness guarantee" if adequate else "Not estimated: require >=20 records and >=5 per class; collect more independent examples")
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("dataset", type=Path); p.add_argument("run", type=Path)
    p.add_argument("--selection", type=Path, required=True)
    p.add_argument("--allow-permissive-comparison", action="store_true")
    args = p.parse_args()
    evaluate_selected(args.dataset, args.run, args.selection, args.allow_permissive_comparison)


def evaluate_selected(dataset, run, selection, allow_permissive=False):
    from .compare import verify_selection
    from .import_data import agreement
    from types import SimpleNamespace
    args = SimpleNamespace(dataset=dataset, run=run)
    selected = verify_selection(run, selection)
    if selected["split"] in {"random", "time"} and not allow_permissive:
        raise ValueError("Permissive comparison requires --allow-permissive-comparison; it is not template-isolated")
    if (args.run/"final-test.json").exists():
        raise ValueError("Final evaluation already exists. Do not retune against this test set.")
    metadata = json.loads((args.run/"run.json").read_text(encoding="utf-8"))
    if hashlib.sha256(args.dataset.read_bytes()).hexdigest() != metadata["dataset_sha256"]:
        raise ValueError("Dataset changed after split freeze")
    rows = {r["id"]:r for r in read_dataset(args.dataset)}
    manifest = json.loads((args.run/"splits.json").read_text(encoding="utf-8"))
    test = [rows[i] for i in manifest["test"]]
    with open(args.run/"research-model.pkl", "rb") as f:
        artifact = pickle.load(f)  # Only the trusted local training output.
    started = time.perf_counter()
    x = transform(artifact["vectorizer"], [r["text_redacted"] for r in test], artifact["condition"], url_rows=test)
    probabilities = artifact["calibrator"].predict_proba(margin(artifact["model"], x).reshape(-1,1))[:,1]
    host_batch_seconds = time.perf_counter()-started
    result = metrics([int(r["label"]) for r in test], probabilities, artifact["threshold"])
    result["by_language"] = language_metrics(test, probabilities, artifact["threshold"])
    from .uncertainty import cluster_intervals
    from datetime import datetime, timezone
    import subprocess
    result['confidence_intervals'] = cluster_intervals([int(r['label']) for r in test], probabilities,
        [manifest['groups'][r['id']] for r in test], artifact['threshold'], seed=metadata['seed'])
    result['evaluation_timestamp_utc'] = datetime.now(timezone.utc).isoformat()
    result['git_commit'] = subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    result['training_data_sha256'] = metadata['dataset_sha256']
    result['split_manifest_sha256'] = hashlib.sha256((run/'splits.json').read_bytes()).hexdigest()
    result['model_sha256'] = hashlib.sha256((run/'research-model.pkl').read_bytes()).hexdigest()
    result['preprocessing_version'] = metadata['preprocessing_version']
    result['feature_configuration'] = {k:metadata[k] for k in ('condition','analyzer')}
    result['errors'] = [dict(id=r['id'],label=int(r['label']),predicted=int(p>=artifact['threshold']))
                        for r,p in zip(test,probabilities) if int(p>=artifact['threshold'])!=int(r['label'])]
    result['by_source'] = {}
    for source in sorted({r['source_ref'] for r in test}):
        indices=[i for i,r in enumerate(test) if r['source_ref']==source]
        labels=[int(test[i]['label']) for i in indices]
        adequate=len(indices)>=20 and min(labels.count(0),labels.count(1))>=5
        result['by_source'][source]=dict(records=len(indices),metrics=metrics(labels,probabilities[indices],artifact['threshold']) if adequate else None,
            note='Private approved-input source reference; descriptive only' if adequate else 'Insufficient support: require 20 records and 5 per class')
    result["final_test_scope"] = metadata.get("final_test_scope", "unspecified; do not claim prospective validation")
    result["host_batch_seconds"] = host_batch_seconds
    result["phone_latency_and_memory"] = "not measured"
    result["annotation_agreement_eligible_subset"] = agreement(list(rows.values()))
    result["agreement_note"] = "Use import-report.json for unfiltered pre-adjudication agreement; this subset excludes unresolved/out-of-scope rows"
    result["evaluation_scope"] = metadata["evaluation_scope"]
    result["selection_sha256"] = hashlib.sha256(selection.read_bytes()).hexdigest()
    result["deployment_approval"] = "pending researcher review of calibration, errors, parity and phone tests"
    write_json(args.run/"final-test.json", result)
    print("Final test evaluated once. No model winner or deployment approval inferred.")

if __name__ == "__main__":
    main()
