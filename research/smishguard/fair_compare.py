"""Prepare all candidates, then evaluate one sealed comparison. Private outputs only."""
import argparse
import csv
import hashlib
import json
import pickle
import platform
import time
from pathlib import Path

import numpy as np
import scipy
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, f1_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from .data import read_dataset, split_rows, template_groups
from .evaluate import metrics
from .linear_export import export_linear
from .preprocessing import VERSION, normalize
from .train import margin, write_json
from .uncertainty import cluster_intervals
from .intake import TOKEN

SEED = 20260929
NAMES = ("lr", "nb", "svm")
GRID = (0.1, 1.0, 10.0)
PROTOCOL = Path(__file__).resolve().parents[2] / "docs/algorithm-comparison-protocol.md"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classifier(name, value):
    if name == "lr":
        return LogisticRegression(C=value, solver="liblinear", max_iter=2000, random_state=SEED)
    if name == "nb":
        return MultinomialNB(alpha=value)
    if name == "svm":
        return LinearSVC(C=value, dual="auto", max_iter=10000, random_state=SEED)
    raise ValueError("Unsupported comparison algorithm")


def vectorizer():
    return TfidfVectorizer(lowercase=False, token_pattern=r"(?u)\b\w+\b",
                           ngram_range=(1, 1), max_features=50000, norm="l2", dtype=np.float64)


def training_folds(y, groups):
    folds = list(StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
                 .split(np.zeros(len(y)), y, groups))
    for train, valid in folds:
        if any(len(np.unique(y[part])) != 2 for part in (train, valid)):
            raise ValueError("Nonviable training fold; no favorable seed retries")
        if set(groups[train]) & set(groups[valid]):
            raise ValueError("Training fold group overlap")
    return folds


def tune(texts, y, folds, name):
    """Only outer-training text is accepted; fit a fresh vocabulary in every fold."""
    trials = []
    for value in GRID:
        scores = []
        for train, valid in folds:
            pipe = Pipeline([("tfidf", vectorizer()), ("classifier", classifier(name, value))])
            pipe.fit([texts[i] for i in train], y[train])
            x = pipe["tfidf"].transform([texts[i] for i in valid])
            scores.append(float(average_precision_score(y[valid], margin(pipe["classifier"], x))))
        trials.append(dict(value=value, fold_average_precision=scores, mean=float(np.mean(scores))))
    best = max(trials, key=lambda trial: trial["mean"])
    pipe = Pipeline([("tfidf", vectorizer()), ("classifier", classifier(name, best["value"]))])
    pipe.fit(texts, y)
    return pipe, trials, best["value"]


def reviewed_assignments(path, rows, groups):
    record = json.loads(path.read_text(encoding="utf-8"))
    partitions = ("train", "validation", "calibration", "test")
    if (not isinstance(record, dict) or set(record) != {*partitions, "reservation_reference"}
            or not isinstance(record["reservation_reference"], str) or not TOKEN.fullmatch(record["reservation_reference"])):
        raise ValueError("Assignments require four partitions and an opaque reservation evidence reference")
    if any(not isinstance(record[key], list) or not all(isinstance(value, str) for value in record[key]) for key in partitions):
        raise ValueError("Assignment partitions must be lists of record IDs")
    assigned = [value for key in partitions for value in record[key]]
    index = {row["id"]: i for i, row in enumerate(rows)}
    if len(assigned) != len(index) or len(set(assigned)) != len(assigned) or set(assigned) != set(index):
        raise ValueError("Assignments must cover every eligible record exactly once")
    splits = {key:[index[value] for value in record[key]] for key in partitions}
    seen = set()
    for ids in splits.values():
        present = {groups[i] for i in ids}
        if seen & present or {rows[i]["label"] for i in ids} != {"0", "1"}:
            raise ValueError("Reserved assignment has crossing template groups or missing class support")
        seen.update(present)
    return splits


def exposure_review(path, rows, splits, history):
    """Keep prior use explicit; an assignment cannot reset an exposed record's history."""
    if path is None:
        raise ValueError("A complete --exposure-review is required; never infer unseen status")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ["id", "prior_use_status", "evidence_reference"]:
            raise ValueError("Invalid exposure-review schema")
        records = list(reader)
    by_id = {record["id"]: record for record in records}
    if len(by_id) != len(records) or set(by_id) != {row["id"] for row in rows}:
        raise ValueError("Exposure review must cover each record exactly once")
    for record in records:
        if (record["prior_use_status"] not in {"exposed", "never_used", "unknown"}
                or not TOKEN.fullmatch(record["evidence_reference"])):
            raise ValueError("Exposure status requires an actual evidence reference")
    test_status = [by_id[rows[i]["id"]]["prior_use_status"] for i in splits["test"]]
    if history == "prospectively_reserved" and any(status != "never_used" for status in test_status):
        raise ValueError("Exposed or unknown final records cannot be called prospectively reserved")
    return dict(test_status_counts={status: test_status.count(status) for status in ("exposed", "never_used", "unknown")},
                interpretation="Human evidence required; declarations cannot prove historical non-use")


