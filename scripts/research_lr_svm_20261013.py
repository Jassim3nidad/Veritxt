"""Reproduce frozen SMS baselines; tune new candidates without evaluating their test.

Run with the existing pinned research environment. All message-bearing outputs and
fitted objects stay in an ignored, newly created private directory. No supplied
archive code or saved pickle is executed. This is retrospective research only.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import pickle
import platform
import time
import zipfile

import numpy as np
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, f1_score
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC
from threadpoolctl import threadpool_limits

from smishguard import fair_compare as fair
from smishguard.evaluate import metrics

SEED = 20260929


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def model(name, c, weight=None):
    if name == "lr":
        return LogisticRegression(C=c, class_weight=weight, solver="liblinear", max_iter=2000, random_state=SEED)
    return LinearSVC(C=c, class_weight=weight, dual="auto", max_iter=10000, random_state=SEED)


def features(name):
    if name == "word_unigram":
        return fair.vectorizer()
    return FeatureUnion([
        ("word", TfidfVectorizer(lowercase=False, token_pattern=r"(?u)\b\w+\b", ngram_range=(1, 2), max_features=50000)),
        ("char", TfidfVectorizer(lowercase=False, analyzer="char", ngram_range=(3, 5), min_df=2, max_features=50000)),
    ])


def measured(y, p, threshold):
    result = metrics(y, p, threshold)
    assert sum(result["confusion"].values()) == len(y)
    return result


def bootstrap(y, groups, probabilities, thresholds):
    rng = np.random.default_rng(SEED)
    blocks = [np.flatnonzero(groups == g) for g in np.unique(groups)]
    values = {n: [] for n in probabilities}
    differences = []
    for _ in range(2000):
        ids = np.concatenate([blocks[i] for i in rng.integers(len(blocks), size=len(blocks))])
        if len(np.unique(y[ids])) < 2:
            continue
        for n, p in probabilities.items():
            pred = p[ids] >= thresholds[n]
            tp = np.sum(pred & (y[ids] == 1)); fp = np.sum(pred & (y[ids] == 0)); fn = np.sum(~pred & (y[ids] == 1))
            values[n].append(float(2 * tp / (2 * tp + fp + fn)))
        differences.append(values["svm"][-1] - values["lr"][-1])
    return dict(draws_used=len(differences), method="paired whole-template-group percentile bootstrap; conditional on fixed models",
                f1_intervals={n: np.quantile(v, [.025, .975]).tolist() for n, v in values.items()},
                svm_minus_lr_f1_interval=np.quantile(differences, [.025, .975]).tolist())


def run(source, output, archive):
    output.mkdir(parents=True, exist_ok=False)
    cfg = read(source / "configuration.json")
    assert digest(source / "dataset.json") == cfg["dataset_sha256"]
    assert digest(source / "splits.json") == cfg["split_sha256"]
    seal = read(source / "final-artifact-manifest.json")["files"]
    for n in ("dataset.json", "splits.json", "test-predictions.json", "configuration.json"):
        assert digest(source / n) == seal[n], f"Historical artifact changed: {n}"
    with zipfile.ZipFile(archive) as z:
        actual = {Path(n).name: hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if not n.endswith("/")}
    assert actual == cfg["new_package_sha256"], "Supplied ZIP differs from audited package"
    rows = read(source / "dataset.json"); split = read(source / "splits.json")
    parts = split["partitions"]; groups = np.array(split["groups"])
    flat = [i for v in parts.values() for i in v]
    assert sorted(flat) == list(range(len(rows)))
    for a in parts:
        for b in parts:
            if a != b:
                assert not set(groups[parts[a]]) & set(groups[parts[b]])
    def part(name):
        ids = parts[name]
        return [rows[i]["text_redacted"] for i in ids], np.array([rows[i]["label"] for i in ids])
    xt, yt = part("train"); xc, yc = part("calibration"); xv, yv = part("validation")
    folds = [(np.array(f["train"]), np.array(f["validation"])) for f in split["inner_folds"]]
    covered = np.zeros(len(yt), dtype=int)
    for a, b in folds:
        assert set(a).isdisjoint(b) and set(a) | set(b) == set(range(len(yt)))
        assert not set(groups[parts["train"]][a]) & set(groups[parts["train"]][b])
        assert set(yt[a]) == set(yt[b]) == {0, 1}
        covered[b] += 1
    assert np.all(covered == 1)
    protocol = dict(status="retrospective; prior test exposure; no prospective test available", seed=SEED,
        source=str(source.resolve()), source_hashes={n: digest(source/n) for n in ("dataset.json", "splits.json", "configuration.json", "test-predictions.json")},
        zip_sha256=digest(archive), code_sha256=digest(Path(__file__)),
        grid=dict(C=[.1, 1., 10.], class_weight=[None, "balanced"], representations=["word_unigram", "word_char"]),
        selection="mean training-fold average precision; iteration order breaks ties", calibration="separate calibration partition",
        tuning_test_policy="newly tuned models have no test predictions or metrics; prospective evaluation pending",
        threshold_grid=np.linspace(.05,.95,91).tolist(), versions=dict(python=platform.python_version(), sklearn=sklearn.__version__, numpy=np.__version__),
        partitions={k: dict(records=len(ids), labels=dict(Counter(str(rows[i]["label"]) for i in ids))) for k, ids in parts.items()})
    write(output / "protocol.json", protocol)
    # Fixed historical parameters only. No selection or change is driven by test.
    fixed = {}; fitted = {}
    for name in ("lr", "svm"):
        start = time.perf_counter()
        pipe = Pipeline([("tfidf", fair.vectorizer()), ("classifier", model(name, cfg["baseline_parameters"][name]))]).fit(xt, yt)
        base_seconds = time.perf_counter() - start
        cal = LogisticRegression(random_state=SEED).fit(pipe.decision_function(xc).reshape(-1,1), yc)
        seconds = time.perf_counter() - start
        assert list(pipe.classes_) == list(cal.classes_) == [0, 1]
        fitted[name] = (pipe, cal)
        payload = pickle.dumps(dict(pipeline=pipe, calibrator=cal, threshold=cfg["baseline_thresholds"][name]))
        (output / ("fixed_" + name + ".pkl")).write_bytes(payload)
        fixed[name] = dict(training_seconds=seconds, base_training_seconds=base_seconds, serialized_bytes=len(payload),
            vocabulary_size=len(pipe["tfidf"].vocabulary_), coefficient_and_idf_bytes=pipe["classifier"].coef_.nbytes+pipe["tfidf"].idf_.nbytes,
            threshold=cfg["baseline_thresholds"][name])
    write(output / "fixed-freeze.json", {n: digest(output / ("fixed_"+n+".pkl")) for n in fitted})
    xe, ye = part("test")
    historical = read(source / "test-predictions.json")
    assert historical["ids"] == [rows[i]["id"] for i in parts["test"]]
    assert historical["labels"] == ye.tolist()
    probabilities = {}
    for name, (pipe, cal) in fitted.items():
        start = time.perf_counter()
        p = cal.predict_proba(pipe.decision_function(xe).reshape(-1,1))[:,1]
        infer = time.perf_counter() - start
        old = historical["predictions"]["standalone_"+name]
        difference = float(np.max(abs(p-np.array(old["scores"]))))
        assert difference < 1e-10
        assert (p >= fixed[name]["threshold"]).astype(int).tolist() == old["predictions"]
        fixed[name].update(test=measured(ye,p,fixed[name]["threshold"]), historical_probability_max_absolute_difference=difference,
            test_inference_seconds=infer, test_ms_per_record=1000*infer/len(ye))
        probabilities[name] = p
    fixed["uncertainty"] = bootstrap(ye, groups[parts["test"]], probabilities, cfg["baseline_thresholds"])
    write(output / "fixed-test-probabilities.json", {n: p.tolist() for n,p in probabilities.items()})
    write(output / "fixed-results.json", fixed)
    print("Fixed LR/SVM decisions and probabilities reproduce historical outputs", flush=True)
    # Prespecified training-only grid, identical folds and representation choices.
    trials = []
    for rep in ("word_unigram", "word_char"):
        scores = {(n,c,w): [] for n in ("lr","svm") for c in (.1,1.,10.) for w in (None,"balanced")}
        for a,b in folds:
            v = features(rep)
            xa = v.fit_transform([xt[i] for i in a]); xb = v.transform([xt[i] for i in b])
            for (n,c,w), values in scores.items():
                clf = model(n,c,w).fit(xa,yt[a])
                values.append(float(average_precision_score(yt[b],clf.decision_function(xb))))
        for (n,c,w), values in scores.items():
            trials.append(dict(model=n, representation=rep, C=c, class_weight=w, fold_average_precision=values,
                               mean_average_precision=float(np.mean(values)), fold_sd=float(np.std(values,ddof=1))))
        print("Training-only grid complete:", rep, flush=True)
    write(output / "training-grid.json", trials)
    tuned = {}
    for name in ("lr", "svm"):
        chosen = max((t for t in trials if t["model"]==name), key=lambda t:t["mean_average_precision"])
        start = time.perf_counter()
        pipe = Pipeline([("tfidf", features(chosen["representation"])), ("classifier",model(name,chosen["C"],chosen["class_weight"]))]).fit(xt,yt)
        cal = LogisticRegression(random_state=SEED).fit(pipe.decision_function(xc).reshape(-1,1),yc)
        elapsed = time.perf_counter()-start
        p = cal.predict_proba(pipe.decision_function(xv).reshape(-1,1))[:,1]
        threshold = float(max(np.linspace(.05,.95,91), key=lambda t:(f1_score(yv,p>=t),t)))
        payload = pickle.dumps(dict(pipeline=pipe,calibrator=cal,threshold=threshold))
        (output / ("tuned_"+name+".pkl")).write_bytes(payload)
        pipe.decision_function(xv[:1])  # warm up without timing model load
        batch=[]; single=[]
        for _ in range(7):
            start=time.perf_counter();cal.predict_proba(pipe.decision_function(xv).reshape(-1,1));batch.append(time.perf_counter()-start)
            start=time.perf_counter();cal.predict_proba(pipe.decision_function(xv[:1]).reshape(-1,1));single.append(time.perf_counter()-start)
        tuned[name]=dict(selected=chosen, threshold=threshold, validation_fixed_half=measured(yv,p,.5),
            validation_selected_threshold=measured(yv,p,threshold), validation_score_status="threshold-optimized development result; not unbiased generalization estimate",
            final_fit_and_calibration_seconds=elapsed, serialized_bytes=len(payload),
            validation_batch_median_seconds=float(np.median(batch)), single_message_median_ms=float(1000*np.median(single)),
            test_status="Not evaluated; prospective test unavailable")
    write(output / "tuned-validation.json", tuned)
    aggregate=dict(protocol=protocol, fixed=fixed, tuned=tuned, training_grid=trials)
    write(output / "aggregate.json", aggregate)
    print(json.dumps({"fixed":{n:fixed[n]["test"]["f1"] for n in ("lr","svm")},
                      "tuned_validation":{n:tuned[n]["validation_selected_threshold"]["f1"] for n in tuned}}), flush=True)


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("source",type=Path);parser.add_argument("output",type=Path);parser.add_argument("archive",type=Path)
    args=parser.parse_args()
    with threadpool_limits(limits=1):
        run(args.source,args.output,args.archive)
