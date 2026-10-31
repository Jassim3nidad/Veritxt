"""Requested 80/20 retraining of the latest NB/SVM comparison.

Reuse its raw-CSV intake, cleaning, features, settings and inference contract.
Keep whole template/sender components together; use integer allocation to meet
rounded 20% row and class counts before fitting. Selection uses only training
OOF predictions. Full training refits never include the outer test partition.
"""
from collections import Counter
from pathlib import Path
import argparse
import importlib.metadata
import json
import math
import pickle
import platform
import shutil
import sys
import time
import warnings

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from threadpoolctl import threadpool_limits

from . import nb_comparison as n

SEED = 42
POLICY = dict(outer_split='80% training / 20% testing, integer-rounded counts',
    allocation='Whole connected groups, exact rounded row/class constraints; seeded group priorities; no score-based retries',
    selection='Pooled 3-fold training-only grouped OOF scam F1; ties: recall, precision, smaller classifier, ID',
    thresholds='NB >=0.5; SVM margin >=0; fixed, no threshold tuning',
    final_fit='Refit all six fixed settings on the entire 80% training partition',
    history='Previously exposed corpus; retrospective, not prospectively unseen',
    android_integration=False)


def split_rows(rows, groups, seed=SEED):
    """Allocate components without splitting them or examining model scores."""
    groups = np.asarray(groups)
    if len(groups) != len(rows):
        raise ValueError('One group ID is required per record')
    labels = np.array([r['label'] for r in rows])
    if set(labels) != {0, 1}:
        raise ValueError('Both ham and smishing are required')
    unique = np.unique(groups)
    members = [np.flatnonzero(groups == g) for g in unique]
    sizes = np.array([len(ii) for ii in members])
    positives = np.array([int(labels[ii].sum()) for ii in members])
    test_n = math.ceil(len(rows) * .2)
    positive_n = int(math.floor(test_n * labels.mean() + .5))
    if not 0 < positive_n < int(labels.sum()) or not 0 < test_n-positive_n < int((labels == 0).sum()):
        raise ValueError('Insufficient two-class support for 80/20')
    # This is a prespecified allocation objective, not a model/score search.
    priorities = np.random.default_rng(seed).random(len(unique))
    result = milp(c=priorities, integrality=np.ones(len(unique)),
        bounds=Bounds(np.zeros(len(unique)), np.ones(len(unique))),
        constraints=LinearConstraint(np.vstack([sizes, positives]),
            [test_n, positive_n], [test_n, positive_n]),
        options=dict(time_limit=30, mip_rel_gap=0))
    if not result.success:
        raise ValueError('Exact grouped 80/20 allocation infeasible or timed out; no leaky fallback: '+result.message)
    test_groups = unique[np.rint(result.x).astype(bool)]
    held = np.isin(groups, test_groups)
    parts = dict(train=np.flatnonzero(~held).tolist(), test=np.flatnonzero(held).tolist())
    n.validate_split(rows, groups, parts)
    if len(parts['test']) != test_n or int(labels[held].sum()) != positive_n:
        raise ValueError('Integer allocation did not satisfy rounded row/class constraints')
    return parts


def training_folds(rows, groups, training, seed=SEED):
    ids = np.array(training)
    labels = np.array([rows[i]['label'] for i in ids])
    folds = []
    coverage = Counter()
    for a, b in StratifiedGroupKFold(n_splits=3, shuffle=True, random_state=seed).split(ids, labels, np.asarray(groups)[ids]):
        train, validation = ids[a].tolist(), ids[b].tolist()
        if any({rows[i]['label'] for i in ii} != {0, 1} for ii in (train, validation)):
            raise ValueError('Training CV fold lacks both classes; no seed retry')
        if set(np.asarray(groups)[train]) & set(np.asarray(groups)[validation]):
            raise ValueError('Group overlap in training CV')
        folds.append(dict(train=train, validation=validation))
        coverage.update(validation)
    if set(coverage) != set(training) or any(v != 1 for v in coverage.values()):
        raise ValueError('Training OOF membership must cover each training row exactly once')
    return folds


