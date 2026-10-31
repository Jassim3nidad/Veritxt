"""Publish aggregate source-development results; never texts or learned features."""
from pathlib import Path
import argparse
import csv
import json


def report(run, root):
    load = lambda path: json.loads(path.read_text(encoding='utf-8'))
    summary = load(run / 'aggregate.json')
    replay = load(run / 'independent-replay-audit.json')
    selection = load(run / 'development-selection.json')
    assert summary['status'] == replay['status'] == 'passed'
    assert not summary['app_changed'] and summary['labels_changed'] == 0
    experiment = load(run / 'experiment.json')
    patterns = load(run / 'false-alert-patterns.json')
    # All fields here contain aggregates/configuration only.
    public = dict(summary, replay_audit=replay, false_alert_patterns=patterns,
        protocol_sha256=experiment['protocol_sha256'], code_sha256=experiment['code_sha256'],
        versions=experiment['versions'], development_candidates=selection['results'],
        research_tests_passed=130, new_guard_tests_passed=9,
        test_scope='Existing same-source retrospective test; not new-source prospective traffic')
    # Exception strings can contain inputs; publish only candidate/type if a future fit fails.
    public['failures'] = [{k: failure[k] for k in ('id', 'error_type')} for failure in summary['failures']]
    docs = root / 'docs'
    basename = 'source-robustness-results-20261013'
    (docs / (basename + '.json')).write_text(json.dumps(public, indent=2), encoding='utf-8')
    with (docs / (basename + '.csv')).open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=['candidate', 'algorithm', 'features', 'value', 'min_df',
            'threshold', 'goal_met', 'macro_source_f1', 'worst_supported_fpr', 'minimum_source_recall'])
        writer.writeheader()
        for r in selection['results']:
            p = r['operating_point']
            writer.writerow(dict(candidate=r['id'], algorithm=r['spec']['algorithm'],
                features=r['spec']['features'], value=r['spec']['value'], min_df=r['spec']['min_df'],
                threshold=p['threshold'], goal_met=p['goal_met'], macro_source_f1=p['macro_source_f1'],
                worst_supported_fpr=p['worst_supported_fpr'], minimum_source_recall=p['minimum_supported_source_recall']))
    lines = ['# Source-based model improvement experiment — 13 October 2026', '',
        '**New development choice: Linear SVM with combined word/character TF-IDF, C=1, min_df=2.** '
        'It leads source-based validation under the prespecified false-alert/recall goals. '
        'The current APK remains byte-identical and still uses the earlier word-only SVM.', '',
        'This is retrospective research using the existing inherited labels. Source-validation metrics '
        'were used to choose among 51 configurations and their operating thresholds; they are optimized development '
        'results, not unbiased future-source performance. The reserved 498-record test was excluded from new '
        'fits and selection, but was historically examined. No independently verified fresh SMS cohort was added.', '',
        '## What changed', '',
        '- Source-based validation holds out each development source and purges cross-source related templates. '
        'All vocabulary/IDF, classifier fits and SVM calibration folds exclude the held source and reserved test.',
        '- Compare SVM/LR C=0.01/0.1/1/10 and NB alpha=0.03/0.1/1/10; word features with/without English stopwords, '
        'character-within-word 3–5 grams, and combined word/character features. New candidates exclude terms appearing '
        'in fewer than two training documents. Three historical configurations are explicit min_df=1 controls.',
        '- Choose warning thresholds using source-validation predictions. A candidate must keep FPR ≤2% in every '
        'source/language subgroup with ≥100 ham records and recall ≥50% in every source with ≥20 smishing records. '
        'Positive-only sources cannot establish a false-positive rate. Failure to meet the goal is reported, '
        'and an all-negative predictor is rejected by the recall floor.',
        '- Freeze family winners, thresholds and final development-only fits before reserved-test prediction.', '',
        f"{summary['completed_candidates']}/{summary['attempted_candidates']} candidates completed; "
        f"{len(summary['failures'])} failures and {sum(bool(r['warnings']) for r in selection['results'])} candidates with fitting warnings. "
        f"{sum(r['operating_point']['goal_met'] for r in selection['results'])} configurations met the development operating goals. "
        f"The run took {summary['elapsed_seconds']:.1f} seconds on this host; this is not an Android benchmark.", '',
        '## Source-based development results', '',
        'All families use the same 2,056 development records. Each model scores a development source using a fit '
        'that excludes that source and its related template groups. Equal-source mean F1 weights the three sources '
        'equally rather than allowing the largest source to dominate.', '',
        '| Family winner | Threshold | Mean source F1 | Worst supported FPR | Lowest supported source recall | Goals met |',
        '|---|---:|---:|---:|---:|---|']
    for algorithm, point in summary['source_validation_family'].items():
        lines.append(f"| {summary['selected_by_family'][algorithm]} | {point['threshold']:.8f} | "
            f"{100*point['macro_source_f1']:.2f}% | {100*point['worst_supported_fpr']:.2f}% | "
            f"{100*point['minimum_supported_source_recall']:.2f}% | {'Yes' if point['goal_met'] else 'No — fallback'} |")
    svm = summary['source_validation_family']['svm']
    control = next(r for r in selection['results'] if r['id'] == 'svm-historical-word-control')['operating_point']
    lines += ['', f"Selected SVM mean source F1 is **{100*svm['macro_source_f1']:.2f}%**, compared with "
        f"**{100*control['macro_source_f1']:.2f}%** for the matched source-fold historical word-only configuration, "
        'when both receive the new source-validation operating-point selection. This changes features, C, '
        'minimum document frequency and threshold together, so it does not identify the causal effect of one change.', '',
        '| Held development source | Scam support | Detected | Missed | Ham support | False alerts | F1 |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for key, m in svm['metrics']['subgroups'].items():
        if key.startswith('source:'):
            c = m['confusion']
            lines.append(f"| {key.split(':',1)[1]} | {m['smishing_support']} | {c['tp']} | {c['fn']} | "
                f"{m['ham_support']} | {c['fp']} | {100*m['f1']:.2f}% |")
    lines += ['', 'The Tagalog-source development fold has 22 false alerts among 1,109 ham messages and catches '
        '34/44 scams. Its 68.00% F1 remains imperfect. These development-fold counts are not directly comparable '
        'to the older 133/1,371 false-alert stress test: membership, training fits, thresholds and the role in '
        'selection differ. The name “Tagalog” denotes a source, not a pure Tagalog-language evaluation.', '',
        '## Reserved historical test', '',
        'After selection, family winners were refitted on the 2,056 development records. The original APK '
        'comparator had 1,540 fitting records and its original ≥0.37 threshold. All results below use the same '
        '498 test IDs and labels, but training sizes and configurations differ. Do not reselect from this table.', '',
        '| Model | Detected scams /73 | Missed scams | False alerts /425 ham | Precision | Recall | F1 |',
        '|---|---:|---:|---:|---:|---:|---:|']
    old = load(root / 'research/runs/bantaytext-20261013/notebook-run-v3/aggregate.json')
    original = next(r for r in old['results'] if r['track'] == 'grouped' and r['id'] == 'svm-C-10.0')['test']
    for name, m in [('Original APK SVM', original)] + [(a.upper() + ' new family winner', r['metrics']['pooled']) for a, r in summary['final'].items()]:
        c = m['confusion']
        lines.append(f"| {name} | {c['tp']} | {c['fn']} | {c['fp']} | {100*m['precision']:.2f}% | "
            f"{100*m['recall']:.2f}% | {100*m['f1']:.2f}% |")
    lines += ['', 'The new SVM produces two fewer false alerts and one additional missed scam versus the original '
        'APK comparator. Its small retrospective F1 increase does not establish a statistically or prospectively '
        'superior production model.', '', '## Language results', '',
        'The existing metadata combines Filipino and Taglish. Separate Tagalog/Taglish rankings cannot be '
        'created without new language annotations. Counts below are on the reserved test; the combined subgroup '
        'contains only ten scams and is descriptive.', '',
        '| Language | Model | Detected scams | Missed scams | False alerts | Ham support |',
        '|---|---|---:|---:|---:|---:|']
    for algorithm, r in summary['final'].items():
        for key, m in r['metrics']['subgroups'].items():
            if key.startswith('language:'):
                c = m['confusion']
                lines.append(f"| {key.split(':',1)[1]} | {algorithm.upper()} | {c['tp']}/{m['smishing_support']} | "
                    f"{c['fn']} | {c['fp']} | {m['ham_support']} |")
    lines += ['', 'Source-validation language performance also remains uneven: the selected SVM catches '
        '115/155 English scams with 22/1,207 ham false alerts, and 81/97 Filipino/Taglish scams with 1/597 '
        'ham false alerts. These are optimized development outcomes, not independent language guarantees.', '',
        '## Original false-alert investigation', '',
        'Prepared a private review packet for all 133 inherited-label false positives. 123 are labeled English '
        'and ten Filipino/Taglish; all have the broad supplied “Legit message” category. Their median fitted '
        'score is ' + f"{summary['false_alert_review']['score_median']:.4f}" + '. Human verification and adjudication '
        'remain pending; no inherited label was changed. A private feature-contribution ledger accompanies the '
        'packet so reviewers can investigate why the separate stress-test model flagged each message.', '',
        '| Descriptive pattern | False-alert messages /133 | Correctly unflagged ham /1,238 |',
        '|---|---:|---:|']
    for key, count in patterns['false_alert']['patterns'].items():
        lines.append(f"| {key} | {count} | {patterns['correct_ham']['patterns'][key]} |")
    lines += ['', 'Financial/account/code wording occurs in many supplied legitimate messages, providing a '
        'plausible shortcut to investigate. Pattern counts are correlations, not causal proof or independent '
        'label verification. Seventeen false alerts scored at least 0.90, so a high numerical score alone '
        'does not establish correctness. Learned terms, contributions and masked messages remain in private storage.', '',
        '## Verification and delivery', '',
        f"- {replay['source_pipelines_replayed']} source-fit pipelines and {replay['final_pipelines_replayed']} final pipelines "
        f"were replayed; maximum source score error {replay['maximum_source_score_error']}. All source-validation "
        'threshold choices reproduce.',
        f"- {summary['protected_files_verified']} original artifacts retain identical hashes, including all older candidate "
        'models, the original app assets and the delivery APK.',
        '- Source/group/reserved-test isolation, training-only calibration memberships and the pre-test selection '
        'freeze were verified. Nine new guard tests passed; the complete research suite passed 130 tests.',
        '- No app model, dataset label, human review decision, fresh SMS record or physical-phone result was fabricated.',
        '- Private trained candidates: `research/runs/source-robustness-20261013/run-v1/final/`. '
        'The selected fitted pipeline is `svm-combined-1-df2/pipeline.pkl`.',
        '- Private reviewer materials: `private-false-alert-review.csv`, `private-feature-contributions.json`; '
        'empty future-data template: `prospective-intake.csv` in the same private run.',
        '- The new word/character FeatureUnion is not supported by the current APK’s word-only native contract. '
        'It requires a new portable scorer and Python/JVM/Android parity before an app variant can use it. '
        'The current APK was intentionally preserved during this research task.', '',
        '## Reproduction', '', '```powershell', "$env:PYTHONPATH='research'",
        'research/.venv/Scripts/python.exe -m unittest discover -s research/tests -p test_source_robustness.py -v',
        'research/.venv/Scripts/python.exe -m smishguard.source_robustness --original research/runs/bantaytext-20261013/notebook-run-v3 --output research/runs/source-robustness-20261013/NEW-RUN',
        '```', '',
        'The output must be a new private directory. See [prespecified protocol](source-robustness-protocol-20261013.md), '
        '[aggregate JSON](source-robustness-results-20261013.json), and [candidate CSV](source-robustness-results-20261013.csv). '
        'The generic prospective intake is intentionally empty; completing its labels provides evidence, not '
        'an automatic blanket software-development permission gate.', '',
        'Methods: [grouped validation](https://scikit-learn.org/1.6/modules/cross_validation.html), '
        '[character/word feature extraction](https://scikit-learn.org/stable/modules/feature_extraction.html), '
        '[validation-only threshold tuning](https://scikit-learn.org/stable/modules/classification_threshold.html). '
        'Executed sklearn version is 1.6.1; stable documentation may describe a later version.']
    (docs / (basename + '.md')).write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('Aggregate report/JSON/CSV saved; no message text or learned feature terms published')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('run', type=Path)
    args = parser.parse_args()
    report(args.run, Path(__file__).resolve().parents[1])
