"""Read-only handoff audit and unchanged LR conversion. All message output stays private.

Does not execute the notebook, train, approve research use, or install an Android asset.
"""
import argparse
from collections import Counter
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import statistics
import unicodedata

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split

from .convert_supplied import validate, unicode_contract, PROBES
from .prepare_team_data import read_rows
from .review_packets import private_output
from .train import write_json

SEEDS = [42, 7, 123, 2024, 99]
MODEL_VERSION = "mark-lr-20260929-0351"
AUDITED_REFERENCE_SHA256 = "4873595713408867e8665198e27b430335b93c2b4b1a6f234737998c488684f8"
URL_RE = r'(https?://\S+|www\.\S+|\b[a-z0-9][a-z0-9-]*(?:\.[a-z0-9-]+)*\.[a-z]{2,8}(?:/\S*)?\b)'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_candidate(model):
    if (model.get("model_type") != "logistic_regression_calibrated"
            or model.get("l2_normalize") is not True):
        raise ValueError("Unsupported candidate semantics")
    validate({**model, "model_type": "logistic_regression", "classes": ["ham", "smishing"]})
    for key in ("calibration_a", "calibration_b", "threshold"):
        if type(model.get(key)) not in (int, float) or not math.isfinite(model[key]):
            raise ValueError("Invalid candidate scalar")
    if model["calibration_a"] <= 0 or model["threshold"] != .4:
        raise ValueError("This candidate requires a positive sigmoid slope and threshold 0.40")
    return model


def content_findings(model):
    # Candidates for review, never a claim that regex proves personal ownership.
    words = list(model["vocabulary"])
    phones = sorted({token for word in words for token in word.split()
                     if re.fullmatch(r'(?:0|63)9\d{9}', token)})
    return dict(phone_shaped_tokens=phones,
                phone_bearing_features=[w for w in words if any(t in phones for t in w.split())],
                long_digit_features=[w for w in words if re.search(r'\d{5,}', w)],
                masked_identifier_features=[w for w in words if re.search(r'x{4,}\d', w)])


def convert(model, source_hash):
    if unicodedata.unidata_version != "15.0.0":
        raise ValueError("Requires Python 3.12 / Unicode 15.0.0")
    validate_candidate(model)
    return dict(schema_version=3, model_version=MODEL_VERSION, algorithm="lr",
        preprocessing_version="python-unicode-word-v2", feature_type="word-unigram-bigram-tfidf-l2",
        vocabulary=sorted(model["vocabulary"], key=model["vocabulary"].get),
        idf=model["idf"], weights=model["coef"], bias=model["intercept"],
        classes=["ham", "smishing"], positive_class="smishing", ngram_range=[1, 2],
        lowercase=True, token_pattern=r'\b\w+\b', term_frequency="raw", normalization="l2",
        score_transform="sigmoid", calibration=dict(a=model["calibration_a"], b=model["calibration_b"]),
        threshold=model["threshold"], threshold_comparison="greater_or_equal", synthetic=False,
        provenance=dict(kind="user_supplied_export", source_sha256=source_hash,
                        trained_on_rows=model.get("trained_on_rows")),
        technical_compatibility="reference_verified", evaluation_status="unverified",
        calibration_status="fitted_unvalidated", intended_use="manual_development",
        automatic_warnings_approved=False, unicode=unicode_contract())


def normalized(text):
    text = re.sub(URL_RE, '<url>', text.strip().lower())
    text = re.sub(r'\d+', '#', text)
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z#<> ]', '', text)).strip()


def exposure(rows):
    """Reconstruct supplied split procedure, not training history certification."""
    retained = {}
    conflicts = {}
    for i, row in enumerate(rows):
        key = normalized(row['text'])
        retained.setdefault(key, i)
        conflicts.setdefault(key, set()).add(row['label'])
    indices = list(retained.values())
    labels = {i: rows[i]['label'] for i in indices}
    roles = {i: {} for i in indices}
    splits = {}
    for seed in SEEDS:
        train, rest = train_test_split(indices, test_size=.3, random_state=seed,
                                      stratify=[labels[i] for i in indices])
        val, test = train_test_split(rest, test_size=2/3, random_state=seed,
                                    stratify=[labels[i] for i in rest])
        splits[seed] = dict(train=train, validation=val, test=test)
        for role, members in splits[seed].items():
            for i in members:
                roles[i][str(seed)] = role
    first_test = set(splits[42]['test'])
    other_dev = {i for seed in SEEDS[1:] for role in ('train', 'validation') for i in splits[seed][role]}
    other_val = {i for seed in SEEDS[1:] for i in splits[seed]['validation']}
    return dict(normalized_rows=len(indices), duplicates_removed=len(rows)-len(indices),
        normalized_conflicting_label_groups=sum(len(v)>1 for v in conflicts.values()),
        role_changing_records=sum(len(set(v.values()))>1 for v in roles.values()),
        first_test_records=len(first_test), first_test_in_other_development=len(first_test & other_dev),
        first_test_in_other_validation=len(first_test & other_val),
        split_support={str(seed): {part: len(ids) for part, ids in s.items()} for seed, s in splits.items()}), roles