def classifier(spec):
    if spec['algorithm'] == 'nb':
        return MultinomialNB(alpha=spec['alpha'])
    return LinearSVC(C=spec['C'], random_state=SEED, dual='auto', max_iter=10000)


def fit(rows, ids, spec):
    vec = n.vectorizer()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        x = vec.fit_transform([rows[i]['text'] for i in ids])
        model = classifier(spec).fit(x, [rows[i]['label'] for i in ids])
    if caught:
        raise ValueError('Fitting warning: '+'; '.join(str(w.message) for w in caught))
    if model.classes_.tolist() != [0, 1]:
        raise ValueError('Class orientation changed')
    return vec, model


def choose(results):
    return sorted(results, key=lambda r: (-r['cv']['f1'], -r['cv']['recall'],
        -r['cv']['precision'], r['model_bytes'], r['spec']['id']))[0]['spec']['id']


def train(dataset, output):
    output = Path(output)
    if output.exists():
        raise FileExistsError('Use a new experiment directory')
    records, identity = n.read_dataset(dataset)
    rows, ledger, audit = n.clean(records)
    output.mkdir(parents=True, exist_ok=False)
    n.save(output/'dataset.json', rows)
    n.save(output/'cleaning-ledger.json', ledger)
    print('Cleaned dataset:', n.counts(rows), flush=True)
    groups = n.group_rows(rows)
    parts = split_rows(rows, groups)
    folds = training_folds(rows, groups, parts['train'])
    audit.update(groups=len(set(groups)),
        mixed_label_template_groups=sum(len({rows[i]['label'] for i in np.flatnonzero(groups == g)}) > 1 for g in set(groups)),
        partitions={p:dict(n.counts([rows[i] for i in ii]), groups=len(set(groups[ii])), fraction=len(ii)/len(rows)) for p, ii in parts.items()},
        group_overlap=int(len(set(groups[parts['train']]) & set(groups[parts['test']]))),
        normalized_text_overlap=len({rows[i]['text'].casefold() for i in parts['train']} & {rows[i]['text'].casefold() for i in parts['test']}),
        cv_partitions=[{p:n.counts([rows[i] for i in ii]) for p, ii in f.items()} for f in folds])
    n.save(output/'data-audit.json', audit)
    n.save(output/'splits.json', dict(partitions=parts, groups=groups.tolist(), training_cv=folds, seed=SEED, target=[.8, .2], policy=POLICY))
    n.save(output/'configuration.json', dict(policy=POLICY, matrix=n.matrix(), input_identity=identity,
        seed=SEED, token_pattern=n.TOKEN_PATTERN, stop_words=n.STOP_WORDS, preprocessing='Unchanged latest NB comparison: whitespace collapse; lowercase; word TF-IDF (1,2); raw TF; smooth IDF; L2'))
    n.save(output/'environment.json', dict(python=sys.version, platform=platform.platform(),
        packages={p:importlib.metadata.version(p) for p in ('numpy', 'scipy', 'scikit-learn', 'threadpoolctl', 'nbformat', 'nbclient')},
        timestamp_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())))
    print('Outer partition counts:', audit['partitions'], flush=True)
    results = []
    train_ids = parts['train']
    index = {i:j for j, i in enumerate(train_ids)}
    y = [rows[i]['label'] for i in train_ids]
    with threadpool_limits(limits=1):
        for spec in n.matrix():
            started = time.perf_counter()
            oof = np.full(len(train_ids), np.nan)
            fold_results = []
            for fold in folds:
                vec, model = fit(rows, fold['train'], spec)
                s, pred = n.predictions(model, vec.transform([rows[i]['text'] for i in fold['validation']]), spec)
                oof[[index[i] for i in fold['validation']]] = s
                fold_results.append(n.metrics([rows[i]['label'] for i in fold['validation']], pred))
            if not np.isfinite(oof).all():
                raise ValueError('Incomplete training-only OOF scores')
            threshold = .5 if spec['algorithm'] == 'nb' else 0.
            cv = n.metrics(y, (oof >= threshold).astype(int))
            cv_seconds = time.perf_counter()-started
            started = time.perf_counter()
            vec, model = fit(rows, train_ids, spec)
            seconds = time.perf_counter()-started
            folder = output/spec['id']; folder.mkdir()
            (folder/'vectorizer.pkl').write_bytes(pickle.dumps(vec, protocol=5))
            (folder/'model.pkl').write_bytes(pickle.dumps(model, protocol=5))
            n.export_reference(vec, model, spec, folder/'candidate-model.json')
            n.save(folder/'training-oof-predictions.json', dict(indices=train_ids, labels=y, scores=oof.tolist(), predictions=(oof >= threshold).astype(int).tolist()))
            result = dict(spec=spec, cv=cv, cv_folds=fold_results, cv_seconds=cv_seconds,
                training_seconds=seconds, features=len(vec.vocabulary_),
                model_bytes=(folder/'model.pkl').stat().st_size, vectorizer_bytes=(folder/'vectorizer.pkl').stat().st_size)
            results.append(result)
            print(spec['id'], 'training CV F1:', round(cv['f1'], 6), flush=True)
    selected = choose(results)
    n.save(output/'cv-results.json', results)
    n.save(output/'selection.json', dict(selected=selected, best_nb=choose([r for r in results if r['spec']['algorithm'] == 'nb']),
        test_evaluation_ids=[s['id'] for s in n.matrix()], policy=POLICY))
    sources = {'implementation.py':Path(__file__), 'nb_comparison.py':Path(n.__file__)}
    for name, path in sources.items():
        shutil.copyfile(path, output/name)
    n.save(output/'freeze.json', dict(dataset_sha256=n.digest(dataset), sources={name:n.digest(path) for name, path in sources.items()},
        files={p.relative_to(output).as_posix():n.digest(p) for p in output.rglob('*') if p.is_file()}))
    print('Frozen training CV selection:', selected, '; test has not been transformed.', flush=True)


