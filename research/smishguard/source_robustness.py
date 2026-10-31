"""Source-based development selection with preserved, historically exposed test data.

No fitted artifacts or messages leave ignored research storage. No app asset changes.
"""
from collections import Counter
from pathlib import Path
import argparse
import csv
import hashlib
import importlib.metadata
import json
import pickle
import time
import warnings

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import FeatureUnion, Pipeline
from threadpoolctl import threadpool_limits

from . import bantaytext_workflow as w

SEED = 42
FPR_LIMIT = .02
RECALL_FLOOR = .50
MIN_HAM = 100
MIN_POSITIVE = 20


def matrix():
    entries = []
    for algorithm in ('svm', 'lr', 'nb'):
        for features in ('word-english', 'word-none', 'char', 'combined'):
            for value in ((.03, .1, 1., 10.) if algorithm == 'nb' else (.01, .1, 1., 10.)):
                entries.append(dict(id=f'{algorithm}-{features}-{value:g}-df2', algorithm=algorithm,
                    features=features, value=value, min_df=2, control=False))
        value = .1 if algorithm == 'nb' else 10.
        entries.append(dict(id=f'{algorithm}-historical-word-control', algorithm=algorithm,
            features='word-english', value=value, min_df=1, control=True))
    return entries


def vectorizer(spec):
    word = dict(analyzer='word', ngram_range=(1, 2), min_df=spec['min_df'],
        stop_words='english' if spec['features'] == 'word-english' else None,
        norm='l2', sublinear_tf=False, smooth_idf=True)
    char = dict(analyzer='char_wb', ngram_range=(3, 5), min_df=spec['min_df'],
        norm='l2', sublinear_tf=False, smooth_idf=True)
    if spec['features'].startswith('word-'):
        return TfidfVectorizer(**word)
    if spec['features'] == 'char':
        return TfidfVectorizer(**char)
    return FeatureUnion([('word', TfidfVectorizer(**word)), ('char', TfidfVectorizer(**char))])


def fit(rows, groups, ids, spec):
    ids = np.asarray(ids, dtype=int)
    texts = [rows[i]['text'] for i in ids]
    y = np.asarray([rows[i]['label'] for i in ids])
    if set(y) != {0, 1}:
        raise ValueError('Training requires both inherited classes')
    classifier_spec = dict(algorithm=spec['algorithm'], C=spec['value'], alpha=spec['value'], class_weight=None)
    def pipeline():
        return Pipeline([('tfidf', vectorizer(spec)), ('classifier', w.classifier(classifier_spec))])
    started = time.perf_counter()
    calibrator = None
    folds = []
    if spec['algorithm'] == 'svm':
        oof = np.full(len(ids), np.nan)
        for a, b in StratifiedGroupKFold(n_splits=3, shuffle=True, random_state=SEED).split(texts, y, groups[ids]):
            if set(y[a]) != {0, 1} or set(y[b]) != {0, 1}:
                raise ValueError('Calibration fold requires both inherited classes')
            assert not set(groups[ids[a]]) & set(groups[ids[b]])
            model = pipeline().fit([texts[i] for i in a], y[a])
            oof[b] = w.margin(model['classifier'], model['tfidf'].transform([texts[i] for i in b]))
            folds.append(dict(train=ids[a].tolist(), calibration=ids[b].tolist()))
        assert np.isfinite(oof).all()
        calibrator = LogisticRegression(C=1, solver='lbfgs', random_state=SEED).fit(oof.reshape(-1, 1), y)
    model = pipeline().fit(texts, y)
    assert model['classifier'].classes_.tolist() == [0, 1]
    return dict(pipe=model, calibrator=calibrator, spec=spec, calibration_folds=folds,
        training_ids=ids.tolist(), training_seconds=time.perf_counter() - started)


def score(artifact, texts):
    x = artifact['pipe']['tfidf'].transform(texts)
    if artifact['calibrator'] is not None:
        p = artifact['calibrator'].predict_proba(w.margin(artifact['pipe']['classifier'], x).reshape(-1, 1))[:, 1]
    else:
        p = artifact['pipe']['classifier'].predict_proba(x)[:, 1]
    if not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
        raise ValueError('Invalid fitted score')
    return p


