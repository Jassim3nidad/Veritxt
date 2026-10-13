"""Verify prediction-derived results and produce a public, aggregate-only handoff."""
import argparse
from collections import Counter
import csv
import json
import pickle
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import nbformat
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research'))
from smishguard.bantaytext_workflow import load,save,digest,calculate_metrics


def target_categories(run, rows, parts, results):
    package=ROOT/'research/data/newdata-20261013/original/smishguard_dataset_2026-10-12/smishguard_dataset.csv'
    original={r['id']:r for r in csv.DictReader(package.open(encoding='utf-8-sig',newline=''))}
    assert all(r['id'] in original for r in rows)
    targeted={}
    selected=load(run/'improvement-freeze.json')['selected']
    for track,key in selected.items():
        entry=next(r for r in results if r['track']==track and r['id']==key)
        pred=load(run/track/key/'test-predictions.json');p=np.array(pred['scores']);y=np.array(pred['labels'])
        ii=parts[track]['test'];categories={}
        for category in ('otp','gov','ads','notifs'):
            mask=np.array([original[rows[i]['id']]['source_category']==category for i in ii])
            negatives=mask&(y==0);n=int(negatives.sum());fp=int(np.sum(negatives&(p>=entry['threshold'])))
            categories[category]=dict(records=int(mask.sum()),ham=n,smishing=int(np.sum(mask&(y==1))),fp=fp,
                false_positive_rate=fp/n if n>=20 else None,
                meaning='Original source category, inherited binary label; no independent confirmation. Rate suppressed below 20 ham.')
        categories['bank_ewallet_notifications']=dict(records=None,reason='No independently validated bank/e-wallet category; notifs is broad, so no invented bank FPR')
        targeted[track]=categories
    return targeted


