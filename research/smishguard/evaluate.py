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
    pred = p >= threshold
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0,1]).ravel()
    precision, recall, _ = precision_recall_curve(y, p)
    bins = []
    for i in range(10):
        mask = (p >= i/10) & ((p < (i+1)/10) if i < 9 else (p <= 1))
        bins.append(dict(count=int(mask.sum()), mean_probability=float(p[mask].mean()) if mask.any() else None,
                         observed_positive_rate=float(y[mask].mean()) if mask.any() else None))
    fpr, fnr = float(fp/max(1,fp+tn)), float(fn/max(1,fn+tp))
    return dict(precision=float(precision_score(y,pred,zero_division=0)), recall=float(recall_score(y,pred)),
        f1=float(f1_score(y,pred)), pr_auc=float(auc(recall,precision)), average_precision=float(average_precision_score(y,p)),
        roc_auc=float(roc_auc_score(y,p)), false_positive_rate=fpr, false_negative_rate=fnr,
        brier=float(brier_score_loss(y,p)), log_loss=float(log_loss(y,p)), reliability_bins=bins,
        expected_calibration_error=sum(b["count"]/len(y)*abs(b["mean_probability"]-b["observed_positive_rate"]) for b in bins if b["count"]),
        confusion=dict(tn=int(tn),fp=int(fp),fn=int(fn),tp=int(tp)),
        hypothetical_base_rates=[dict(prevalence=r, estimated_positive_predictive_value=(1-fnr)*r/max(1e-15,(1-fnr)*r+fpr*(1-r))) for r in (.001,.01,.05)])

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
    result = metrics([int(r["label"]) for r in test], probabilities, artifact["threshold"])
    result["by_language"] = language_metrics(test, probabilities, artifact["threshold"])
    result["final_test_scope"] = metadata.get("final_test_scope", "unspecified; do not claim prospective validation")
    result["host_batch_seconds"] = time.perf_counter()-started
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