def source_folds(rows, groups, development, reserved):
    development = np.asarray(development, dtype=int)
    reserved = set(reserved)
    assert not reserved & set(development)
    assert not set(groups[list(reserved)]) & set(groups[development])
    folds = []
    for source in sorted({rows[i]['source'] for i in development}):
        held = [int(i) for i in development if rows[i]['source'] == source]
        held_groups = set(groups[held])
        training = [int(i) for i in development if rows[i]['source'] != source and groups[i] not in held_groups]
        assert not set(training) & set(held)
        assert not reserved & set(training + held)
        assert not set(groups[training]) & held_groups
        if {rows[i]['label'] for i in training} != {0, 1}:
            raise ValueError(f'Source complement lacks two classes: {source}')
        folds.append(dict(source=source, train=training, validation=held,
            related_records_purged=len(development) - len(training) - len(held)))
    return folds


def subgroups(rows, ids):
    result = {}
    for field in ('source', 'language'):
        for value in sorted({rows[i][field] for i in ids}):
            indices = [j for j, i in enumerate(ids) if rows[i][field] == value]
            result[f'{field}:{value}'] = np.asarray(indices, dtype=int)
    return result


def evaluate(rows, ids, scores, threshold):
    y = [rows[i]['label'] for i in ids]
    result = dict(pooled=w.calculate_metrics(y, scores, threshold), subgroups={})
    for key, indices in subgroups(rows, ids).items():
        m = w.calculate_metrics(np.asarray(y)[indices], np.asarray(scores)[indices], threshold)
        m['ham_support'] = m['confusion']['tn'] + m['confusion']['fp']
        m['smishing_support'] = m['confusion']['tp'] + m['confusion']['fn']
        m['small_positive_support'] = m['smishing_support'] < MIN_POSITIVE
        result['subgroups'][key] = m
    return result


def choose_threshold(rows, ids, scores):
    """Use validation-only score boundaries; preserve the recall floor in fallback."""
    scores = np.asarray(scores)
    y = np.asarray([rows[i]['label'] for i in ids])
    order = np.argsort(-scores, kind='stable')
    ordered = scores[order]
    thresholds = np.unique(np.concatenate(([0., .5, 1.], scores, np.nextafter(scores, np.inf))))
    thresholds = thresholds[(thresholds >= 0) & (thresholds <= 1)]
    cut = np.searchsorted(-ordered, -thresholds, side='right')
    source_f1, recalls, fprs = [], [], []
    for key, positions in subgroups(rows, ids).items():
        membership = np.zeros(len(ids), dtype=bool)
        membership[positions] = True
        pos = membership & (y == 1)
        neg = membership & (y == 0)
        tp = np.concatenate(([0], np.cumsum(pos[order])))[cut]
        fp = np.concatenate(([0], np.cumsum(neg[order])))[cut]
        positives, negatives = int(pos.sum()), int(neg.sum())
        if key.startswith('source:'):
            denominator = 2 * tp + fp + positives - tp
            source_f1.append(np.divide(2 * tp, denominator, out=np.zeros_like(tp, dtype=float), where=denominator > 0))
            if positives >= MIN_POSITIVE:
                recalls.append(tp / positives)
        if negatives >= MIN_HAM:
            fprs.append(fp / negatives)
    if not recalls or not fprs:
        raise ValueError('Validation needs supported positive source and ham subgroups')
    macro = np.mean(source_f1, axis=0)
    worst_fpr = np.max(fprs, axis=0)
    minimum_recall = np.min(recalls, axis=0)
    total_tp = np.concatenate(([0], np.cumsum((y[order] == 1))))[cut]
    pooled_recall = total_tp / max(1, int((y == 1).sum()))
    feasible = (worst_fpr <= FPR_LIMIT) & (minimum_recall >= RECALL_FLOOR)
    indices = np.flatnonzero(feasible)
    goal_met = bool(len(indices))
    if goal_met:
        selected = max(indices, key=lambda j: (macro[j], -worst_fpr[j], pooled_recall[j], thresholds[j]))
    else:
        indices = np.flatnonzero(minimum_recall >= RECALL_FLOOR)
        if not len(indices):
            raise ValueError('No supported nontrivial recall-preserving threshold')
        selected = max(indices, key=lambda j: (-worst_fpr[j], macro[j], pooled_recall[j], thresholds[j]))
    return dict(threshold=float(thresholds[selected]), goal_met=goal_met,
        macro_source_f1=float(macro[selected]), worst_supported_fpr=float(worst_fpr[selected]),
        minimum_supported_source_recall=float(minimum_recall[selected]),
        pooled_recall=float(pooled_recall[selected]), threshold_boundaries=len(thresholds),
        metrics=evaluate(rows, ids, scores, float(thresholds[selected])))


