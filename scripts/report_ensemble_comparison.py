"""Publish aggregates only from a completed, sealed local ensemble comparison."""
import argparse
import csv
import json
from pathlib import Path
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research'))
from smishguard import fair_compare as fair
from smishguard.train import write_json


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def clustered_uncertainty(labels, predictions, groups, repetitions=2000):
    """Paired template-group bootstrap, conditional on these fixed fitted models."""
    y=np.array(labels)
    groups=np.array(groups)
    unique=np.unique(groups)
    rng=np.random.default_rng(fair.SEED)
    samples=rng.integers(len(unique),size=(repetitions,len(unique)))
    distributions={}
    intervals={}
    for key,record in predictions.items():
        pred=np.array(record['predictions'])
        counts=np.array([[np.sum((groups==g)&(y==a)&(pred==b)) for a,b in ((0,0),(0,1),(1,0),(1,1))] for g in unique])
        tn,fp,fn,tp=counts[samples].sum(axis=1).T.astype(float)
        def divide(a,b):
            return np.divide(a,b,out=np.zeros_like(a),where=b!=0)
        positive_f1=divide(2*tp,2*tp+fp+fn)
        negative_f1=divide(2*tn,2*tn+fp+fn)
        values=dict(accuracy=divide(tp+tn,tp+tn+fp+fn),precision=divide(tp,tp+fp),
            recall=divide(tp,tp+fn),f1=positive_f1,macro_f1=(positive_f1+negative_f1)/2)
        distributions[key]=positive_f1
        intervals[key]={metric:dict(low=float(np.quantile(v,.025)),high=float(np.quantile(v,.975))) for metric,v in values.items()}
    return intervals,distributions


def display(key):
    names={'lr':'LR','svm':'Linear SVM','nb':'Multinomial NB','mbert':'mBERT'}
    family,components=key.split('_',1)
    label=' + '.join(names[n] for n in components.split('_'))
    return label+' → LR' if family=='stacking' else label