def verify_freeze(dataset, output):
    output = Path(output)
    frozen = n.load(output/'freeze.json')
    if n.digest(dataset) != frozen['dataset_sha256']:
        raise ValueError('Dataset changed')
    for name, path in {'implementation.py':Path(__file__), 'nb_comparison.py':Path(n.__file__)}.items():
        if n.digest(path) != frozen['sources'][name]:
            raise ValueError('Implementation changed: '+name)
    for name, sha in frozen['files'].items():
        if n.digest(output/name) != sha:
            raise ValueError('Frozen file changed: '+name)


def evaluate(dataset, output):
    output = Path(output)
    verify_freeze(dataset, output)
    with (output/'test-evaluation-started.json').open('x', encoding='utf-8') as f:
        json.dump(dict(selection_sha256=n.digest(output/'selection.json')), f)
    rows = n.load(output/'dataset.json')
    ids = n.load(output/'splits.json')['partitions']['test']
    texts = [rows[i]['text'] for i in ids]; y = [rows[i]['label'] for i in ids]
    selection = n.load(output/'selection.json')
    results = []
    with threadpool_limits(limits=1):
        for item in n.load(output/'cv-results.json'):
            spec = item['spec']; folder = output/spec['id']
            vec = pickle.loads((folder/'vectorizer.pkl').read_bytes())
            model = pickle.loads((folder/'model.pkl').read_bytes())
            s, pred = n.predictions(model, vec.transform(texts), spec)
            n.save(folder/'test-predictions.json', dict(indices=ids, labels=y, scores=s.tolist(), predictions=pred.tolist()))
            checks = n.inference_checks(vec, model, spec, n.load(folder/'candidate-model.json'), texts)
            n.save(folder/'inference-checks.json', checks)
            subgroups = {}
            for field in ('language', 'source'):
                for value in sorted({rows[i][field] for i in ids}):
                    jj = [j for j, i in enumerate(ids) if rows[i][field] == value]
                    support = Counter(y[j] for j in jj)
                    subgroups[field+':'+value] = dict(records=len(jj), ham=support[0], smishing=support[1],
                        metrics=n.metrics([y[j] for j in jj], pred[jj]) if min(support[0], support[1]) >= 5 else None)
            results.append(dict(item, test=n.metrics(y, pred), subgroups=subgroups,
                parity=dict(max_feature_error=checks['max_feature_error'], max_score_error=checks['max_score_error'])))
            print(spec['id'], 'test F1:', round(results[-1]['test']['f1'], 6), flush=True)
    n.save(output/'test-results.json', dict(selected=selection['selected'], results=results, policy=POLICY))
    verify_freeze(dataset, output)
    print('80/20 retraining and single test evaluation complete.', flush=True)