def prepare(dataset, output, history, exclusion_report, assignments=None, exposure_path=None):
    if history == "prospectively_reserved" and assignments is None:
        raise ValueError("Prospective evaluation requires reviewed frozen assignments; a new random split cannot establish unseen status")
    rows = sorted(read_dataset(dataset), key=lambda row: row["id"])
    if len(rows) < 1200:
        raise ValueError("Configured guard requires 1,200 eligible primary records; methodology applicability is pending. See docs/sample-size-provenance.md; this is not a universal statistical minimum.")
    if len({row["id"] for row in rows}) != len(rows):
        raise ValueError("Duplicate record IDs")
    groups = np.asarray(template_groups(rows))
    splits = reviewed_assignments(assignments, rows, groups) if assignments else split_rows(rows, groups, "group", SEED)
    exposure = exposure_review(exposure_path, rows, splits, history)
    training = splits["train"]
    texts = [normalize(rows[i]["text_redacted"]) for i in training]
    y = np.array([int(rows[i]["label"]) for i in training])
    folds = training_folds(y, groups[training])
    exclusion_hash = digest(exclusion_report)
    output.mkdir(parents=True, exist_ok=False)
    manifest = {part: [rows[i]["id"] for i in indices] for part, indices in splits.items()}
    manifest["groups"] = {row["id"]: int(groups[i]) for i, row in enumerate(rows)}
    manifest["inner_folds"] = [{"train": [rows[training[i]]["id"] for i in a],
                                "validation": [rows[training[i]]["id"] for i in b]} for a, b in folds]
    write_json(output / "splits.json", manifest)
    validation = {}
    for name in NAMES:
        pipe, trials, chosen = tune(texts, y, folds, name)
        v, model = pipe["tfidf"], pipe["classifier"]
        def partition(part):
            ids = splits[part]
            return v.transform([normalize(rows[i]["text_redacted"]) for i in ids]), np.array([int(rows[i]["label"]) for i in ids])
        xc, yc = partition("calibration")
        calibrator = LogisticRegression(random_state=SEED).fit(margin(model, xc).reshape(-1, 1), yc)
        xv, yv = partition("validation")
        scores = calibrator.predict_proba(margin(model, xv).reshape(-1, 1))[:, 1]
        threshold = float(max(np.linspace(.05, .95, 91), key=lambda t: (f1_score(yv, scores >= t), t)))
        artifact = dict(vectorizer=v, model=model, calibrator=calibrator, threshold=threshold, condition="deployment")
        run = output / name
        run.mkdir()
        (run / "research-model.pkl").write_bytes(pickle.dumps(artifact))
        export = export_linear(v, model, calibrator, threshold, synthetic=False)
        export["model_version"] = f"comparison-v1-{name}-{digest(dataset)[:12]}"
        write_json(run / "model.json", export)
        validation[name] = dict(chosen_parameter=chosen, inner_trials=trials, threshold=threshold,
                                validation_f1=float(f1_score(yv, scores >= threshold)))
    files = ["splits.json"] + [f"{name}/{file}" for name in NAMES for file in ("research-model.pkl", "model.json")]
    write_json(output / "freeze.json", dict(protocol_sha256=digest(PROTOCOL), dataset_sha256=digest(dataset),
        exclusion_report_sha256=exclusion_hash, seed=SEED, preprocessing=VERSION, history=history,
        assignment_sha256=digest(assignments) if assignments else None,
        exposure_review_sha256=digest(exposure_path), exposure_review=exposure,
        assignment_policy="reviewed complete group-isolated manifest; unseen status is human evidence" if assignments else "seeded retrospective group split",
        partition_support={part: dict(records=len(ids), groups=len(set(groups[ids])),
            phishing=sum(rows[i]["label"] == "1" for i in ids), legitimate=sum(rows[i]["label"] == "0" for i in ids))
            for part, ids in splits.items()},
        versions=dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__, sklearn=sklearn.__version__),
        files={file: digest(output / file) for file in files}, validation=validation,
        final_test_opened=False, research_winner=None))


def adequate_groups(y, groups):
    return len(set(groups)) >= 20 and all(len(set(groups[y == label])) >= 5 for label in (0, 1))