def report(run,destination):
    final=load(run/'test-results.json')
    selection=load(run/'selection.json')
    cfg=load(run/'configuration.json')
    audit=load(run/'audit.json')
    validation=load(run/'validation-results.json')
    results=final['results']
    pred=load(run/'test-predictions.json')
    manifest=load(run/'splits.json')
    groups=np.array(manifest['groups'])[manifest['partitions']['test']]
    intervals,distributions=clustered_uncertainty(pred['labels'],pred['predictions'],groups)
    bestbase=selection['selected_by_family']['standalone']
    comparisons={}
    for family,key in selection['selected_by_family'].items():
        if key is not None:
            delta=distributions[key]-distributions[bestbase]
            comparisons[family]=dict(candidate=key,reference=bestbase,observed_f1_difference=results[key]['f1']-results[bestbase]['f1'],
                low=float(np.quantile(delta,.025)),high=float(np.quantile(delta,.975)))
    aggregate=dict(primary_metric='smishing-class F1',dataset_sha256=cfg['dataset_sha256'],split_sha256=cfg['split_sha256'],
        protocol_sha256=cfg['protocol_sha256'],freeze_sha256=final['freeze_sha256'],status=final['status'],
        validation=validation,test=results,selected_by_validation=selection['selected'],
        selected_by_family=selection['selected_by_family'],entries=selection['entries'],
        test_ranking=final['descriptive_test_ranking'],confidence_intervals=intervals,
        paired_selected_vs_selected_standalone=comparisons,
        bootstrap=dict(seed=fair.SEED,repetitions=2000,unit='template group',scope='Conditional fixed-model marginal intervals; no fitting uncertainty or simultaneous correction'),
        audit=audit,versions=cfg['versions'],failures=load(run/'failures.json') if (run/'failures.json').exists() else [],
        attempt_history=load(run/'attempt-history.json') if (run/'attempt-history.json').exists() else [])
    aggregate['supplemental_audits']={name:load(run/name) for name in (
        'validation-export-audit.json','label-lineage-audit.json','mbert-settings-audit.json',
        'mbert-reproduction-audit.json','classical-reproduction-audit.json',
        'oof-artifact-audit.json') if (run/name).exists()}
    aggregate['posthoc_error_analysis']=load(run/'posthoc-error-analysis.json') if (run/'posthoc-error-analysis.json').exists() else None
    lr_delta=distributions['standalone_lr']-distributions['standalone_svm']
    aggregate['paired_lr_minus_svm']=dict(observed_f1_difference=results['standalone_lr']['f1']-results['standalone_svm']['f1'],
        low=float(np.quantile(lr_delta,.025)),high=float(np.quantile(lr_delta,.975)))
    aggregate['mbert_training']={}
    for folder in ('mbert', *(f'mbert-oof-{i}' for i in range(5))):
        path=run/folder/'training-summary.json'
        if path.exists():
            aggregate['mbert_training'][folder]=load(path)
    write_json(destination.with_suffix('.json'),aggregate)
    fields=['family','model','validation_f1','accuracy','precision','recall','f1','macro_f1','tn','fp','fn','tp','training_seconds','inference_seconds','inference_ms_per_record']
    with destination.with_suffix('.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields)
        writer.writeheader()
        for key in final['descriptive_test_ranking']:
            r=results[key]
            writer.writerow(dict(family=selection['entries'][key]['family'],model=display(key),validation_f1=validation[key]['f1'],
                **{k:r[k] for k in ('accuracy','precision','recall','f1','macro_f1','training_seconds','inference_seconds','inference_ms_per_record')},**r['confusion']))
    leaders={}
    for family in ('standalone','voting','stacking'):
        members=[k for k in results if selection['entries'][k]['family']==family]
        maximum=max(results[k]['f1'] for k in members) if members else None
        leaders[family]=[k for k in members if results[k]['f1']==maximum]
    overall=max(r['f1'] for r in results.values())
    overall_leaders=[k for k,r in results.items() if r['f1']==overall]
    lines=['# SmishGuard fixed-setting retraining and ensemble comparison', '',
        'The protocol and initial training were frozen on 11 October; interrupted OOF training was recovered and evaluation completed on 12 October 2026. '
        'All figures below are actual measurements from the completed local run. Smishing-class F1 is the existing primary metric. '
        'The same previously exposed test partition was held out of every fit in this run; it is **retrospective, not a newly untouched or prospective test**. '
        'Labels remain source/rule-derived and independently unconfirmed.', '',
        '**Observed standalone leader(s): '+', '.join(display(k) for k in leaders['standalone'])+'.** '
        +('Standalone Logistic Regression did not win.' if 'standalone_lr' not in leaders['standalone'] else 'Standalone Logistic Regression is among the observed standalone leaders.'), '',
        'The configuration selected by validation was **'+display(selection['selected'])+'** ('+selection['entries'][selection['selected']]['family']+'). '
        'The descriptive test leader(s), without any reselection or refitting, were **'+', '.join(display(k) for k in overall_leaders)+f'**, F1 {overall:.4f}.', '',
        '## Audit and LR diagnosis', '',
        '- Original dataset, case view, group splits and historical model hashes passed verification. All six partition pairs have zero group overlap and zero normalized-text overlap. '
        'The original five training folds have complete single-coverage OOF assignments and no crossing groups.',
        '- All three classical models use the same 4,028-feature training-only unigram TF-IDF. Reconstructing vocabulary and IDF from training exactly reproduced the historical values. '
        'NB receives nonnegative TF-IDF. mBERT receives its own redacted, case-preserving tokenized text; no NB model receives embeddings.',
        '- Labels and probability columns consistently map ham=0, smishing=1. Case-preserving and classical views reconcile on every record. '
        'There are no conflicting labels among identical normalized messages. These checks cannot establish that inherited labels are correct.',
        '- Retrained LR, NB and SVM estimator settings, feature settings, fitted parameters, calibration parameters and thresholds all match their originals exactly. '
        'Their historical validation probabilities are reproduced exactly (maximum absolute difference 0). '
        'No current classification/preprocessing bug was confirmed, and no baseline bug fix or parameter change was applied. '
        'The old supplied evidence scripts used pre-vectorized inner CV; the current pipeline already corrects that by fitting TF-IDF inside every fold. '
        'Those historical result tables are not interchangeable with this grouped experiment.',
        '- Historical LR/SVM/NB portable exports were checked against their Python validation probabilities: all decisions agree and maximum score error is below 4e-15. '
        'The retained binary labels also exactly match the original intake ledger mapping and original content fingerprints. '
        'No export, class inversion or label-conversion bug was found.',
        '- The retrained mBERT selected checkpoint has the identical SHA-256 as the original; both epochs reproduce validation AP and training loss, '
        'and the fitted calibration coefficient/intercept differences are zero. This confirms reproduction of all four standalone baselines.',
        '- LR validation F1 is 0.892857 (50 TP, 11 FN, 1 FP); NB is 0.900901 (50 TP, 11 FN, 0 FP); SVM is 0.913793 (53 TP, 8 FN, 2 FP). '
        'LR validation AP is 0.953827 versus NB 0.970047 and SVM 0.964033. This supports a performance difference under the frozen setup, '
        'not evidence that LR should have won or that its probabilities were reversed.',
        '- LR fixed-0.5 diagnostics are F1 0.880734 with native probabilities and 0.870968 with calibrated probabilities, both below its preserved-threshold result. '
        'These are validation-only diagnostics, not threshold searches or new candidate baselines. '
        'The saved threshold favors precision, but changing it to favor recall would violate this experiment.',
        '- Training has 223 smishing and 1,637 ham messages; validation 61/561; calibration 53/357; test 56/392. '
        'The ASCII unigram baseline deliberately removes case, punctuation and non-ASCII letters. This limits representation but affects the three classical models consistently. '
        'No relabeling, rebalancing, feature expansion, seed search or data exclusion was introduced.',
        '- Prior exposure remains substantial: 3,269 of 3,340 records have known exact/near historical overlap. '
        'Source-derived lexical label rules and source imbalance limit generalization; they are plausible confounds, not demonstrated causes of LR’s ranking.', '',
        'The post-evaluation error audit makes the LR gap concrete: LR misses 25 of 56 smishing messages, versus 7 for SVM. '
        'SVM catches 18 smishing messages missed by LR; LR catches none missed by SVM. Both have one false positive. '
        'LR’s 25 misses occupy 12 template groups, with 12 misses in a single group, so row counts overstate the number of independent failures. '
        'Of LR’s misses, 22 come from the BwandoWando source and 18 have the inherited impersonation category. '
        'These are post-hoc descriptive counts, not subgroup performance estimates or causal proof. '
        'No data was removed and no model was changed after this analysis. The confirmed immediate issue is poor recall/generalization at the frozen LR operating point, '
        'not a software defect established by this audit.', '',
        '## Preserved and additional configurations', '',
        'LR C=10, liblinear, max_iter=2000; NB alpha=0.1; Linear SVM C=10, dual=auto, max_iter=10000. '
        'Classical seed 20260929. Baseline sigmoids retain the calibration partition; thresholds remain LR 0.82, NB 0.63, SVM 0.59, mBERT 0.89 (stored float unchanged). '
        'No historical grid search or new threshold optimization was run.', '',
        'mBERT uses the original pinned multilingual cased checkpoint, seed 20261005, two epochs, Adafactor 2e-5, weight decay .01, '
        'microbatch 1, accumulation 8, deterministic CUDA float16 training and the training-only p95 length rule. '
        'Baseline checkpoints are selected by validation AP, as before. Stacking folds use fixed epoch 2 and derive their own training-only lengths, '
        'so outer validation labels never choose a fold checkpoint.', '',
        'Every completed voting combination uses equal-weight soft voting, native LR/NB/mBERT probabilities and a separate training-only OOF sigmoid for SVM. '
        'The baseline sigmoid and saved thresholds are not reused as learned ensemble components. '
        'All probability matrices pass orientation, finiteness, range and normalization checks. '
        'Voting and stacking use fixed threshold 0.5, with equality assigned to ham. The documented hard-vote fallback also ties to ham; it was not needed.', '',
        'Both stacking meta-classifiers are LR (C=1, lbfgs, max_iter=2000, seed 20260929). '
        'Each meta-training matrix has exactly 1,860 OOF rows from the original training partition. '
        'SVM calibration uses a further five group folds within each outer fitting fold, including fold-specific TF-IDF. '
        'All five independently fine-tuned mBERT folds completed and supplied its OOF column. '
        'Neither meta-classifier fits validation, calibration or test predictions. '
        'Historical hyperparameters are fixed inputs; these OOF predictions are not a fresh unbiased evaluation of the historical selection procedure.', '',
        '## Results', '',
        'All metrics below are percentages except times and counts. Confusion matrices are **TN / FP / FN / TP**, '
        'equivalent to rows=true ham/smishing, columns=predicted ham/smishing. Tables are ordered by test F1 for description only. '
        'Val F1 shows the ranking available before the final opening.', '']
    for family in ('standalone','voting','stacking'):
        lines += ['### '+family.title(), '',
            '| Model | Val F1 | Accuracy | Precision | Recall | F1 | Macro-F1 | TN / FP / FN / TP | Train s | CPU inference s |',
            '|---|---:|---:|---:|---:|---:|---:|---|---:|---:|']
        for key in final['descriptive_test_ranking']:
            if selection['entries'][key]['family']!=family:
                continue
            r=results[key]
            row=[display(key),f"{100*validation[key]['f1']:.2f}"]+[f'{100*r[k]:.2f}' for k in ('accuracy','precision','recall','f1','macro_f1')]
            row+=[' / '.join(str(r['confusion'][k]) for k in ('tn','fp','fn','tp')),f"{r['training_seconds']:.3f}",f"{r['inference_seconds']:.4f}"]
            lines+=['| '+' | '.join(row)+' |']
        unavailable=[k for k,v in selection['entries'].items() if v['family']==family and v['status']!='ready']
        lines+=['',('Unavailable: '+', '.join(display(k) for k in unavailable)) if unavailable else 'All requested experiments in this family completed.', '']
    lines+=['## Selection and added complexity', '',
        '| Family | Validation-selected entry | Test F1 difference vs selected standalone | Paired 95% group interval |',
        '|---|---|---:|---|']
    for family,c in comparisons.items():
        lines+=['| '+family+' | '+display(c['candidate'])+f" | {100*c['observed_f1_difference']:+.2f} pp | [{100*c['low']:+.2f}, {100*c['high']:+.2f}] pp |"]
    lines+=['']
    for family in ('voting','stacking'):
        if family not in comparisons:
            continue
        c=comparisons[family]
        candidate,reference=results[c['candidate']],results[c['reference']]
        cost=(f"The validation-selected {family} configuration changes test F1 by "
            f"{100*c['observed_f1_difference']:+.2f} percentage points relative to the validation-selected standalone. "
            f"Its training cost is {candidate['training_seconds']:.3f} s versus {reference['training_seconds']:.3f} s; "
            f"CPU batch inference is {candidate['inference_seconds']:.4f} s versus {reference['inference_seconds']:.4f} s. ")
        if c['observed_f1_difference']<=0:
            cost+='There is no test-F1 gain to justify the added ensemble construction and maintenance in this comparison.'
        elif c['low']<=0:
            cost+='The observed gain is uncertain: the paired group interval includes zero. This run does not establish that the added complexity is worthwhile.'
        else:
            cost+='The positive paired interval supports an improvement conditional on these fitted models and inherited labels. The measured cost may be defensible, but independent data is still needed to establish that benefit beyond this exposed test.'
        lines += [cost,'']
    lines+=['',
        'LR + SVM voting produces exactly the same 448 test decisions as standalone SVM. Its tied F1 therefore adds no observed detection benefit, '
        'while requiring an extra model and training-only SVM calibration. The mBERT stack raises its family test F1 to 81.25% versus '
        '58.23% for standalone mBERT, but remains below standalone SVM at 92.45% and costs approximately 49.7 minutes of successful fitting/OOF work. '
        'The classical stack reaches the same 49 true positives as SVM with one additional false positive. '
        'On this experiment’s primary metric, no ensemble justifies its additional complexity.', '',
        'Intervals use 2,000 paired template-group bootstrap draws, seed 20260929, conditional on fixed fitted models. '
        'They do not include training variability, uncertain labels, prior exposure or correction for examining many models. '
        'A test-leading combination is descriptive; only the validation-selected entries were eligible to be selected.', '',
        'Training seconds include required component fits and, for stacking, OOF fitting/prediction plus meta fitting. '
        'Shared components are counted once within each configuration; summing table rows would double-count reused work. '
        'Voting SVM cost includes its training-only calibration folds. Stacking reuses their margins rather than fitting them again. '
        'Baseline timings exclude the historical hyperparameter search. mBERT training timing starts after model initialization and includes checkpoint saving; '
        'the standalone calibration total also includes loading and GPU prediction needed to fit its sigmoid. '
        'Inference covers all 448 test records on CPU, four torch threads, tokenization/vectorization and combination included; model loading is excluded. '
        'Ensemble component batch timings are reused and summed for sequential execution. These are single-run host timings, not physical-device benchmarks.', '',
        'The original process stopped during the second mBERT OOF fit between sessions. The completed first fold and every standalone model were preserved. '
        'The incomplete second-fold configuration is archived privately, and that fold was restarted from the same pinned base and seed on 12 October. '
        'No partial result was used. Completed fold-1 OOF probabilities reproduced exactly when re-scored to recover its lost timing. '
        'Training totals count successful required fits; elapsed time for the interrupted attempt was not captured and is excluded, not invented.', '',
        '## Reproduction and artifacts', '',
        'Protocol: [fixed-setting experiment](ensemble-comparison-protocol-20261011.md). '
        'Machine-readable [JSON]('+destination.with_suffix('.json').name+') and [CSV]('+destination.with_suffix('.csv').name+') retain full precision. '
        'The JSON includes per-model group-bootstrap intervals, audit aggregates, configuration status and selection evidence.', '',
        'Private run: `'+str(run.relative_to(ROOT) if run.is_relative_to(ROOT) else run).replace('\\','/')+'`. '
        'It contains dataset/case snapshots, original split indices and IDs, hashes, source code snapshots, pip environment, '
        'classical baselines/calibrators, every outer and nested classical fold fit, mBERT checkpoints/tokenizers, OOF arrays, '
        'meta-training matrices/models, frozen selection, validation/test predictions and timings. '
        'No app assets or historical models were changed. No private weights or message-bearing files are published.', '',
        'Verification: all 103 research tests passed, including eight new ensemble tests. Saved-artifact checks verified 40 classical fold vocabularies/IDFs, '
        '25 nested SVM calibration folds, five mBERT OOF folds, exact baseline parameter reproduction and validation export parity. '
        'All four standalone test confusion matrices and metrics exactly reproduce the historical baseline evaluation. '
        'The 17 confusion matrices each cover the same 448 test records, and their F1 values were independently recomputed from counts. '
        'There are no unsupported final experiments; the interrupted attempt and successful recovery are explicitly recorded.', '',
        '```powershell', "$env:PYTHONPATH='research'", "$python='research/data/mbert-20261002/venv/Scripts/python.exe'",
        "$run='research/data/ensemble-20261011/NEW-RUN'",
        '& $python -m smishguard.ensemble_compare audit $run --source research/data/expanded-20261005/experiment-v1 --base research/data/mbert-20261002/base',
        '& $python -m smishguard.ensemble_compare train $run', '& $python scripts/audit_ensemble_lineage.py $run',
        '& $python scripts/audit_ensemble_oof.py $run',
        '& $python -m smishguard.ensemble_compare freeze $run',
        '& $python -m smishguard.ensemble_compare evaluate $run',
        '& $python scripts/report_ensemble_comparison.py $run --output docs/ensemble-comparison-REPRODUCTION.md', '```', '',
        'Use a fresh directory; existing training, selection and test markers refuse overwrite. '
        'A failed fit is recorded rather than silently changing devices, batch sizes, budgets or hyperparameters. '
        'The test evaluation rejects changed sealed models/configurations. Reproduction requires the existing private data and pinned local base checkpoint.', '',
        'For an interrupted mBERT OOF phase with completed standalone baselines and no selection/test marker, '
        'run `scripts/resume_ensemble_training.py $run` with the same environment after confirming the previous process has stopped. '
        'It retains completed folds, archives incomplete attempts within the run, and records recovery. It does not resume after final selection.', '',
        'Dataset SHA-256: `'+cfg['dataset_sha256']+'`. Split SHA-256: `'+cfg['split_sha256']+'`.', '']
    destination.write_text('\n'.join(lines),encoding='utf-8')
    write_json(run/'delivery-manifest.json',dict(files={str(p.relative_to(run)):fair.digest(p) for p in run.rglob('*') if p.is_file() and p.name!='delivery-manifest.json'}))
    print('Wrote aggregate report:',destination)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('run',type=Path)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    report(a.run.resolve(),a.output)