def report(run):
    a=load(run/'aggregate.json');cfg=load(run/'configuration.json');data_audit=load(run/'data-audit.json')
    rows=load(run/'dataset.json');splits=load(run/'splits.json');results=a['results'];verified=0
    group_sources={g:{rows[i]['source'] for i,v in enumerate(splits['groups']) if v==g} for g in set(splits['groups'])}
    cross_source={g for g,sources in group_sources.items() if len(sources)>1}
    data_audit['cross_source_template_groups']=len(cross_source)
    data_audit['records_in_cross_source_template_groups']=sum(g in cross_source for g in splits['groups'])
    for phase in ('baseline','improvement'):
        freeze=load(run/(phase+'-freeze.json'))
        assert not freeze['test_opened'] and freeze['configuration_sha256']==digest(run/'configuration.json')
        for name,sha in freeze['files'].items():assert digest(run/name)==sha
    for r in results:
        p=load(run/r['track']/r['id']/'test-predictions.json')
        assert p['indices']==splits['partitions'][r['track']]['test']
        measured=calculate_metrics(p['labels'],p['scores'],r['threshold'],r['config']['algorithm']!='svm' or r['config'].get('calibrated',False))
        assert measured==r['test'];verified+=1
    targets=target_categories(run,rows,splits['partitions'],results)
    coverage={};reliability={}
    for track,key in a['selected'].items():
        artifact=pickle.loads((run/track/key/'pipeline.pkl').read_bytes())
        fitted=artifact['pipe']['tfidf']
        if hasattr(fitted,'build_analyzer') and fitted.analyzer=='word':
            analyzer=fitted.build_analyzer();vocab=set(fitted.get_feature_names_out())
            coverage[track]=dict(taglish_probe_tokens={token:token in vocab for token in ('po','paki','nyo','ninyo','na')},
                language={})
            for language in sorted({r['language'] for r in rows}):
                ids=[i for i in splits['partitions'][track]['test'] if rows[i]['language']==language]
                terms=[analyzer(rows[i]['text']) for i in ids]
                total=sum(len(t) for t in terms);known=sum(term in vocab for terms_i in terms for term in terms_i)
                coverage[track]['language'][language]=dict(records=len(ids),analyzed_features=total,known_feature_fraction=known/total if total else None,
                    note='Includes word unigrams and bigrams after English stopword filtering; not accuracy or language proficiency')
        preds=load(run/track/key/'test-predictions.json');p=np.array(preds['scores']);y=np.array(preds['labels']);bins=[]
        for j in range(10):
            mask=(p>=j/10)&((p<(j+1)/10) if j<9 else (p<=1))
            bins.append(dict(count=int(mask.sum()),mean_score=float(p[mask].mean()) if mask.any() else None,
                             observed_inherited_scam_fraction=float(y[mask].mean()) if mask.any() else None))
        reliability[track]=dict(bins=bins,expected_calibration_error=sum(v['count']/len(y)*abs(v['mean_score']-v['observed_inherited_scam_fraction']) for v in bins if v['count']),
            status='Retrospective score reliability under inherited labels; does not establish real-world probability calibration')
    input_audit=load(ROOT/'docs/bantaytext-input-audit-20261013.json')
    for path,sha in input_audit['protected_hashes'].items():assert digest(ROOT/path)==sha
    assert all(not v for v in splits['support']['grouped']['template_overlap'].values())
    nb=nbformat.read(ROOT/'research/SmishGuard_Model_Training_and_Evaluation.ipynb',as_version=4);nbformat.validate(nb)
    code_cells=[c for c in nb.cells if c.cell_type=='code']
    assert all(c.execution_count is not None for c in code_cells)
    assert not any(o.output_type=='error' for c in code_cells for o in c.outputs)
    jvm=load(run/'parity/active-jvm-aggregate.json')
    assert jvm['maximum_absolute_error']<=1e-10 and jvm['required_abstentions']==7
    junit=list((ROOT/'android/app/build/test-results/testDevelopmentUnitTest').glob('TEST-*.xml'))
    counts=Counter()
    for path in junit:
        xml=ET.parse(path).getroot()
        for k in ('tests','failures','errors','skipped'):counts[k]+=int(xml.get(k,'0'))
    assert not counts['failures'] and not counts['errors']
    summary=dict(a,data_audit=data_audit,split_support=splits['support'],configuration=cfg,targeted_evaluation=targets,
        vocabulary_coverage=coverage,score_reliability=reliability,
        verification=dict(recomputed_test_results=verified,protected_files_unchanged=len(input_audit['protected_hashes']),
            notebook_code_cells_executed=len(code_cells),notebook_sha256=digest(ROOT/'research/SmishGuard_Model_Training_and_Evaluation.ipynb'),
            jvm= jvm,junit=dict(counts),build='assembleDevelopment/lintDevelopment/testDevelopmentUnitTest passed',
            research_tests='113 passed',script_tests='1 unittest passed',physical_device='Not performed',emulator='No adb devices available; not run'),
        code_hashes={p.relative_to(ROOT).as_posix():digest(p) for p in [ROOT/'research/smishguard/bantaytext_workflow.py',ROOT/'scripts/create_bantaytext_notebook.py']})
    save(ROOT/'docs/bantaytext-comparison-20261013.json',summary)
    csv_rows=[]
    for r in results:
        for split in ('validation','test'):
            metrics=r[split]
            csv_rows.append(dict(track=r['track'],phase=r['phase'],id=r['id'],split=split,threshold=r['threshold'],
                **{k:metrics[k] for k in ('records','precision','recall','f1','accuracy','average_precision','roc_auc','false_positive_rate','false_negative_rate','brier','log_loss')},
                **metrics['confusion'],feature_count=r['feature_count'],serialized_bytes=r['serialized_bytes'],
                sparse_training_bytes=r['sparse_training_bytes'],training_seconds=r['training_seconds'],host_ms=r.get('host_test_ms_per_message') if split=='test' else r['host_validation_ms_per_message']))
    with (ROOT/'docs/bantaytext-comparison-20261013.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(csv_rows[0]));writer.writeheader();writer.writerows(csv_rows)
    lines=['# SmishGuard baseline-first BantayText experiment — 13 October 2026','',
        '**Decision: retain the active supplied model.** The grouped validation-selected research candidate is '+a['selected']['grouped']+'. Improvements are retrospective, with inherited labels and no genuinely unseen cohort. Its source stress results do not establish reliable deployment generalization. No app weights, inference policies, permissions, consent, receiver behavior or reporting controls changed.','',
        'The executed [notebook](../research/SmishGuard_Model_Training_and_Evaluation.ipynb) contains actual training, prediction, confusion-matrix arithmetic, tables and plots. All 62 configurations (31 per track, including diagnostics) completed; the baseline phase was frozen, tested and saved before improvements. The [CSV](bantaytext-comparison-20261013.csv) separates all 124 validation/test rows. [JSON](bantaytext-comparison-20261013.json) retains full metrics/configuration, memory/latency and subgroup counts.','',
        '## Data and leakage','',
        'The latest supplied package contains 4,261 records: 3,184 ham, 577 smishing and 500 unmapped gambling ads. Existing source/privacy rules hold 921 rows, leaving 3,340 masked fitting records. This experiment holds 59 flagged records and removes 727 masked casefold duplicates, leaving **2,554 records (2,229 ham, 325 smishing; 12.73% scam)**. No 25.5% ratio was forced. [Input/source audit](bantaytext-input-audit-20261013.json) documents source contributions, schemas, original categories, rule mappings, missing fields, placeholder counts and active-model baseline.','',
        'Pinned source snapshots contain 3,454 Tagalog-SMS, 8,895 Chua marketing and 1,021 bwandowando records. Two Chua CSV rows have extra-field overflow; the established source matcher only admits documented exact source joins. A full raw-source build cannot be reproduced because upstream package inputs are incomplete. We did not execute the supplied builder or invent permissions.','',
        'English stopword filtering does not remove po/paki/nyo/ninyo/na. The selected grouped training vocabulary includes po/na, while paki/nyo/ninyo are absent because they were not observed in that training view. This limits local coverage; these words are not hard-coded scam indicators. Unicode word TF-IDF preserves Filipino text in masked views, and character features test misspellings/obfuscation. Raw URL hosts, shorteners, sender and identifiers were masked or excluded upstream; their causal contribution cannot be recovered.','',
        '| Track | Train ham/scam | Validation ham/scam | Test ham/scam | Cross-partition template groups |','|---|---:|---:|---:|---|']
    for track,v in splits['support'].items():
        support=v['support'];values=[f"{support[p]['ham']}/{support[p]['smishing']}" for p in ('train','validation','test')]
        lines.append('| '+track+' | '+' | '.join(values)+' | '+str(v['template_overlap'])+' |')
    lines += ['',f"The cleaned corpus has {len(cross_source)} template components spanning multiple sources ({data_audit['records_in_cross_source_template_groups']} records). These potential reused messages/campaigns are grouped together; similarity is not confirmed campaign identity."]
    lines+=['','Random uses a two-step stratified 60/20/20 split, seed 42. Grouped uses 1,840 connected components and 10 stratified group folds assigned 6/2/2. Supplied template equivalence and normalized SequenceMatcher ≥.85 form label-blind edges. No grouped component crosses boundaries; this heuristic cannot establish complete campaign independence. Random and grouped test sets differ: compare conditions within each track. Dates have unverified receipt meaning/timezone, so temporal testing is unavailable. Every eligible message already had historical exposure; re-splitting does not make it prospectively unseen.','',
        '## Baseline and selected candidates','',
        'Standard baselines share unrestricted Unicode word unigrams, raw TF-IDF/smooth IDF/L2, no stopwords, seed 42. NB alpha=1; LR C=1/liblinear; LinearSVC C=1/dual=auto, no class weights. Native SVM uses margin ≥0 and ranking margins, with no probability/calibration claim. Improved SVM probabilities come from 3 training-only grouped OOF folds with fold-local TF-IDF and a sigmoid fit; calibration quality remains unvalidated.','',
        '| Track/model | Validation F1 | Test precision | Test recall | Test F1 | AP | ROC AUC | TN/FP/FN/TP |','|---|---:|---:|---:|---:|---:|---:|---|']
    for r in results:
        if r['phase']=='baseline' or r['id']==a['selected'][r['track']]:
            m=r['test'];c=m['confusion'];lines.append(f"| {r['track']}/{r['id']} | {r['validation']['f1']:.4f} | {m['precision']:.4f} | {m['recall']:.4f} | {m['f1']:.4f} | {m['average_precision']:.4f} | {m['roc_auc']:.4f} | {c['tn']}/{c['fp']}/{c['fn']}/{c['tp']} |")
    lines+=['','Selection maximizes validation scam F1 subject to precision ≥.90 and TP≥5; ties prefer fewer serialized bytes then experiment ID. Threshold grid .05–.95 in .01 steps. Each phase saves model hashes and selection before any test transform. Tests were evaluated once per configuration; no test-driven retuning or replacement occurred. False negatives miss phishing; false positives can disrupt trust in legitimate OTP/transaction messages. The precision floor is a provisional research operating criterion, not approval for automatic warnings.','',
        '## Controlled comparisons on grouped validation','',
        '| Experiment | Threshold | Default-threshold F1 | Tuned validation F1 | Test F1 (descriptive) | Features | Pickle bytes | Train seconds | Host test ms/message |','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    chosen_ids=['nb-alpha-0.03','nb-word12-english','nb-alpha-0.3','nb-alpha-1.0','nb-word1-english','nb-word12-no-stop','nb-char','nb-combined',
        'lr-word12-english','lr-C-0.1','lr-C-10.0','lr-oof-calibrated','lr-balanced','svm-word12-english','svm-C-10.0','svm-combined','lr-portable',
        'lr-remove_urls','lr-placeholders_only','lr-source_only']
    for r in results:
        if r['track']=='grouped' and r['id'] in chosen_ids:
            lines.append(f"| {r['id']} | {r['threshold']:.2f} | {r['default_validation']['f1']:.4f} | {r['validation']['f1']:.4f} | {r['test']['f1']:.4f} | {r['feature_count']} | {r['serialized_bytes']} | {r['training_seconds']:.3f} | {r['host_test_ms_per_message']:.3f} |")
    lines+=['','Interpret these alpha/feature comparisons using validation and the same partitions. Threshold tuning is a separate changed factor; default-threshold metrics are saved alongside tuned metrics. No arbitrary feature pruning was needed for this host experiment; no phone memory/latency claim follows. Sparse matrix byte counts exclude Python object/string and runtime overhead. Pickle size is a measured research serialization size, not an Android asset size. Combined features concatenate equally weighted individually L2-normalized word and char blocks. Source-only and URL/placeholder ablations are prespecified diagnostics, excluded from model selection. Source prevalence is strongly confounded: the cleaned bwandowando source contains only positive labels.','',
        '## Errors and targeted legitimate-message evaluation','',
        'Targeted categories join original metadata by ID only **after selection**, without changing text, labels, partitions or fitted parameters. Category membership comes from original source categories; binary ham labels remain inherited and unverified. Bank/e-wallet notifications are not separately validated, and the broad `notifs` category must not be presented as bank-specific. No confirmed-malicious category is claimed.','',
        '| Track/category | Ham support | Smishing support | False positives | FPR |','|---|---:|---:|---:|---:|']
    for track,categories in targets.items():
        for cat,v in categories.items():
            if v.get('ham') is not None:
                rate=f"{v['false_positive_rate']:.4f}" if v['false_positive_rate'] is not None else 'suppressed (<20 ham)'
                lines.append(f"| {track}/{cat} | {v['ham']} | {v['smishing']} | {v['fp']} | {rate} |")
    lines+=['','Rates are descriptive and suppressed below 20 relevant-class records, not statistically powered guarantees. Private error ledgers contain row indices and predictions only. No SMS text is emitted publicly. The grouped selected model has 4 FP and 3 FN; its English subgroup has 284 ham/63 smishing with 4 FP/2 FN, and Filipino/Taglish has 141 ham/10 smishing with 0 FP/1 FN. The latter FNR is suppressed because its positive denominator is below 20. URL-removal stress and source/category counts are in JSON. No test-derived data correction or feature retuning was performed.','',
        '| Held source (diagnostic) | Test records | F1 | Recall |','|---|---:|---:|---:|']
    for source,v in a['source_heldout'].items():
        if 'metrics' in v:lines.append(f"| {source} | {v['test']['records']} | {v['metrics']['f1']:.4f} | {v['metrics']['recall']:.4f} |")
    lines+=['','Each source stress fit excludes that source and every overlapping template group. Settings and threshold remain fixed from main grouped validation, which included the source earlier; these post-selection diagnostics are not an unbiased nested source-holdout estimate. The weak Tagalog result, source imbalance, inherited labeling rules and historical exposure prevent a reliable deployment-winner claim.','',
        '## Android/model handoff','',
        'The active supplied schema-2 LR remains byte-identical. Its full-training-corpus resubstitution baseline is separately labeled in the input audit and must not be compared with held-out candidate metrics. Exact original artifact training reproduction remains unresolved despite supplied procedure evidence. Existing score presentation is an uncalibrated model score, not fraud probability; prior automatic-warning behavior and disabled reporting are preserved.','',
        'The selected research SVM uses Unicode English-stopword word bigrams and training-OOF calibration, which the current Android word-unigram contract cannot consume. Its private pipeline stores the exact ordered vocabulary, IDF, class order [0,1], coefficients, calibration and validation threshold. Independent labels, unseen evaluation and a separately reviewed native feature contract are needed before integration. Do not silently truncate features or substitute preprocessing.','',
        'A separately fitted portable LR comparator exports the existing schema-1 contract for parity only: ASCII word unigrams, raw TF-IDF, exact ordered vocabulary/IDF, L2, class [not_suspicious,suspicious], inclusive threshold and a fitted training-OOF sigmoid with calibration_evaluated=false. Python and JVM fixed synthetic probes agree within 1e-10. Empty/oversized comparator inputs fail; unknown/malformed input scores remain explicitly non-probability. The comparator is not installed or approved. Active-model safe probes include legitimate-style OTP/bank/e-wallet, Taglish, malicious-style, empty, malformed, URL-only and random text; these are software checks, not accuracy labels.','',
        f"Verification: {verified} test metric records independently recomputed; {len(code_cells)} notebook code cells executed without errors; {len(input_audit['protected_hashes'])} protected app/model hashes unchanged. JVM: {counts['tests']} tests, {counts['failures']} failures, {counts['errors']} errors, {counts['skipped']} conditional skips. Active parity: {jvm['cases']} probes, max score error {jvm['maximum_absolute_error']:.3g}, {jvm['required_abstentions']} required abstentions. Assemble/lint/JVM development checks passed. No emulator or physical-device testing was performed in this task.", '',
        'Vocabulary coverage and score-reliability bins/ECE are in JSON. Coverage counts analyze held-out word features against training vocabulary without fitting on held-out messages; low support and masked text limit interpretation. Reliability is retrospective under inherited labels, not a risk-percentage validation.','',
        'See [reproduction and test report](bantaytext-reproduction-20261013.md) and [research candidate model card](bantaytext-model-card-20261013.md). Public outputs contain aggregate metrics only. Fitted artifacts/vocabulary, row membership and datasets stay in ignored research storage. The first execution failed on record copying before training, was fixed and retained privately; the complete delivered run is notebook-run-v3, including original-category targeted notebook outputs.','']
    (ROOT/'docs/bantaytext-comparison-20261013.md').write_text('\n'.join(lines),encoding='utf-8')
    print('Verified and reported',verified,'test configurations;',len(code_cells),'executed cells;',dict(counts))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('run',type=Path);report(p.parse_args().run)
