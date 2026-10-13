"""Aggregate-only report for the audited supplied-update reproduction."""
import argparse
from collections import Counter
import csv
from pathlib import Path
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research'))
from smishguard import ensemble_compare as experiment
from smishguard import fair_compare as fair
from smishguard.train import write_json
from report_ensemble_comparison import clustered_uncertainty, display


def fpr(result):
    c=result['confusion']
    return c['fp']/(c['tn']+c['fp'])


def report(run,destination):
    cfg,rows,m=experiment.context(run)
    selection=experiment.load(run/'selection.json')
    final=experiment.load(run/'test-results.json')
    val=experiment.load(run/'validation-results.json')
    test=final['results']
    pred=experiment.load(run/'test-predictions.json')
    audit=experiment.load(run/'audit.json')
    package=audit['new_package']
    exclusions=experiment.load(run/'excluded-overlap-summary.json')
    ids=m['partitions']['test']
    groups=np.array(m['groups'])[ids]
    y=np.array(pred['labels'])
    if pred['ids'] != [rows[i]['id'] for i in ids]:
        raise ValueError('Test predictions have different reserved IDs')
    for split,results in [('test',test),('validation',val)]:
        saved=experiment.load(run/(split+'-predictions.json'))
        if saved['ids'] != [rows[i]['id'] for i in m['partitions'][split]]:
            raise ValueError('Finalized prediction order mismatch')
        for key,r in results.items():
            entry=selection['entries'][key]
            pp=saved['predictions'][key]
            recalculated=experiment.measure(saved['labels'],pp['scores'],entry['threshold'],entry['family']!='standalone')
            for metric in ('accuracy','precision','recall','f1','macro_f1','confusion'):
                if r[metric] != recalculated[metric]:
                    raise ValueError('Saved metric does not reproduce from finalized scores')
            c=r['confusion']
            if sum(c.values())!=len(saved['ids']):
                raise ValueError('Confusion matrix coverage mismatch')
            r['false_positive_rate']=fpr(r)
    intervals,distributions=clustered_uncertainty(y,pred['predictions'],groups)
    base=selection['selected_by_family']['standalone']
    paired={}
    for family,key in selection['selected_by_family'].items():
        if key:
            delta=distributions[key]-distributions[base]
            paired[family]=dict(candidate=key,reference=base,observed_f1_difference=test[key]['f1']-test[base]['f1'],
                low=float(np.quantile(delta,.025)),high=float(np.quantile(delta,.975)))
    lrdelta=distributions['standalone_lr']-distributions['standalone_svm']
    reuse=experiment.load(run/'mbert-oof-reuse.json') if (run/'mbert-oof-reuse.json').exists() else None
    errors={}
    for key in test:
        pp=np.array(pred['predictions'][key]['predictions'])
        mask=(pp!=y)
        errors[key]=dict(error_records=int(mask.sum()),error_groups=len(set(groups[mask])),
            false_negative_by_source=dict(Counter(rows[i]['source'] for j,i in enumerate(ids) if y[j]==1 and pp[j]==0)),
            false_negative_by_category=dict(Counter(rows[i]['category'] for j,i in enumerate(ids) if y[j]==1 and pp[j]==0)),
            false_positive_by_source=dict(Counter(rows[i]['source'] for j,i in enumerate(ids) if y[j]==0 and pp[j]==1)))
    lp=np.array(pred['predictions']['standalone_lr']['predictions'])
    sp=np.array(pred['predictions']['standalone_svm']['predictions'])
    lrsvm_vote_same=bool(np.array_equal(sp,pred['predictions']['voting_lr_svm']['predictions']))
    lrsvm=dict(svm_catches_lr_misses=int(((y==1)&(lp==0)&(sp==1)).sum()),
        lr_catches_svm_misses=int(((y==1)&(lp==1)&(sp==0)).sum()),
        different_decisions=int((lp!=sp).sum()))
    # Historical metrics are read only after the new configuration freeze/test.
    previous=experiment.load(ROOT/'docs/ensemble-comparison-20261011.json')['test']
    identical={key:all(test[key][metric]==previous[key][metric] for metric in ('accuracy','precision','recall','f1','macro_f1','confusion'))
               for key in test if key in previous}
    aggregate=dict(primary_metric='smishing-class F1',status=package['status'],new_package=package,excluded_overlap=exclusions,
        preparation=audit['partitions'],exposure=audit['exposure'],reserved_test_prior_exact_overlap=audit['current_reserved_test_prior_exact_overlap'],
        configuration={k:cfg[k] for k in ('baseline_parameters','baseline_thresholds','mbert_threshold','baseline_seed','mbert_seed','meta','versions')},
        dataset_sha256=cfg['dataset_sha256'],split_sha256=cfg['split_sha256'],protocol_sha256=cfg['protocol_sha256'],
        freeze_sha256=final['freeze_sha256'],entries=selection['entries'],validation=val,test=test,
        validation_ranking=selection['ranking'],descriptive_test_ranking=final['descriptive_test_ranking'],
        selected_by_validation=selection['selected'],selected_by_family=selection['selected_by_family'],
        confidence_intervals=intervals,paired_selected_vs_selected_standalone=paired,
        paired_lr_minus_svm=dict(observed=test['standalone_lr']['f1']-test['standalone_svm']['f1'],
            low=float(np.quantile(lrdelta,.025)),high=float(np.quantile(lrdelta,.975))),
        bootstrap=dict(repetitions=2000,seed=fair.SEED,unit='template group',scope='Conditional fixed-model marginal intervals; no fitting/label uncertainty or simultaneous correction'),
        posthoc_errors=errors,lr_vs_svm_errors=lrsvm,lr_svm_voting_decisions_identical_to_svm=lrsvm_vote_same,previous_metrics_reproduced=identical,
        mbert_oof_reuse=None if reuse is None else {k:v for k,v in reuse.items() if k not in {'source','files'}},
        failures=experiment.load(run/'failures.json') if (run/'failures.json').exists() else [],
        verification=experiment.load(run/'oof-artifact-audit.json'),
        final_integrity=experiment.load(run/'final-integrity-verification.json') if (run/'final-integrity-verification.json').exists() else None,
        attempt_history=experiment.load(run/'attempt-history.json') if (run/'attempt-history.json').exists() else [],
        cache_source_equivalence=experiment.load(run/'cache-source-equivalence.json') if (run/'cache-source-equivalence.json').exists() else None,
        diagnostics=experiment.load(run/'validation-diagnostics.json'),
        timing='Current standalone/classical/meta timings; cached mBERT OOF costs are measured historical costs, not new computation. CPU sequential-batch inference includes input transformation, excludes model loading.',
        supplemental_audits={name:experiment.load(run/name) for name in ('classical-reproduction-audit.json','mbert-reproduction-audit.json') if (run/name).exists()})
    write_json(destination.with_suffix('.json'),aggregate)
    fields=['partition','family','model','validation_rank','test_rank','accuracy','precision','recall','f1','macro_f1','false_positive_rate',
        'tn','fp','fn','tp','training_seconds','inference_seconds','inference_ms_per_record']
    vr={k:i+1 for i,k in enumerate(selection['ranking'])}
    tr={k:i+1 for i,k in enumerate(final['descriptive_test_ranking'])}
    with destination.with_suffix('.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields)
        writer.writeheader()
        for split,results in [('validation',val),('test',test)]:
            for key in selection['ranking']:
                r=results[key]
                writer.writerow(dict(partition=split,family=selection['entries'][key]['family'],model=display(key),validation_rank=vr[key],test_rank=tr[key],
                    **{k:r[k] for k in ('accuracy','precision','recall','f1','macro_f1','false_positive_rate','training_seconds','inference_seconds','inference_ms_per_record')},**r['confusion']))
    leaders=[k for k in final['descriptive_test_ranking'] if test[k]['f1']==max(r['f1'] for r in test.values())]
    lines=['# SmishGuard supplied-update audit and fixed-setting comparison','',
        f"The configuration selected on validation was **{display(selection['selected'])}** ({selection['entries'][selection['selected']]['family']}, F1 {val[selection['selected']]['f1']:.4f}). "
        f"The descriptive test leader(s) were **{', '.join(display(k) for k in leaders)}**, F1 {test[leaders[0]]['f1']:.4f}. No model was changed or reselected after test evaluation.",'',
        '**This is retrospective reproduction, not evidence of performance on newly admitted data.** The 12 October package contains 4,261 rows, but its eligible binary fitting corpus remains exactly the previous 3,340 ordered records (2,947 ham, 393 smishing). '
        'The rebuilt template groups, four partitions and five training folds also exactly match the earlier experiment. All 448 reserved test messages have exact historical exposure. '
        'They are held out of current fitting, calibration and selection, but cannot be described as untouched or prospective.','',
        '## Data audit and confirmed limitations','',
        '- Original ZIP and all eight members are preserved privately. Supplied scripts were inspected and never executed. Strict UTF-8 parsing, schema/identity checks, source joins, label orientation, grouping and history checks preceded fitting. '
        'Smishing maps to 1 and ham to 0; source spam labels are not directly mapped to smishing.',
        '- Supplied labels: 577 smishing, 3,184 ham, 500 gambling_ad. The third label is preserved and held; there is no authorized binary mapping. Advertising is not silently converted to either class.',
        '- The remaining holds are 263 GitHub rows (including 203 A.S.E.A. rows with explicitly pending permission), 19 team rows with unresolved origin/use evidence, and 139 existing automated privacy holds. '
        'This retains the established experiment source/privacy policy. The 709 additions (203 ASEA, 6 screenshots, 500 ads) contribute zero newly eligible binary records.',
        '- Earlier message texts, labels, IDs and order are unchanged. Eight date metadata fields changed; dates are not model inputs. The auxiliary ASEA CSV duplicates its 203 final-dataset rows and is not appended a second time. '
        'The 500 ads were moved from the old excluded corpus; they are not 500 newly collected independent messages.',
        '- README contains stale earlier-version counts and a binary column description despite three labels. Source categories and heuristic confidence do not establish truth. '
        'The updated review workbook contains 118 flagged records and a 300-row sample, with zero filled labeler/final-label cells; empty review cells are not approvals.',
        f"- Exact cleaned duplicates: {package['duplicate_exact_text']}; normalized conflicting-label groups: {package['normalized_conflict_groups']}; supplied template-key mismatches: {package['supplied_template_key_mismatches']}; "
        f"full-package near-template groups: {package['computed_template_groups']}. Near groups with differing labels are documented, not automatically relabeled.",
        f"- Historical inventory: {audit['exposure']['historical_files']} available corpora, {audit['exposure']['historical_unique_normalized_texts']} distinct normalized messages. "
        f"Among all 4,261 supplied rows, {audit['exposure']['exact']} have exact and {audit['exposure']['near_only']} have additional near-only overlap; {audit['exposure']['no_detected_overlap']} have no detected overlap. "
        'Files with unknown fitting membership are recorded as possible prior corpus exposure. No detected match does not establish independent unseen data.',
        '- Missing fields, per-source labels, label-method/confidence counts, historical label disagreements, workbook review counts and file hashes are retained in the JSON audit. '
        'Original labels are preserved even when they disagree with earlier labels. Independent labels/privacy reviews remain pending.',
        f"- Included/excluded overlap: no exact cleaned text overlap, but {exclusions['normalized_exact_overlap_records']} excluded messages collide after preprocessing, "
        f"{exclusions['same_template_overlap_records']} share a template, and {exclusions['direct_near_overlap_records']} have a direct near witness in the included corpus. "
        f"Near witnesses occur against {exclusions['direct_near_by_included_label']['smishing']} smishing, {exclusions['direct_near_by_included_label']['ham']} ham and "
        f"{exclusions['direct_near_by_included_label']['gambling_ad']} gambling-ad records (counts can overlap). These are scope/representation ambiguities, not automatic label errors; all excluded records remain excluded.",
        '- No current training, labeling-conversion or probability-order bug was confirmed. Historical supplied pre-vectorized CV was already corrected by the established fold-local TF-IDF pipeline; no new bug fix was applied.','',
        '## Fixed settings and fitting evidence','',
        'Freshly refitted standalone LR, NB, SVM and mBERT use the previous settings and training budgets. LR C=10/liblinear, NB alpha=.1, SVM C=10/dual=auto; unigram TF-IDF and seed 20260929. '
        'Baseline calibration uses only the reserved calibration partition. Saved thresholds remain LR .82, NB .63, SVM .59 and mBERT '+repr(cfg['mbert_threshold'])+'. No hyperparameter, threshold or weight search ran.','',
        'mBERT uses the pinned multilingual cased base/tokenizer, seed 20261005, two epochs, Adafactor 2e-5, weight decay .01, microbatch 1, accumulation 8, deterministic CUDA float16, training-only p95 length and a 2700-second fit budget. '
        'Standalone checkpoint selection uses validation AP. Stacking bases use fixed epoch 2, their own training-only length rule and no outer-validation checkpoint selection.','',
        ('Five mBERT OOF fits were reused after verifying identical ordered fitting views, labels, groups/folds, settings, fitting code after universal-newline decoding, dependency versions and frozen artifact hashes. '
         'They are saved in the new directory with explicit reuse provenance. Their original successful OOF training costs are included when assessing the cost to build a stack; these are not newly performed training seconds.' if reuse else
         'mBERT OOF fitting status and any failures are recorded in the machine-readable report.'),'',
        'Eleven voting combinations use equal-weight soft voting on correctly ordered valid probabilities. LR/NB probabilities are native; mBERT predictions come from its independently fitted model; '
        'SVM has a distinct sigmoid fitted only on training-fold OOF margins. Every vocabulary/IDF is fitted inside its own fold. Threshold .5, equality to ham. NB receives nonnegative TF-IDF.','',
        'The two LR meta-classifiers are separate from standalone LR. They fit only training OOF matrices: (LR,SVM,NB)→LR and (mBERT,SVM,NB)→LR. '
        'SVM OOF calibration uses five nested grouped folds per outer fold. Meta C=1/lbfgs/max_iter=2000/seed=20260929; threshold .5, equality to ham. '
        'Both OOF matrices and actual fold pipelines/checkpoints are saved. Selection uses validation smishing F1; ties use lexicographic experiment ID. '
        'Fixed historical hyperparameters are prespecified inputs to this run; OOF predictions do not undo their historical selection on this same training corpus or constitute an unbiased assessment of that earlier selection.','']
    for family in ('standalone','voting','stacking'):
        lines += ['## '+family.title(),'',
            'Ranks are global across finalized configurations. Metrics are percentages; confusion order is TN / FP / FN / TP.','']
        for split,results in [('Validation',val),('Reserved retrospective test',test)]:
            lines += ['### '+split,'',
                '| Model | Val rank | Test rank | Accuracy | Precision | Recall | F1 | Macro-F1 | FPR | TN / FP / FN / TP | Required train s | CPU infer s | ms/record |',
                '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|']
            for key in selection['ranking']:
                if selection['entries'][key]['family'] != family or key not in results:
                    continue
                r=results[key]
                c=r['confusion']
                nums=' | '.join(f"{100*r[n]:.2f}" for n in ('accuracy','precision','recall','f1','macro_f1','false_positive_rate'))
                confusion=' / '.join(str(c[n]) for n in ('tn','fp','fn','tp'))
                lines.append(f"| {display(key)} | {vr[key]} | {tr[key]} | {nums} | {confusion} | {r['training_seconds']:.3f} | {r['inference_seconds']:.4f} | {r['inference_ms_per_record']:.4f} |")
            lines += ['']
        unavailable=[display(k)+': '+e.get('reason','unavailable') for k,e in selection['entries'].items() if e['family']==family and e['status']!='ready']
        lines += unavailable or ['All requested configurations in this family completed.']
        lines += ['']
    lr=test['standalone_lr'];svm=test['standalone_svm']
    lines += ['## LR and error patterns','',
        f"Standalone LR test F1 is {lr['f1']:.4f}, recall {lr['recall']:.4f}, with {lr['confusion']['fn']} false negatives and {lr['confusion']['fp']} false positives. "
        f"Standalone SVM has {svm['confusion']['fn']} false negatives and {svm['confusion']['fp']} false positives. SVM catches {lrsvm['svm_catches_lr_misses']} smishing messages missed by LR; "
        f"LR catches {lrsvm['lr_catches_svm_misses']} missed by SVM. LR errors span {errors['standalone_lr']['error_groups']} template groups. "
        'This describes poor recall at its fixed operating point, without establishing a software defect or requiring LR to win.','',
        'LR false-negative source counts: '+str(errors['standalone_lr']['false_negative_by_source'])+'. '
        'Its false-negative category counts: '+str(errors['standalone_lr']['false_negative_by_category'])+'. '
        'These are post-evaluation descriptive counts under unconfirmed inherited labels, not causal explanations or independently validated subgroup estimates.','',
        'Validation-only native/calibrated LR diagnostics at the preserved threshold and fixed .5 are saved in JSON. They did not change its eligible threshold or configuration. '
        'Standalone LR performance is distinct from using LR to combine OOF component predictions.','',
        '## Ensemble complexity and paired uncertainty','',
        '| Family | Validation-selected entry | Test F1 difference vs selected standalone | Paired 95% group interval |','|---|---|---:|---|']
    for family,r in paired.items():
        lines.append(f"| {family} | {display(r['candidate'])} | {100*r['observed_f1_difference']:+.2f} pp | [{100*r['low']:+.2f}, {100*r['high']:+.2f}] pp |")
    lines += ['']
    for family in ('voting','stacking'):
        k=selection['selected_by_family'][family]
        if k:
            gain=test[k]['f1']-test[base]['f1']
            lines.append(f"The validation-selected {family} changes test F1 by {100*gain:+.2f} percentage points versus {display(base)}. "
                f"Required training cost is {test[k]['training_seconds']:.3f}s versus {test[base]['training_seconds']:.3f}s; sequential CPU test inference is "
                f"{test[k]['inference_seconds']:.4f}s versus {test[base]['inference_seconds']:.4f}s. "+
                ('There is no observed test-F1 gain to justify its added components in this comparison.' if gain<=0 else
                 'The observed gain must be assessed against the paired interval and added components; this exposed test does not establish a prospective advantage.'))
            lines += ['']
    lines += ['Intervals use 2,000 paired draws of whole template groups, seed 20260929. Per-model intervals and the paired LR−SVM difference are in JSON. '
        'Intervals are conditional on fixed fitted models, with no fitting or label uncertainty and no simultaneous multiple-comparison correction. '
        'Training costs count shared components once per hypothetical configuration, so summing table rows double-counts shared work. '
        'Inference includes each input transformation and combination, excludes model loading, and uses four torch CPU threads. Cached component timings are summed for sequential execution. '
        'These single-run host times are descriptive, not phone benchmarks.','',
        ('LR + SVM voting makes exactly the same 448 test decisions as standalone SVM. Its tied test F1 adds no observed detection benefit while requiring another fitted component and training-only SVM calibration.' if lrsvm_vote_same else
         'LR + SVM voting and standalone SVM have different decisions; their tied aggregate F1 does not imply identical error patterns.'),'',
        '## Reproduction and preservation','',
        f"All {sum(identical.values())} of {len(identical)} comparable configurations reproduce the previous experiment's prediction-derived metrics exactly. "
        'The full supplied package changed, but the eligible fitting corpus and splits did not. This is a reproduction check, not a new-dataset improvement claim. '
        'Comparisons to the earlier 1,068-record dataset remain descriptive because that corpus differs.','',
        'Private artifacts: `research/data/newdata-20261013/experiment-v2/`. Original input archive/members, complete intake/hold ledger, full-package template groups, historical corpus inventory and exact/near ledgers, '
        'dataset/case snapshots, split IDs, fitted vectorizers/models/calibrators, OOF fold fits and matrices, tokenizers, configurations, code/dependency snapshots, frozen selection and finalized predictions remain private. '
        'The first audit attempt was interrupted before fitting to finalize the adapter and is preserved as `interrupted-audit-v1/`. '
        'Previous datasets, splits, fitted models and app assets were preserved; no deployment, push or external messaging occurred.','',
        'The initial cache gate compared raw saved LF source to the CRLF checkout and rejected reuse despite identical Python source. It triggered a fresh OOF fallback; that incomplete fold was stopped and preserved under `interrupted-attempts/`. '
        'Recovery verifies original raw source/artifact hashes, identical universal-newline source and ASTs, and the identical complete dependency lock including the original torch direct-wheel reference. '
        'The first recovery rejected that direct reference because it expected a version-pin line; this metadata parser was corrected before reuse. '
        'Neither fix changes fitting logic, settings, thresholds or predictions. No partial fallback result is used, and its unmeasured duration is excluded rather than invented. '
        'The cache-verification amendment and every attempt status were saved before selection. The reproduction driver performs this verification directly.','',
        ('Verification: '+str(experiment.load(run/'final-integrity-verification.json')['tests_passed'])+' research tests passed. '
         +str(experiment.load(run/'final-integrity-verification.json')['frozen_artifacts_verified'])+' frozen artifacts, '
         +str(experiment.load(run/'final-integrity-verification.json')['historical_data_model_and_app_asset_files_verified'])+' historical input/model/app-asset files and all eight original archive members passed final hash checks. '
         'Both ZIP copies match the supplied download. All 17 test confusion matrices cover the same 448 reserved records, and every saved metric was independently recomputed from finalized scores.'
         if (run/'final-integrity-verification.json').exists() else 'Final integrity evidence is saved separately when available.'),'',
        'Protocol: [frozen supplied-update procedure](new-dataset-comparison-protocol-20261013.md). '
        f"Aggregate [JSON]({destination.with_suffix('.json').name}) and [CSV]({destination.with_suffix('.csv').name}) contain full-precision results; CSV includes validation and test separately.",'',
        f"Dataset SHA-256: `{cfg['dataset_sha256']}`. Split SHA-256: `{cfg['split_sha256']}`.",'',
        '```powershell',"$env:PYTHONPATH='research'","$env:PYTHONIOENCODING='utf-8'","$python='research/data/mbert-20261002/venv/Scripts/python.exe'",
        "$run='research/data/newdata-20261013/NEW-RUN'",
        '& $python -m smishguard.new_dataset_compare audit research/data/newdata-20261013/original/smishguard_dataset_2026-10-12 $run --source research/data/expanded-20261005/experiment-v1 --base research/data/mbert-20261002/base --snapshots research/data/source-evidence-pinned',
        '& $python scripts/train_update_with_verified_cache.py $run',
        '& $python scripts/audit_ensemble_lineage.py $run','& $python scripts/audit_ensemble_oof.py $run',
        '& $python -m smishguard.ensemble_compare freeze $run','& $python -m smishguard.ensemble_compare evaluate $run',
        '& $python scripts/report_new_dataset_comparison.py $run --output docs/new-dataset-comparison-REPRODUCTION.md','```','']
    destination.write_text('\n'.join(lines),encoding='utf-8')
    print('Aggregate report saved:',destination,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('run',type=Path)
    p.add_argument('--output',type=Path,default=ROOT/'docs/new-dataset-comparison-20261013.md')
    a=p.parse_args()
    report(a.run,a.output)