def rank(record):
    p = record['operating_point']
    if p['goal_met']:
        return (1, p['macro_source_f1'], -p['worst_supported_fpr'], p['pooled_recall'], -record['mean_feature_count'])
    return (0, -p['worst_supported_fpr'], p['macro_source_f1'], p['pooled_recall'], -record['mean_feature_count'])


def protected_files(root, original):
    paths = [original / name for name in ('dataset.json', 'splits.json', 'configuration.json',
        'aggregate.json', 'baseline-freeze.json', 'improvement-freeze.json')]
    paths += list(original.glob('*/*/pipeline.pkl'))
    paths += list((root / 'research/runs/bantaytext-20261013/validation-v2/source-heldout').glob('*/*-pipeline.pkl'))
    paths += [root / p for p in ('android/app/src/selectedSvm/assets/model.json',
        'android/app/src/selectedSvm/assets/raw-sms-adapter.json', 'android/app/src/development/assets/model.json',
        'deliverables/Veritxt-LinearSVM-20261013/Veritxt-0.3.0-LinearSVM.apk')]
    return {str(p.relative_to(root)): w.digest(p) for p in paths}


def verify_protected(root, manifest):
    for name, digest in manifest.items():
        if w.digest(root / name) != digest:
            raise ValueError(f'Protected original changed: {name}')


def false_alert_review(root, original, output, rows):
    folder = root / 'research/runs/bantaytext-20261013/validation-v2/source-heldout/tagalog'
    predictions = w.load(folder / 'svm-predictions.json')
    threshold = w.load(folder / 'svm-freeze.json')['threshold']
    artifact = pickle.loads((folder / 'svm-pipeline.pkl').read_bytes())
    chosen = [j for j, label in enumerate(predictions['labels']) if label == 0 and predictions['scores'][j] >= threshold]
    assert len(chosen) == 133
    languages = Counter(rows[predictions['indices'][j]]['language'] for j in chosen)
    categories = Counter(rows[predictions['indices'][j]]['category'] for j in chosen)
    fields = ['review_id', 'record_id', 'row_index', 'source', 'language', 'category', 'masked_message',
        'inherited_label', 'model_score', 'review_label', 'review_reason', 'evidence_reference']
    contributions = []
    names = artifact['pipe']['tfidf'].get_feature_names_out()
    weights = artifact['pipe']['classifier'].coef_[0]
    with (output / 'private-false-alert-review.csv').open('w', newline='', encoding='utf-8-sig') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for number, j in enumerate(chosen, 1):
            i = predictions['indices'][j]
            row = rows[i]
            writer.writerow(dict(review_id=f'source-fp-{number:03}', record_id=row['id'], row_index=i,
                source=row['source'], language=row['language'], category=row['category'],
                masked_message=row['text'], inherited_label=0, model_score=predictions['scores'][j],
                review_label='', review_reason='', evidence_reference=''))
            x = artifact['pipe']['tfidf'].transform([row['text']]).tocsr()
            values = weights[x.indices] * x.data
            top = np.argsort(-values)[:8]
            contributions.append(dict(review_id=f'source-fp-{number:03}', row_index=i,
                positive_features=[dict(term=str(names[x.indices[k]]), margin_contribution=float(values[k])) for k in top if values[k] > 0]))
    w.save(output / 'private-feature-contributions.json', contributions)
    scores = [predictions['scores'][j] for j in chosen]
    return dict(records=len(chosen), language=dict(languages), category=dict(categories),
        threshold=threshold, score_min=float(min(scores)), score_median=float(np.median(scores)),
        score_max=float(max(scores)), labels_changed=0, completed_review_decisions=0,
        interpretation='False positives under inherited labels; review pending. This is a separate stress-test fit.')