def paired_f1_intervals(y, predictions, groups, repetitions=2000):
    if not adequate_groups(y, groups):
        return dict(status="insufficient independent class/group support", intervals=None)
    if set(predictions) != set(NAMES) or any(len(pred) != len(y) for pred in predictions.values()):
        raise ValueError("Paired uncertainty requires all three predictions on identical records")
    rng = np.random.default_rng(SEED)
    unique = np.unique(groups)
    pairs = [(a, b) for i, a in enumerate(NAMES) for b in NAMES[i + 1:]]
    samples = {f"{a}-{b}": [] for a, b in pairs}
    for _ in range(repetitions):
        indices = np.concatenate([np.flatnonzero(groups == group) for group in rng.choice(unique, len(unique), replace=True)])
        if len(np.unique(y[indices])) < 2:
            continue
        f1 = {name: f1_score(y[indices], pred[indices], zero_division=0) for name, pred in predictions.items()}
        for a, b in pairs:
            samples[f"{a}-{b}"].append(f1[a] - f1[b])
    return dict(status=f"conditional paired cluster percentile bootstrap; {repetitions} resamples", seed=SEED,
                scope="Fixed fitted models; marginal pairwise intervals, not simultaneous family-wise inference or fitting uncertainty",
                intervals={key: dict(valid_replicates=len(values), low=float(np.quantile(values, .025)),
                                     high=float(np.quantile(values, .975))) for key, values in samples.items()})


def evaluate(dataset, output):
    freeze = json.loads((output / "freeze.json").read_text(encoding="utf-8"))
    if digest(dataset) != freeze["dataset_sha256"] or digest(PROTOCOL) != freeze["protocol_sha256"]:
        raise ValueError("Dataset or protocol changed after freeze")
    for file, expected in freeze["files"].items():
        if digest(output / file) != expected:
            raise ValueError("Comparison artifact changed after freeze")
    rows = {row["id"]: row for row in read_dataset(dataset)}
    manifest = json.loads((output / "splits.json").read_text(encoding="utf-8"))
    test = [rows[key] for key in manifest["test"]]
    y = np.array([int(row["label"]) for row in test])
    groups = np.array([manifest["groups"][row["id"]] for row in test])
    # Fail closed after interrupted evaluation too: inspect locally; never retune and rerun.
    with (output / "final-evaluation-started.json").open("x", encoding="utf-8") as stream:
        json.dump(dict(freeze_sha256=digest(output / "freeze.json")), stream)
    results, predictions = {}, {}
    for name in NAMES:
        run = output / name
        # Trusted, locally generated sealed artifact only; never import external pickle.
        artifact = pickle.loads((run / "research-model.pkl").read_bytes())
        start = time.perf_counter()
        x = artifact["vectorizer"].transform([normalize(row["text_redacted"]) for row in test])
        scores = artifact["calibrator"].predict_proba(margin(artifact["model"], x).reshape(-1, 1))[:, 1]
        elapsed = time.perf_counter() - start
        threshold = artifact["threshold"]
        predictions[name] = scores >= threshold
        result = metrics(y, scores, threshold)
        result.update(threshold=threshold, model_json_bytes=(run / "model.json").stat().st_size,
                      full_pipeline_pickle_bytes=(run / "research-model.pkl").stat().st_size,
                      host_batch_seconds=elapsed, host_batch_records=len(test), android_latency="pending device measurement",
                      calibration_status="held-out diagnostics only; no independent prospective calibration claim")
        result["confidence_intervals"] = (cluster_intervals(y, scores, groups, threshold, seed=SEED, repetitions=2000)
            if adequate_groups(y, groups) else dict(status="insufficient independent class/group support", intervals=None))
        results[name] = result
    best = max(result["f1"] for result in results.values())
    write_json(output / "comparison-aggregate.json", dict(results=results, primary_metric="phishing F1",
        highest_observed_f1=[name for name in NAMES if results[name]["f1"] == best],
        paired_f1=paired_f1_intervals(y, predictions, groups), test_records=len(test), test_groups=len(set(groups)),
        history=freeze["history"], freeze_sha256=digest(output / "freeze.json"),
        interpretation="Observed ranking only; assess paired uncertainty and prior-use history. No automatic deployment approval.",
        deployment_coverage="not evaluated; Android abstains on meaningless/all-unknown input; report coverage before app-performance claims"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("dataset", type=Path)
    prepare_parser.add_argument("output", type=Path)
    prepare_parser.add_argument("--history", required=True, choices=["previously_used", "prospectively_reserved"])
    prepare_parser.add_argument("--exclusion-report", required=True, type=Path)
    prepare_parser.add_argument("--assignments", type=Path, help="Reviewed frozen partition JSON; required for a prospectively reserved cohort")
    prepare_parser.add_argument("--exposure-review", required=True, type=Path,
                                help="Private per-record prior-use ledger with evidence references")
    evaluate_parser = sub.add_parser("evaluate")
    evaluate_parser.add_argument("dataset", type=Path)
    evaluate_parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.dataset, args.output, args.history, args.exclusion_report, args.assignments, args.exposure_review)
    else:
        evaluate(args.dataset, args.output)


if __name__ == "__main__":
    main()