def audit(package, private, report):
    private_output(package); private_output(private)
    private.mkdir(parents=True, exist_ok=True)
    source = package / '1_android_app/model_export_final.json'
    model = validate_candidate(json.loads(source.read_text(encoding='utf-8')))
    copies = list(package.rglob('model_export_final.json'))
    if len(copies) != 3 or len({sha(p) for p in copies}) != 1:
        raise ValueError("Model copies differ")
    datasets = list(package.rglob('smishguard_dataset*.csv'))
    if len(datasets) != 2 or len({sha(p) for p in datasets}) != 1:
        raise ValueError("Dataset copies differ")
    rows = read_rows(datasets[0].read_bytes(), ('id', 'text', 'label', 'source_category', 'source'))
    if any(r['label'] not in {'ham', 'smishing'} or not r['text'].strip() for r in rows):
        raise ValueError("Invalid dataset labels or blank text")
    findings = content_findings(model)
    write_json(private / 'content-findings.json', findings)
    split_audit, roles = exposure(rows)
    write_json(private / 'reconstructed-roles.json', roles)
    write_json(private / 'exposure-ledger.json', {
        'dataset_sha256': sha(datasets[0]), 'status': 'previously_exposed',
        'basis': 'supplied comparison and model inspection; reconstructed roles are not executed training logs',
        'records': [{'id': r['id'], 'text_sha256': hashlib.sha256(r['text'].encode()).hexdigest(),
                     'prior_use_status': 'exposed'} for r in rows]})
    # Audited plain Python reference source only; never unpickle supplied artifacts.
    reference_path = package / '1_android_app/reference_scorer.py'
    if sha(reference_path) != AUDITED_REFERENCE_SHA256:
        raise ValueError("Reference source changed; inspect before allowing its execution")
    spec = importlib.util.spec_from_file_location('private_reference', reference_path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    reference = module.Scorer(str(source))
    vectorizer = TfidfVectorizer(vocabulary=model['vocabulary'], lowercase=True,
                                token_pattern=r'(?u)\b\w+\b', ngram_range=(1, 2))
    vectorizer.idf_ = np.asarray(model['idf'])
    probes = PROBES + ['Ma, pauwi na po ako', 'Kain tayo mamaya.', 'Nasa bahay na ako.',
        'xqzvplmkj', 'Your account is suspended. Verify at https://example.invalid now.']
    texts = [r['text'] for r in rows] + probes
    margins = vectorizer.transform(texts) @ np.asarray(model['coef']) + model['intercept']
    scores = 1 / (1 + np.exp(-(model['calibration_a'] * margins + model['calibration_b'])))
    errors = [abs(reference.p_smishing(text)-score) for text, score in zip(texts, scores)]
    if max(errors) > 1e-10:
        raise ValueError("Reference/scikit-learn inference mismatch; no conversion")
    converted = convert(model, sha(source))
    write_json(private / 'model.json', converted)
    write_json(private / 'cases.json', [dict(text=text, score=float(score), suspicious=bool(score >= .4),
        tokens=re.findall(r'\b\w+\b', text.lower())) for text, score in zip(texts, scores)])
    per_seed_path = next(package.rglob('comparative_per_seed.csv'))
    table = read_rows(per_seed_path.read_bytes())
    aggregates = {}
    for name in dict.fromkeys(r['model'] for r in table):
        group = [r for r in table if r['model'] == name]
        if sorted(int(r['seed']) for r in group) != sorted(SEEDS):
            raise ValueError("Unexpected comparison seeds")
        aggregates[name] = {key: statistics.mean(float(r[key]) for r in group)
                           for key in ('precision', 'recall', 'f1', 'accuracy', 'ms', 'kb')}
        aggregates[name].update(f1_sample_sd=statistics.stdev(float(r['f1']) for r in group),
            missed=sum(int(r['missed']) for r in group), false_alarms=sum(int(r['false_alarms']) for r in group))
    supplied_table = read_rows(next(package.rglob('comparative_results.csv')).read_bytes())
    for row in supplied_table:
        mean = aggregates[row['Algorithm']]
        for key, column in [('accuracy', 'Accuracy'), ('precision', 'Smishing Precision'), ('recall', 'Smishing Recall')]:
            if row[column] != f"{mean[key]:.1%}":
                raise ValueError("Supplied summary rounding mismatch")
        if (row['Smishing F1'] != f"{mean['f1']:.1%} ± {mean['f1_sample_sd']:.1%}"
                or int(row['Missed scams (total)']) != mean['missed']
                or int(row['False alarms (total)']) != mean['false_alarms']
                or float(row['Size (KB)']) != round(mean['kb'], 1)
                or float(row['ms / message']) != round(mean['ms'], 2)):
            raise ValueError("Supplied summary mismatch")
    references = re.findall(r'check\("(.*?)", (?:true|false), ([\d.]+), RiskLevel\.',
        (package/'1_android_app/kotlin/SmishScorerTest.kt').read_text())
    reference_errors = [abs(reference.p_smishing(text)-float(expected)) for text, expected in references]
    summary = dict(dataset_rows=len(rows), classes=dict(Counter(r['label'] for r in rows)),
        duplicate_ids=len(rows)-len({r['id'] for r in rows}), dataset_sha256=sha(datasets[0]),
        identical_dataset_copies=2, identical_model_copies=3, source_model_sha256=sha(source),
        source_model_bytes=source.stat().st_size, converted_model_bytes=(private/'model.json').stat().st_size,
        converted_model_sha256=sha(private/'model.json'), model_version=MODEL_VERSION,
        feature_count=len(model['vocabulary']), trained_on_rows_claim=model['trained_on_rows'],
        source_category_counts=dict(Counter(r['source_category'] for r in rows)),
        schema_numeric_checks='passed', positive_class='smishing: notebook sign correction and reference semantics; classes absent from source JSON',
        notebook_outputs=sum(len(c.get('outputs', [])) for c in json.loads((package/'3_training/SMISHGUARD_Training.ipynb').read_text())['cells']),
        notebook_execution_counts_present=sum(c.get('execution_count') is not None for c in
            json.loads((package/'3_training/SMISHGUARD_Training.ipynb').read_text())['cells']),
        vocabulary_review={key: len(value) for key, value in findings.items()},
        candidate_packaging='blocked: unresolved identifier-shaped vocabulary; no review acceptance fabricated',
        python_reference_sklearn_cases=len(texts), python_max_absolute_error=float(max(errors)),
        ordinary_taglish_software_probes=dict(count=3, above_candidate_threshold=int(sum(scores[-5:-2] >= .4)),
            interpretation='Invented ordinary-language probes; regression observations, not labeled research performance'),
        reconstructed_split_audit=split_audit, recalculated_comparison=aggregates,
        summary_recalculation='all five rows match rounded means, sample SDs, error totals, host timing and classifier-only sizes',
        supplied_rounded_references=dict(cases=len(references), max_absolute_error=max(reference_errors),
            tolerance=.001, passed=all(e<=.001 for e in reference_errors)),
        ci_recalculation='unavailable: record-level predictions and paired manifests absent',
        research_training_executed=False, supplied_code_executed='audited reference arithmetic only')
    for key, filename in [('jvm_adapter', 'jvm-adapter-aggregate.json'), ('jvm_supplied', 'jvm-supplied-aggregate.json')]:
        if (private/filename).exists():
            outcome = json.loads((private/filename).read_text())
            expected_model = sha(private/'model.json') if key == 'jvm_adapter' else sha(source)
            if outcome.get('model_sha256') == expected_model and outcome.get('cases_sha256') == sha(private/'cases.json'):
                summary[key] = outcome
            else:
                summary[key] = dict(status='stale/unbound result; rerun private JVM parity')
    if (private.parent/'group-audit.json').exists():
        summary['template_sensitivity_audit'] = json.loads((private.parent/'group-audit.json').read_text())
    write_json(report, summary)
    print('Audit complete; private messages and review findings withheld; aggregate report written.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package', type=Path)
    parser.add_argument('private_output', type=Path)
    parser.add_argument('aggregate_report', type=Path)
    args = parser.parse_args()
    audit(args.package, args.private_output, args.aggregate_report)


if __name__ == '__main__':
    main()