def run(root, original, output):
    root, original, output = root.resolve(), original.resolve(), output.resolve()
    if not output.is_relative_to(root / 'research/runs') or output.exists():
        raise ValueError('Use a new ignored research/runs directory')
    output.mkdir(parents=True)
    start = time.perf_counter()
    protected = protected_files(root, original)
    w.save(output / 'protected-originals.json', protected)
    cfg = w.load(original / 'configuration.json')
    assert w.digest(original / 'dataset.json') == cfg['cleaned_sha256']
    assert w.digest(original / 'splits.json') == cfg['split_sha256']
    rows = w.load(original / 'dataset.json')
    splits = w.load(original / 'splits.json')
    groups = np.asarray(splits['groups'])
    parts = splits['partitions']['grouped']
    development = sorted(parts['train'] + parts['validation'])
    reserved = parts['test']
    folds = source_folds(rows, groups, development, reserved)
    protocol = root / 'docs/source-robustness-protocol-20261013.md'
    w.save(output / 'experiment.json', dict(seed=SEED, dataset_sha256=w.digest(original / 'dataset.json'),
        splits_sha256=w.digest(original / 'splits.json'), protocol_sha256=w.digest(protocol),
        code_sha256=w.digest(Path(__file__)), development=development, reserved_test=reserved,
        source_folds=folds, candidates=matrix(), goals=dict(fpr=FPR_LIMIT, recall=RECALL_FLOOR,
        minimum_ham=MIN_HAM, minimum_positive=MIN_POSITIVE),
        versions={name: importlib.metadata.version(name) for name in ('numpy', 'scipy', 'scikit-learn', 'threadpoolctl')},
        historical_exposure=True, inherited_labels=True, new_prospective_records=0))
    review = false_alert_review(root, original, output, rows)
    w.save(output / 'false-alert-summary.json', review)
    with (output / 'prospective-intake.csv').open('w', newline='', encoding='utf-8-sig') as handle:
        csv.writer(handle).writerow(['record_id', 'masked_message', 'source', 'template_group',
            'language_English_Tagalog_Taglish_other', 'receipt_date', 'source_use_evidence',
            'label', 'label_evidence', 'reviewer', 'adjudication', 'notes'])
    results, failures = [], []
    index = {i: j for j, i in enumerate(development)}
    with threadpool_limits(limits=1):
        for number, spec in enumerate(matrix(), 1):
            folder = output / 'candidates' / spec['id']
            folder.mkdir(parents=True)
            scores = np.full(len(development), np.nan)
            feature_counts, fit_seconds, observed_warnings = [], [], []
            try:
                for fold in folds:
                    with warnings.catch_warnings(record=True) as caught:
                        warnings.simplefilter('always')
                        artifact = fit(rows, groups, fold['train'], spec)
                    observed_warnings.extend(str(warning.message) for warning in caught)
                    artifact_path = folder / (fold['source'] + '-pipeline.pkl')
                    artifact_path.write_bytes(pickle.dumps(artifact))
                    feature_counts.append(len(artifact['pipe']['tfidf'].get_feature_names_out()))
                    fit_seconds.append(artifact['training_seconds'])
                    predicted = score(artifact, [rows[i]['text'] for i in fold['validation']])
                    for i, p in zip(fold['validation'], predicted):
                        assert np.isnan(scores[index[i]])
                        scores[index[i]] = p
                    w.save(folder / (fold['source'] + '-audit.json'), dict(pipeline_sha256=w.digest(artifact_path),
                        training_ids=fold['train'], validation_ids=fold['validation'],
                        calibration_folds=artifact['calibration_folds'], source_name_feature=False))
                assert np.isfinite(scores).all()
                point = choose_threshold(rows, development, scores)
                record = dict(id=spec['id'], spec=spec, operating_point=point,
                    mean_feature_count=float(np.mean(feature_counts)), source_fit_seconds=float(sum(fit_seconds)),
                    warnings=sorted(set(observed_warnings)))
                results.append(record)
                w.save(folder / 'source-validation-predictions.json', dict(indices=development,
                    labels=[rows[i]['label'] for i in development], scores=scores.tolist()))
                w.save(folder / 'result.json', record)
                print(f"{number}/{len(matrix())} {spec['id']}: source F1 {point['macro_source_f1']:.4f}, worst FPR {point['worst_supported_fpr']:.4f}, goal {point['goal_met']}", flush=True)
            except Exception as error:
                failure = dict(id=spec['id'], error_type=type(error).__name__, error=str(error))
                failures.append(failure)
                w.save(folder / 'failure.json', failure)
                print(f"{number}/{len(matrix())} {spec['id']}: FAILED {type(error).__name__}", flush=True)
        if not results:
            raise ValueError('No supported candidate completed')
        # Stable predeclared tie break: smaller lexicographic ID.
        ordered = sorted(results, key=lambda r: r['id'])
        family = {algorithm: max([r for r in ordered if r['spec']['algorithm'] == algorithm], key=rank)
            for algorithm in ('svm', 'lr', 'nb')}
        overall = max(ordered, key=rank)
        w.save(output / 'development-selection.json', dict(family={k: r['id'] for k, r in family.items()},
            overall=overall['id'], any_goal_met=any(r['operating_point']['goal_met'] for r in results),
            selected_before_test_prediction=True, results=results, failures=failures))
        final_artifacts = {}
        frozen = {}
        for r in family.values():
            artifact = fit(rows, groups, development, r['spec'])
            artifact['threshold'] = r['operating_point']['threshold']
            folder = output / 'final' / r['id']
            folder.mkdir(parents=True)
            path = folder / 'pipeline.pkl'
            path.write_bytes(pickle.dumps(artifact))
            frozen[r['id']] = dict(pipeline_sha256=w.digest(path), threshold=artifact['threshold'],
                spec=r['spec'], training_records=len(development), calibration_folds=artifact['calibration_folds'])
            final_artifacts[r['id']] = artifact
        w.save(output / 'selection-freeze-before-test.json', dict(overall=overall['id'],
            family={k: r['id'] for k, r in family.items()}, models=frozen,
            development_selection_sha256=w.digest(output / 'development-selection.json'),
            test_predictions_opened=False))
        verify_protected(root, protected)
        final = {}
        for algorithm, r in family.items():
            artifact = final_artifacts[r['id']]
            scores = score(artifact, [rows[i]['text'] for i in reserved])
            folder = output / 'final' / r['id']
            assert w.digest(folder / 'pipeline.pkl') == frozen[r['id']]['pipeline_sha256']
            reloaded = pickle.loads((folder / 'pipeline.pkl').read_bytes())
            repeated = score(reloaded, [rows[i]['text'] for i in reserved])
            error = float(np.max(np.abs(repeated - scores)))
            assert error <= 1e-12
            metrics = evaluate(rows, reserved, scores, artifact['threshold'])
            w.save(folder / 'reserved-test-predictions.json', dict(indices=reserved,
                labels=[rows[i]['label'] for i in reserved], scores=scores.tolist()))
            final[algorithm] = dict(id=r['id'], threshold=artifact['threshold'], metrics=metrics,
                pipeline_bytes=(folder / 'pipeline.pkl').stat().st_size,
                features=len(artifact['pipe']['tfidf'].get_feature_names_out()),
                mean_score_ms=None, replay_max_score_error=error,
                operating_goal_met_on_source_validation=r['operating_point']['goal_met'])
            # Warmed host batch timing, separate from training and device measurements.
            timings = []
            for _ in range(5):
                timed = time.perf_counter()
                score(artifact, [rows[i]['text'] for i in reserved])
                timings.append((time.perf_counter() - timed) * 1000 / len(reserved))
            final[algorithm]['mean_score_ms'] = float(np.median(timings))
    verify_protected(root, protected)
    summary = dict(status='passed', scope='Retrospective source-based development experiment; no prospective claims',
        selected=overall['id'], selected_family=overall['spec']['algorithm'],
        selected_by_family={k: r['id'] for k, r in family.items()},
        any_goal_met=any(r['operating_point']['goal_met'] for r in results),
        attempted_candidates=len(matrix()), completed_candidates=len(results), failures=failures,
        development_records=len(development), reserved_test_records=len(reserved),
        source_validation_family={k: r['operating_point'] for k, r in family.items()},
        final=final, false_alert_review=review, protected_files_verified=len(protected),
        final_models_frozen_before_test=True, labels_changed=0, app_changed=False,
        new_prospective_records=0, fresh_label_decisions=0, elapsed_seconds=time.perf_counter() - start,
        limitations=['Inherited labels; no independent adjudication', 'Historical corpus/test exposure',
            'Only three sources, including one positive-only source', 'Language combines Filipino/Taglish',
            'Source-validation calibration transfer is unverified', 'Host timings; no device benchmark'])
    w.save(output / 'aggregate.json', summary)
    print('Completed. Development selection:', overall['id'], 'operating goal met:', summary['any_goal_met'], flush=True)
    for algorithm, r in final.items():
        print(algorithm, 'reserved test F1', round(r['metrics']['pooled']['f1'], 4),
            'confusion', r['metrics']['pooled']['confusion'], flush=True)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--original', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.root, args.original, args.output)