def report(dataset, output, destination):
    output, destination = Path(output), Path(destination)
    verify_freeze(dataset, output)
    data = n.load(output/'test-results.json'); audit = n.load(output/'data-audit.json')
    split = n.load(output/'splits.json')
    rows = n.load(output/'dataset.json')
    for result in data['results']:
        pred = n.load(output/result['spec']['id']/'test-predictions.json')
        if pred['indices'] != split['partitions']['test'] or pred['labels'] != [rows[i]['label'] for i in pred['indices']]:
            raise ValueError('Saved test membership/labels changed')
        if n.metrics(pred['labels'], pred['predictions']) != result['test']:
            raise ValueError('Saved test metrics do not match predictions')
    destination.mkdir(parents=True, exist_ok=True)
    aggregate = dict(selected=data['selected'], audit=audit, results=data['results'], policy=POLICY,
        freeze_sha256=n.digest(output/'freeze.json'))
    n.save(destination/'results.json', aggregate)
    comparison = [dict(id=r['spec']['id'], cv_f1=r['cv']['f1'], **{k:r['test'][k] for k in ('accuracy','precision','recall','f1','macro_f1','fpr','fnr')},
        tn=r['test']['confusion_matrix'][0][0], fp=r['test']['confusion_matrix'][0][1],
        fn=r['test']['confusion_matrix'][1][0], tp=r['test']['confusion_matrix'][1][1]) for r in data['results']]
    n.write_csv(destination/'comparison.csv', comparison)
    lines = ['# 80/20 retraining — 19 October 2026', '',
        f'**Training-CV-selected model: {data["selected"]}.** All six latest NB/SVM settings were retrained.', '',
        'The original October 12 ZIP and latest NB comparison cleaning/features are reused. '
        'Labels are inherited; this historically exposed corpus supports retrospective evaluation only. '
        'Models, vocabulary, text and row predictions remain private. Current Android assets and prior notebooks are preserved.', '',
        '| Partition | Records | Ham | Smishing | Fraction | Groups |', '|---|---:|---:|---:|---:|---:|']
    for name, a in audit['partitions'].items():
        lines.append(f'| {name} | {a["records"]} | {a["ham"]} | {a["smishing"]} | {a["fraction"]:.4%} | {a["groups"]} |')
    lines += ['', '20% is rounded upward to a whole record. Test positive support is rounded from the corpus class ratio. '
        'Whole template/sender connected components are allocated using binary integer constraints and fixed seed-42 group priorities. '
        'This changes the old fold allocator, which substantially missed its requested sizes. '
        f'Group overlap: {audit["group_overlap"]}; normalized-text overlap: {audit["normalized_text_overlap"]}. '
        'The split is frozen before fitting. No score-based split/seed search or random leakage fallback is used. '
        'This constrained allocation is not a conventional row-random split, and group/source composition can differ from traffic.', '',
        'Three grouped cross-validation folds are formed entirely within the 80% training partition. '
        'Each fold learns its own vocabulary/IDF and classifier; pooled training OOF F1 selects the configuration, '
        'then recall, precision, smaller classifier and ID break ties. Fixed NB threshold >=0.5 and SVM margin >=0; '
        'no calibration or threshold tuning. All six classifiers are refitted on every training row before '
        'selection/artifact hashes are sealed and the 20% test partition is transformed once. '
        'All configurations are reported; the test ranking cannot change selection.', '',
        '| Configuration | Training CV F1 | Test accuracy | Scam precision | Scam recall | Scam F1 | TN/FP/FN/TP |',
        '|---|---:|---:|---:|---:|---:|---|']
    for r in comparison:
        lines.append(f'| {r["id"]} | {r["cv_f1"]:.2%} | {r["accuracy"]:.2%} | {r["precision"]:.2%} | {r["recall"]:.2%} | {r["f1"]:.2%} | {r["tn"]}/{r["fp"]}/{r["fn"]}/{r["tp"]} |')
    lines += ['', 'Metrics were recomputed from the saved test predictions. Every candidate passed the existing independent '
        'JSON feature/score/decision checks on the test cohort and 115 synthetic probes at 1e-10 tolerance. '
        'These are Python inference checks, not Android integration. The schema-8 tokenizer still requires a matching Android scorer.', '',
        'The two-class source/rule labels, source imbalance, heuristic template grouping, approximate language metadata and '
        'historical exposure remain limitations. Different test membership prevents treating differences from older reports '
        'as a controlled accuracy improvement. CV fold supports, per-fold metrics, source/language test supports, '
        'FPR/FNR and classification reports are in results.json. Source terms/attribution remain in docs/source-evidence.md.', '',
        'Reproduce from the repository root using a new private output directory:', '', '```powershell',
        "$env:PYTHONPATH='research'",
        'research/.venv/Scripts/python.exe -m smishguard.holdout_8020 train research/data/newdata-20261013/smishguard_dataset_2026-10-12.zip research/runs/holdout-8020-20261019/NEW-RUN',
        'research/.venv/Scripts/python.exe -m smishguard.holdout_8020 evaluate research/data/newdata-20261013/smishguard_dataset_2026-10-12.zip research/runs/holdout-8020-20261019/NEW-RUN',
        'research/.venv/Scripts/python.exe -m smishguard.holdout_8020 report research/data/newdata-20261013/smishguard_dataset_2026-10-12.zip research/runs/holdout-8020-20261019/NEW-RUN --report-dir docs/holdout-8020-20261019',
        '```', '', f'Completed private run: `{output.as_posix()}`.', '']
    (destination/'RESULTS.md').write_text('\n'.join(lines), encoding='utf-8')
    n.save(output/'completion-verification.json', dict(freeze_verified=True, metrics_recomputed=True,
        training_records=audit['partitions']['train']['records'], test_records=audit['partitions']['test']['records'],
        group_overlap=audit['group_overlap'], normalized_text_overlap=audit['normalized_text_overlap'],
        models_evaluated=len(data['results']), json_parity_passed=True,
        public_files={p.name:n.digest(p) for p in destination.iterdir() if p.is_file()}))
    print('Verified aggregate report:', destination/'RESULTS.md', flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['train', 'evaluate', 'report'])
    parser.add_argument('dataset', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--report-dir', type=Path, default=Path('docs/holdout-8020-20261019'))
    args = parser.parse_args()
    if args.phase == 'train':
        train(args.dataset, args.output)
    elif args.phase == 'evaluate':
        evaluate(args.dataset, args.output)
    else:
        report(args.dataset, args.output, args.report_dir)


if __name__ == '__main__':
    main()
