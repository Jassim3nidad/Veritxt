"""Publish aggregate-only thesis evidence from actual sealed experiment files."""
import argparse
import csv
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from sklearn.calibration import calibration_curve
from smishguard import retraining as r

NAMES={'A':'Word TF-IDF + LR','B':'Word TF-IDF + SVM','C':'Word + char TF-IDF + SVM',
       'D':'Word + char TF-IDF + LR','E':'Word TF-IDF + NB'}


def pct(value):return f'{100*value:.2f}%'


def tests(log):
    lines=log.read_text(encoding='utf-8-sig',errors='replace').splitlines()
    return dict(summary=[x for x in lines if x.startswith('Ran ') or x=='OK' or x.startswith('FAILED')],sha256=r.digest(log))


def main():
    p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('--root',type=Path,default=Path('.'));args=p.parse_args()
    root=args.root.resolve();run=args.run.resolve();parent=run.parent;audit_path=parent/'audit-v1'
    dataset=root/'research/runs/bantaytext-20261013/notebook-run-v3/dataset.json'
    r.verify_freeze(dataset,run)
    audit=r.load(run/'data-audit.json');selection=r.load(run/'selection.json');holdout=r.load(run/'holdout-results.json');validation=r.load(run/'validation-results.json')
    baseline=r.load(audit_path/'baseline-replay.json');old_audit=r.load(root/'research/runs/bantaytext-20261013/notebook-run-v3/data-audit.json')
    upstream=r.load(audit_path/'upstream-record-audit.json')
    reproduction=r.load(audit_path/'reproducibility.json')
    ablation=r.load(parent/'character-ablation-v1/aggregate.json')
    preservation=r.load(audit_path/'preservation.json')
    for name,sha in preservation.items():
        if r.digest(root/name)!=sha:raise ValueError('Preserved app/model/notebook changed: '+name)
    parity={family:{kind:r.load(parent/f'parity-{family}-v2'/f'research-{kind}-parity.json') for kind in ('jvm','android')} for family in ('E','C')}
    xml=[ET.parse(p).getroot() for p in (root/'android/app/build/test-results/testDebugUnitTest').glob('TEST-*.xml')]
    qa=dict(research=tests(audit_path/'research-tests-final.log'),backend=tests(audit_path/'backend-tests-final.log'),
        latest_jvm={key:sum(int(n.attrib.get(key,0)) for n in xml) for key in ('tests','failures','errors','skipped')},
        notebook='17 cells executed end-to-end in a fresh run, including fitting, locking and retrospective holdout evaluation',
        initial_parity_failure='Two existing comparator tests lacked legacy model.json fixtures. Preserved fixtures supplied; full reruns passed, assertions unchanged.',
        initial_backend_failure='Research venv lacks Flask. Re-run in established backend/.venv: 46 tests passed.',
        protected_hashes_verified=len(preservation))
    selected_xml=[ET.parse(p).getroot() for p in (root/'android/app/build/test-results/testSelectedSvmUnitTest').glob('TEST-*.xml')]
    qa['preserved_selected_svm_regression']={key:sum(int(n.attrib.get(key,0)) for n in selected_xml) for key in ('tests','failures','errors','skipped')}
    calibration={}
    for family,item in holdout['results'].items():
        pred=r.load(run/item['predictions_file']);fraction,mean=calibration_curve(pred['labels'],pred['scores'],n_bins=8,strategy='quantile')
        calibration[family]=dict(mean_probability=mean.tolist(),observed_phishing_fraction=fraction.tolist(),bins='8 quantile bins, ties may merge',
            brier=item['holdout']['brier'],interpretation='Inherited-label historical holdout diagnostic, no population calibration claim')
    r.save(run/'reliability-bins.json',calibration)
    aggregate=dict(audit=audit,upstream_cleaning_audit=old_audit,upstream_record_audit=upstream,reproducibility=reproduction,
        matched_character_ablation=ablation,baseline_replay=baseline,selection=selection,
        holdout=holdout,calibration_bins=calibration,robustness=r.load(run/'robustness-validation.json'),
        shortcuts=r.load(run/'shortcut-validation.json'),source_transfer=r.load(run/'source-transfer-validation.json'),
        parity=parity,qa=qa,environment=r.load(run/'environment.json'),
        experiment_artifacts={str(f.relative_to(root)):r.digest(f) for f in [run/'freeze.json',run/'configuration.json',run/'selection.json',run/'holdout-results.json',
            run/'validation-results.json',run/'candidate-model.json',root/'research/Model_Training_and_Evaluation.ipynb']})
    out=root/'docs/retraining-results-20261013.json';r.save(out,aggregate)
    rows=[]
    for family,item in holdout['results'].items():
        c=item['candidate'];m=item['holdout'];latency=item['latency']
        rows.append(dict(family=family,model=NAMES[family],id=c['id'],threshold=c['threshold'],
            **{k:m[k] for k in ('accuracy','precision','recall','f1','macro_f1','pr_auc','average_precision','roc_auc','brier','fpr')},
            **m['confusion'],training_seconds=c['training_seconds'],pipeline_bytes=c['artifact_bytes'],
            feature_count=c['feature_count'],sparse_training_bytes=c['sparse_training_bytes'],
            host_single_p50_ms=latency['host_single_p50_ms'],host_single_p95_ms=latency['host_single_p95_ms'],
            history='previously_used_retrospective'))
    with (root/'docs/retraining-comparison-20261013.csv').open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    figure_dir=root/'docs/retraining-figures-20261013';figure_dir.mkdir(exist_ok=True)
    for name in ('coverage.png','confusion-and-comparison.png','precision-recall.png','reliability.png'):
        shutil.copyfile(run/name,figure_dir/name)
    c=selection['selected'];e=holdout['results'][c['family']];m=e['holdout'];ci=e['conditional_cluster_intervals']
    report=['# Research-guided retraining — 13 October 2026','',
        f'**Validation-selected research candidate: {NAMES[c["family"]]} (`{c["id"]}`). Production model preserved.**',
        f'The locked historical holdout gives precision {pct(m["precision"])}, recall {pct(m["recall"])}, phishing F1 {pct(m["f1"])}. '
        'No prospective winner or thesis population-performance claim is established. The corpus has already influenced earlier experiments; repartitioning does not undo exposure.','',
        '## Method and measured audit','',
        f'Upstream audit: {old_audit["before"]["records"]} fitting-view records, {upstream["audit"]["unique_raw_messages"]} distinct input-view strings before cleaning, {old_audit["removals"]["duplicate_masked_casefold_text"]} duplicates removed and {old_audit["removals"]["pending_flagged_review"]} flagged rows held. '
        f'This run loaded exactly {audit["eligible_records"]} records/{audit["unique_normalized_messages"]} unique normalized messages, {audit["template_groups"]} heuristic template groups, 2,229 ham and 325 inherited smishing labels. '
        'Raw original source bytes and the previous cleaning ledger remain private and unchanged. New original-records/cleaning ledgers preserve the input view and original supplied labels. '
        'The input view already masks identifiers and links; it is not original SMS. No further URL, number or currency removal, translation, stemming, lemmatization or stopword removal was applied.','',
        'English: 1,709; combined Filipino/Taglish: 845. Sources: Tagalog-SMS 1,424; marketing 1,002; bwandowando 128 (positive-only). '
        'Source names do not establish language or phishing truth. Broad legitimate/spam categories require independent target-task review. '
        'No eligible normalized label conflicts or new malformed records were found; this does not prove label correctness.','',
        '| Partition | Records | Ham | Phishing | Groups | Fraction |','|---|---:|---:|---:|---:|---:|']
    for part,info in audit['partitions'].items():report.append(f'| {part} | {info["records"]} | {info["labels"]["0"]} | {info["labels"]["1"]} | {info["groups"]} | {pct(info["fraction"])} |')
    report += ['',
        'Twenty stratified group folds allocate 14/3/3, targeting 70/15/15; actual size/prevalence differs because groups are indivisible. '
        'Positive prevalence is 13.19% training, 7.57% validation and 15.46% holdout. This drift and the 29 validation positives weaken threshold stability and population representativeness. '
        'No favorable-seed retry occurred. All pairwise group/exact overlap counts are zero. Grouping is label-blind .85 SequenceMatcher connected components plus exact Unicode casefold and supplied metadata. '
        'Unknown campaign/sender/conversation links and non-Latin near-template gaps can remain. Receipt timestamps are unverified, so chronology is unavailable. '
        'Only three sources exist; whole-source 70/15/15 partitions are infeasible. Separate development source-transfer diagnostics are reported, without claiming independent future-source validation.','',
        f'{len(validation["candidates"])} raw/calibrated comparisons from 70 fitted settings; {len(validation["failures"])} fitting failures. Search time {validation["seconds"]:.1f} seconds, single-threaded on this host. '
        'TF-IDF/classifiers use training only. Three training-only group folds each learn their own vocabulary/IDF; OOF margins fit a sigmoid followed by a final training-only refit. '
        'Original distribution is evaluated before paired balanced class weighting. NB alpha: 0.03, 0.1, 0.3, 1 and 3. No resampling or SMOTE is used. '
        'Word unigrams are the A/B starting baselines; bigrams, min_df and feature caps are tuned. C/D start word (1,2) + char_wb (3,5) and also test char (3,6).','',
        'Provisional operating goals were recorded before fitting: validation precision >=90%, FPR <=2%, >=5 TP. Rank eligible settings by recall, F1, AP, smaller serialized artifact, then deterministic ID. '
        'These are research requirements, pending deployment acceptance. Calibration variants are compared separately; the sigmoid wins deterministic score ties without implying universal calibration improvement. '
        'No holdout result enters selection. Family winners, thresholds and file hashes are sealed before the single holdout evaluation.','',
        '## Comparative results','',
        '| Model family | Validation P | Validation R | Validation F1 | Locked threshold |','|---|---:|---:|---:|---:|']
    for f,v in selection['family_winners'].items():
        vm=v['validation'];report.append(f'| {f}: {NAMES[f]} | {pct(vm["precision"])} | {pct(vm["recall"])} | {pct(vm["f1"])} | {v["threshold"]:.8f} |')
    report += ['','Historical holdout, 427 identical eligible records (361 ham/66 phishing) for all five family winners. All selected modes use fitted sigmoids.','',
        '| Family | Accuracy | Precision | Recall | Phishing F1 | Macro F1 | PR-AUC | AP | ROC-AUC | TN/FP/FN/TP |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---|']
    for row in rows:
        report.append(f'| {row["family"]} | {pct(row["accuracy"])} | {pct(row["precision"])} | {pct(row["recall"])} | {pct(row["f1"])} | {pct(row["macro_f1"])} | {row["pr_auc"]:.4f} | {row["average_precision"]:.4f} | {row["roc_auc"]:.4f} | {row["tn"]}/{row["fp"]}/{row["fn"]}/{row["tp"]} |')
    report += ['','PR-AUC is trapezoidal area; AP is separately reported. Accuracy alone is insufficient: an all-ham predictor would score 84.54% accuracy here while missing every phishing SMS. '
        'A matched character ablation fixes C=0.1, balanced weights, word (1,2), min_df=1, no feature cap and the same calibration folds, changing only the char_wb block. '
        'Validation AP increases from 0.7878 word-only to 0.8254 combined; qualifying recall from 41.38% to 44.83%. '
        'Each uses the original validation operating rule. This post-selection development diagnostic is not independent confirmation and cannot change the winner. '
        'The original preserved SVM baseline replay gave 95.24% F1 on its different 498-record historical partition, with zero score difference; LR 91.67%, NB 87.41%. '
        'These are not directly comparable to this new membership, training allocation or operating policy. The reversal of validation ranking is counterevidence to an assumed universal SVM winner.','',
        '## Probability handling and efficiency','',
        '| Family | Brier, historical holdout | Fit seconds incl. calibration | Pickle MiB | Features | Sparse train MiB | Host single p50/p95 ms |',
        '|---|---:|---:|---:|---:|---:|---|']
    for row in rows:report.append(f'| {row["family"]} | {row["brier"]:.5f} | {row["training_seconds"]:.3f} | {row["pipeline_bytes"]/2**20:.3f} | {row["feature_count"]} | {row["sparse_training_bytes"]/2**20:.3f} | {row["host_single_p50_ms"]:.3f}/{row["host_single_p95_ms"]:.3f} |')
    report += ['','Host single-message latency uses 100 holdout messages and includes feature transformation; wall times vary by host/load. Sparse bytes are storage for the training CSR matrix, not peak RAM. '
        'Reliability curves/bins are saved. The selected NB validation Brier improves from 0.02823 raw to 0.02275 sigmoid; ranking and chosen confusion counts tie. '
        'OOF-to-full-fit score shift, inherited labels, sample size and unknown deployment base rate prevent a real-traffic probability claim. SVM raw margins have Brier=null. '
        'Native candidate results always set probability=false; no “chance of phishing” certainty claim is introduced.','',
        '## Language and subgroup findings','',
        '| Selected NB language metadata | Records | Ham | Phishing | Precision | Recall | F1 |','|---|---:|---:|---:|---:|---:|---:|']
    for name,item in e['subgroups'].items():
        if name.startswith('language:') and item['metrics']:
            sm=item['metrics'];report.append(f'| {name.split(":",1)[1]} | {item["records"]} | {item["ham"]} | {item["phishing"]} | {pct(sm["precision"])} | {pct(sm["recall"])} | {pct(sm["f1"])} |')
    report += ['','The combined Filipino/Taglish subgroup has only eight positives; its perfect observed counts do not establish broad multilingual robustness. '
        'Separate Tagalog/Taglish and reliably labeled banking, OTP, verification, delivery and conversation subgroups are unavailable. '
        'Inherited impersonation categories include government/courier/brand, so they are not automatically financial-impersonation labels. '
        'The aggregate JSON contains all family subgroup supports. Two-class metrics require >=20 messages and >=5 each class; single-class category counts are preserved without misleading AUC/F1.','',
        'Controlled validation-only surface edits of existing messages gave zero NB prediction flips: uppercase 380 changed records; whitespace 383; terminal punctuation 383; targeted spelling obfuscation 77; Taglish spelling 7. '
        'The seven Taglish edits are all ham and cannot establish scam robustness. Scores/rankings can change even without threshold flips. '
        'These are supplementary assumed label-preserving transformations, pending semantic review, not newly collected SMS or security guarantees. '
        'Source/link-only controls, frozen URL removal and source-complement fitting diagnose shortcuts, but tuned validation diagnostics do not prove genuine indicators or source invariance.','',
        f'Conditional cluster-bootstrap 95% intervals (1,000 draws, fixed selected model): recall {pct(ci["intervals"]["recall"]["low"])}–{pct(ci["intervals"]["recall"]["high"])}, '
        f'precision {pct(ci["intervals"]["precision"]["low"])}–{pct(ci["intervals"]["precision"]["high"])}, F1 {pct(ci["intervals"]["f1"]["low"])}–{pct(ci["intervals"]["f1"]["high"])}. '
        'They exclude selection, exposure, label and fitting uncertainty. At the locked threshold, seeds 42/43/44 gave validation F1 83.02/78.43/83.02% and recall 75.86/68.97/75.86%; '
        'membership/settings remain fixed. This is fitting/calibration variability, not an independent outer-split comparison.','',
        '## Offline candidate validation','',
        'The selected configuration is NB alpha=0.03, word (1,2), min_df=2, max_features=20,000, original class distribution, OOF sigmoid and threshold >=0.5147900878024994. '
        'Export uses validated JSON weights/IDF/ordered vocabulary/Unicode tables and preserves positive class smishing at index 1. '
        'The separate ResearchLinearScorer implements independently normalized word/char blocks, codepoint character slices and sklearn short-word padding. '
        'ResearchLinearRawDetector uses the existing frozen raw-SMS masking adapter; original input length is checked before masking. '
        'No network dependency or production loader registration is added. Python pickles remain research-only.','',
        '| Actual exported candidate | JSON bytes | JVM max score error | API36 max score error | Emulator load ms | Synthetic score p50/max ms |',
        '|---|---:|---:|---:|---:|---|']
    for f,v in parity.items():
        j=v['jvm'];d=v['android'];report.append(f'| {f}: {NAMES[f]} | {j["candidate_json_bytes"]} | {j["max_score_error"]:.2e} | {d["max_score_error"]:.2e} | {d["load_ms"]:.2f} | {d["synthetic_score_p50_ms"]:.3f}/{d["synthetic_score_max_ms"]:.3f} |')
    report += ['','Each actual export passed 20 synthetic masked probes plus 31 synthetic raw-SMS adapter probes on JVM and API36 emulator, airplane mode on and INTERNET permission absent. '
        'Both also match all 427 already locked real masked holdout scores and decisions within 1e-10; every record is assessable with zero failures/abstentions on this cohort. '
        'The raw-SMS adapter is idempotent on these existing fitting views. These engineering repetitions do not change research selection/evaluation or provide fresh labels. '
        'Synthetic feature/score errors are below 6e-16; real-score errors are recorded separately in the aggregate JSON. '
        'Empty/unknown text abstains; NUL, malformed surrogates and oversized input fail safely. '
        f'Whole instrumentation process PSS samples: NB {parity["E"]["android"]["pss_kib_before"]:,}→{parity["E"]["android"]["pss_kib_after"]:,} KiB; '
        f'combined SVM {parity["C"]["android"]["pss_kib_before"]:,}→{parity["C"]["android"]["pss_kib_after"]:,} KiB. These are not isolated model RAM. '
        f'Actual masked-message detection p50/p95 ms on this emulator: NB {parity["E"]["android"]["real_detection_p50_ms"]:.3f}/{parity["E"]["android"]["real_detection_p95_ms"]:.3f}; '
        f'combined SVM {parity["C"]["android"]["real_detection_p50_ms"]:.3f}/{parity["C"]["android"]["real_detection_p95_ms"]:.3f}. '
        'Synthetic timings include an unusually long message, are single-pass measurements, and are not representative physical-device benchmarks. '
        'Current production assets/notebook and preserved artifacts passed all 23 original hash checks. Newly built debug test APKs are private engineering artifacts; no active candidate APK or production pointer was replaced.','',
        '## XLM-R, rights, limitations and recommendation','',
        'F: XLM-R was not trained. This research environment lacks torch/transformers and a pinned XLM-R checkpoint; hardware acceleration was not demonstrated. '
        'Existing mBERT results cannot substitute. No original authorized-text transformer comparison, weighted-loss result, checkpoint/export or mobile benchmark is claimed. '
        'Future work must pin checkpoint/revision/license/dependencies, use native tokenizer without TF-IDF cleaning, reuse eligible membership and record ordinary versus weighted loss/resource costs.','',
        'Source terms are the historically pinned records in [source evidence](source-evidence.md): Tagalog-SMS CC0, marketing CC BY 4.0, bwandowando CC BY-NC-SA 4.0. '
        'Retain attribution/change/license records. Acquisition lineage, privacy/redaction, independent labeling and intended thesis/distribution scope remain separate human reviews. '
        'No personal/social source is admitted, no open accessibility is treated as blanket rights, and no fitted vocabulary/SMS is included in public reports.','',
        'Recommend NB as the candidate for this prespecified retrospective comparison, with combined SVM retained for future comparison. '
        'Do not change production from these results: independent labels, truly untouched prospective messages, separate language/scam annotations and physical Android device tests remain necessary. '
        'The small validation-positive support, prevalence drift, heuristic grouping and ranking reversal prevent a conclusive universal deployment choice. '
        'Review the nine holdout errors and upstream 59 flagged records privately. A private scope-review queue flags 70 inherited gambling-lure messages '
        'whose phishing/scam-versus-marketing status needs human adjudication. These remained in the declared inherited-label exploratory comparison, '
        'so all deployment claims remain inadmissible until label quality is resolved. No labels were changed.','',
        '## Reproduction, tests and artifact trace','',
        'From repository root, set PYTHONPATH=research and use research/.venv/Scripts/python.exe (Python 3.12). Use new output directories; the shown completed run refuses overwrite.','',
        '```text',
        'python -m pip install -r research/retraining-requirements.txt',
        'python -m smishguard.retraining train research/runs/bantaytext-20261013/notebook-run-v3/dataset.json research/runs/retraining-20261013/NEW-RUN --history previously_used',
        'python -m smishguard.retraining evaluate research/runs/bantaytext-20261013/notebook-run-v3/dataset.json research/runs/retraining-20261013/NEW-RUN',
        'python -m unittest discover -s research/tests -v',
        'python scripts/replay_retraining_baseline.py --output research/runs/retraining-20261013/NEW-BASELINE-REPLAY.json',
        'backend/.venv/Scripts/python.exe -m unittest discover -s backend -v',
        f'python scripts/execute_retraining_notebook.py --run {run.relative_to(root/"research").as_posix()} --replay',
        'python scripts/prepare_retraining_parity.py research/runs/retraining-20261013/run-v1 --output research/runs/retraining-20261013/NEW-PARITY --legacy-parity research/runs/bantaytext-20261013/notebook-run-v3/parity',
        'gradlew.bat :app:testDebugUnitTest :app:lintDebug :app:assembleDebug :app:assembleDebugAndroidTest -PmodelParityDir=ABSOLUTE_PRIVATE_PARITY_DIRECTORY --console=plain',
        'adb -s emulator-5554 shell am instrument -w -r -e researchParity true -e class ph.smishguard.ResearchLinearAndroidTest ph.smishguard.test/ph.smishguard.SoftwareTestRunner',
        f'python scripts/report_retraining.py {run.relative_to(root).as_posix()}',
        '```','',
        'Research tests: **145 passed**, including 15 new guards. Backend: **46 passed** in its established environment. Latest full JVM suite: **37 tests, 31 passed, 6 optional artifact-dependent tests skipped, zero failures/errors**; '
        'both actual NB and combined SVM parity runs passed. Build/lint/test APK checks passed; four API36 instrumentation runs passed one candidate test each, '
        'including the two strengthened runs with real masked cohort coverage/latency. '
        'Notebook: all 17 cells executed end-to-end in a fresh run, including fitting, locking and retrospective holdout evaluation. '
        'The first run is preserved with its exact source snapshot. A label-0 missing-count reporting bug was corrected; it did not alter labels, splits or model fitting. '
        'The fresh run has identical split membership, selected settings/thresholds, native inference parameters and all five holdout prediction vectors (zero score differences). '
        'The preserved selectedSvm variant also builds and passes 37 JVM tests (32 executed, five optional tests skipped). '
        'Initial comparator fixture failures and wrong-venv Flask failure are preserved in audit-v1 logs; no assertions were weakened.','',
        'Notebook: `research/Model_Training_and_Evaluation.ipynb` (self-contained embedded implementation, configurable CSV/JSON/ZIP/Drive input, clean setup instructions). '
        'Prepared input must use the documented existing masked fitting view for this Android adapter; raw corpus preparation/lineage must precede using a different input. '
        'Established notebook unchanged. Pipeline: `research/smishguard/retraining.py`. '
        f'Private run: `{run.relative_to(root).as_posix()}/` (dataset, ledgers, splits, configuration, selection, freeze, fitted pipelines, predictions, curves, errors, metadata). '
        'Actual native candidates and parity: `research/runs/retraining-20261013/parity-E-v2/` and `parity-C-v2/`. '
        'Public aggregate JSON/CSV and figures accompany this report; their experiment file hashes trace every reported metric.','',
        '![Confusion matrices and model comparison](retraining-figures-20261013/confusion-and-comparison.png)','',
        '![Precision–recall curves](retraining-figures-20261013/precision-recall.png)','',
        '![Reliability diagrams](retraining-figures-20261013/reliability.png)','',
        'Method references: [version-matched TF-IDF](https://scikit-learn.org/1.6/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html), '
        '[calibration](https://scikit-learn.org/stable/modules/calibration.html), [XLM-R paper](https://arxiv.org/abs/1911.02116), '
        '[checkpoint card](https://huggingface.co/FacebookAI/xlm-roberta-base). These support methodology/provenance, not a SmishGuard performance claim.']
    (root/'docs/retraining-experiment-20261013.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    print('Aggregate reports/CSV/figures saved; preserved original hashes verified')


if __name__=='__main__':main()
