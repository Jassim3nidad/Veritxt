# SmishGuard fixed-setting retraining and ensemble comparison

The protocol and initial training were frozen on 11 October; interrupted OOF training was recovered and evaluation completed on 12 October 2026. All figures below are actual measurements from the completed local run. Smishing-class F1 is the existing primary metric. The same previously exposed test partition was held out of every fit in this run; it is **retrospective, not a newly untouched or prospective test**. Labels remain source/rule-derived and independently unconfirmed.

**Observed standalone leader(s): Linear SVM.** Standalone Logistic Regression did not win.

The configuration selected by validation was **LR + Linear SVM + Multinomial NB → LR** (stacking). The descriptive test leader(s), without any reselection or refitting, were **Linear SVM, LR + Linear SVM**, F1 0.9245.

## Audit and LR diagnosis

- Original dataset, case view, group splits and historical model hashes passed verification. All six partition pairs have zero group overlap and zero normalized-text overlap. The original five training folds have complete single-coverage OOF assignments and no crossing groups.
- All three classical models use the same 4,028-feature training-only unigram TF-IDF. Reconstructing vocabulary and IDF from training exactly reproduced the historical values. NB receives nonnegative TF-IDF. mBERT receives its own redacted, case-preserving tokenized text; no NB model receives embeddings.
- Labels and probability columns consistently map ham=0, smishing=1. Case-preserving and classical views reconcile on every record. There are no conflicting labels among identical normalized messages. These checks cannot establish that inherited labels are correct.
- Retrained LR, NB and SVM estimator settings, feature settings, fitted parameters, calibration parameters and thresholds all match their originals exactly. Their historical validation probabilities are reproduced exactly (maximum absolute difference 0). No current classification/preprocessing bug was confirmed, and no baseline bug fix or parameter change was applied. The old supplied evidence scripts used pre-vectorized inner CV; the current pipeline already corrects that by fitting TF-IDF inside every fold. Those historical result tables are not interchangeable with this grouped experiment.
- Historical LR/SVM/NB portable exports were checked against their Python validation probabilities: all decisions agree and maximum score error is below 4e-15. The retained binary labels also exactly match the original intake ledger mapping and original content fingerprints. No export, class inversion or label-conversion bug was found.
- The retrained mBERT selected checkpoint has the identical SHA-256 as the original; both epochs reproduce validation AP and training loss, and the fitted calibration coefficient/intercept differences are zero. This confirms reproduction of all four standalone baselines.
- LR validation F1 is 0.892857 (50 TP, 11 FN, 1 FP); NB is 0.900901 (50 TP, 11 FN, 0 FP); SVM is 0.913793 (53 TP, 8 FN, 2 FP). LR validation AP is 0.953827 versus NB 0.970047 and SVM 0.964033. This supports a performance difference under the frozen setup, not evidence that LR should have won or that its probabilities were reversed.
- LR fixed-0.5 diagnostics are F1 0.880734 with native probabilities and 0.870968 with calibrated probabilities, both below its preserved-threshold result. These are validation-only diagnostics, not threshold searches or new candidate baselines. The saved threshold favors precision, but changing it to favor recall would violate this experiment.
- Training has 223 smishing and 1,637 ham messages; validation 61/561; calibration 53/357; test 56/392. The ASCII unigram baseline deliberately removes case, punctuation and non-ASCII letters. This limits representation but affects the three classical models consistently. No relabeling, rebalancing, feature expansion, seed search or data exclusion was introduced.
- Prior exposure remains substantial: 3,269 of 3,340 records have known exact/near historical overlap. Source-derived lexical label rules and source imbalance limit generalization; they are plausible confounds, not demonstrated causes of LR’s ranking.

The post-evaluation error audit makes the LR gap concrete: LR misses 25 of 56 smishing messages, versus 7 for SVM. SVM catches 18 smishing messages missed by LR; LR catches none missed by SVM. Both have one false positive. LR’s 25 misses occupy 12 template groups, with 12 misses in a single group, so row counts overstate the number of independent failures. Of LR’s misses, 22 come from the BwandoWando source and 18 have the inherited impersonation category. These are post-hoc descriptive counts, not subgroup performance estimates or causal proof. No data was removed and no model was changed after this analysis. The confirmed immediate issue is poor recall/generalization at the frozen LR operating point, not a software defect established by this audit.

## Preserved and additional configurations

LR C=10, liblinear, max_iter=2000; NB alpha=0.1; Linear SVM C=10, dual=auto, max_iter=10000. Classical seed 20260929. Baseline sigmoids retain the calibration partition; thresholds remain LR 0.82, NB 0.63, SVM 0.59, mBERT 0.89 (stored float unchanged). No historical grid search or new threshold optimization was run.

mBERT uses the original pinned multilingual cased checkpoint, seed 20261005, two epochs, Adafactor 2e-5, weight decay .01, microbatch 1, accumulation 8, deterministic CUDA float16 training and the training-only p95 length rule. Baseline checkpoints are selected by validation AP, as before. Stacking folds use fixed epoch 2 and derive their own training-only lengths, so outer validation labels never choose a fold checkpoint.

Every completed voting combination uses equal-weight soft voting, native LR/NB/mBERT probabilities and a separate training-only OOF sigmoid for SVM. The baseline sigmoid and saved thresholds are not reused as learned ensemble components. All probability matrices pass orientation, finiteness, range and normalization checks. Voting and stacking use fixed threshold 0.5, with equality assigned to ham. The documented hard-vote fallback also ties to ham; it was not needed.

Both stacking meta-classifiers are LR (C=1, lbfgs, max_iter=2000, seed 20260929). Each meta-training matrix has exactly 1,860 OOF rows from the original training partition. SVM calibration uses a further five group folds within each outer fitting fold, including fold-specific TF-IDF. All five independently fine-tuned mBERT folds completed and supplied its OOF column. Neither meta-classifier fits validation, calibration or test predictions. Historical hyperparameters are fixed inputs; these OOF predictions are not a fresh unbiased evaluation of the historical selection procedure.

## Results

All metrics below are percentages except times and counts. Confusion matrices are **TN / FP / FN / TP**, equivalent to rows=true ham/smishing, columns=predicted ham/smishing. Tables are ordered by test F1 for description only. Val F1 shows the ranking available before the final opening.

### Standalone

| Model | Val F1 | Accuracy | Precision | Recall | F1 | Macro-F1 | TN / FP / FN / TP | Train s | CPU inference s |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|
| Linear SVM | 91.38 | 98.21 | 98.00 | 87.50 | 92.45 | 95.72 | 391 / 1 / 7 / 49 | 0.056 | 0.0094 |
| LR | 89.29 | 94.20 | 96.88 | 55.36 | 70.45 | 83.62 | 391 / 1 / 25 / 31 | 0.074 | 0.0089 |
| mBERT | 87.27 | 92.63 | 100.00 | 41.07 | 58.23 | 77.09 | 392 / 0 / 33 / 23 | 674.696 | 64.7518 |
| Multinomial NB | 90.09 | 91.07 | 83.33 | 35.71 | 50.00 | 72.55 | 388 / 4 / 36 / 20 | 0.054 | 0.0094 |

All requested experiments in this family completed.

### Voting

| Model | Val F1 | Accuracy | Precision | Recall | F1 | Macro-F1 | TN / FP / FN / TP | Train s | CPU inference s |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|
| LR + Linear SVM | 90.43 | 98.21 | 98.00 | 87.50 | 92.45 | 95.72 | 391 / 1 / 7 / 49 | 0.346 | 0.0183 |
| Linear SVM + Multinomial NB | 91.23 | 95.31 | 94.87 | 66.07 | 77.89 | 87.64 | 390 / 2 / 19 / 37 | 0.333 | 0.0190 |
| LR + Linear SVM + Multinomial NB | 90.27 | 94.87 | 97.14 | 60.71 | 74.73 | 85.93 | 391 / 1 / 22 / 34 | 0.387 | 0.0279 |
| LR + Linear SVM + mBERT | 92.98 | 93.75 | 100.00 | 50.00 | 66.67 | 81.61 | 392 / 0 / 28 / 28 | 665.646 | 64.7698 |
| LR + mBERT | 88.07 | 92.63 | 100.00 | 41.07 | 58.23 | 77.09 | 392 / 0 / 33 / 23 | 665.355 | 64.7604 |
| Linear SVM + mBERT | 88.07 | 92.63 | 100.00 | 41.07 | 58.23 | 77.09 | 392 / 0 / 33 / 23 | 665.592 | 64.7610 |
| Multinomial NB + mBERT | 88.07 | 92.41 | 100.00 | 39.29 | 56.41 | 76.13 | 392 / 0 / 34 / 22 | 665.342 | 64.7612 |
| Linear SVM + Multinomial NB + mBERT | 92.04 | 91.96 | 100.00 | 35.71 | 52.63 | 74.12 | 392 / 0 / 36 / 20 | 665.633 | 64.7706 |
| LR + Linear SVM + Multinomial NB + mBERT | 91.07 | 91.74 | 100.00 | 33.93 | 50.67 | 73.08 | 392 / 0 / 37 / 19 | 665.688 | 64.7794 |
| LR + Multinomial NB + mBERT | 90.09 | 91.52 | 100.00 | 32.14 | 48.65 | 72.01 | 392 / 0 / 38 / 18 | 665.396 | 64.7700 |
| LR + Multinomial NB | 87.04 | 91.07 | 100.00 | 28.57 | 44.44 | 69.80 | 392 / 0 / 40 / 16 | 0.096 | 0.0185 |

All requested experiments in this family completed.

### Stacking

| Model | Val F1 | Accuracy | Precision | Recall | F1 | Macro-F1 | TN / FP / FN / TP | Train s | CPU inference s |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|
| LR + Linear SVM + Multinomial NB → LR | 93.22 | 97.99 | 96.08 | 87.50 | 91.59 | 95.22 | 390 / 2 / 7 / 49 | 2.526 | 0.0281 |
| mBERT + Linear SVM + Multinomial NB → LR | 93.10 | 95.98 | 97.50 | 69.64 | 81.25 | 89.50 | 391 / 1 / 17 / 39 | 2979.760 | 64.7707 |

All requested experiments in this family completed.

## Selection and added complexity

| Family | Validation-selected entry | Test F1 difference vs selected standalone | Paired 95% group interval |
|---|---|---:|---|
| standalone | Linear SVM | +0.00 pp | [+0.00, +0.00] pp |
| voting | LR + Linear SVM + mBERT | -25.79 pp | [-43.02, +2.04] pp |
| stacking | LR + Linear SVM + Multinomial NB → LR | -0.86 pp | [-3.86, +0.00] pp |

The validation-selected voting configuration changes test F1 by -25.79 percentage points relative to the validation-selected standalone. Its training cost is 665.646 s versus 0.056 s; CPU batch inference is 64.7698 s versus 0.0094 s. There is no test-F1 gain to justify the added ensemble construction and maintenance in this comparison.

The validation-selected stacking configuration changes test F1 by -0.86 percentage points relative to the validation-selected standalone. Its training cost is 2.526 s versus 0.056 s; CPU batch inference is 0.0281 s versus 0.0094 s. There is no test-F1 gain to justify the added ensemble construction and maintenance in this comparison.


LR + SVM voting produces exactly the same 448 test decisions as standalone SVM. Its tied F1 therefore adds no observed detection benefit, while requiring an extra model and training-only SVM calibration. The mBERT stack raises its family test F1 to 81.25% versus 58.23% for standalone mBERT, but remains below standalone SVM at 92.45% and costs approximately 49.7 minutes of successful fitting/OOF work. The classical stack reaches the same 49 true positives as SVM with one additional false positive. On this experiment’s primary metric, no ensemble justifies its additional complexity.

Intervals use 2,000 paired template-group bootstrap draws, seed 20260929, conditional on fixed fitted models. They do not include training variability, uncertain labels, prior exposure or correction for examining many models. A test-leading combination is descriptive; only the validation-selected entries were eligible to be selected.

Training seconds include required component fits and, for stacking, OOF fitting/prediction plus meta fitting. Shared components are counted once within each configuration; summing table rows would double-count reused work. Voting SVM cost includes its training-only calibration folds. Stacking reuses their margins rather than fitting them again. Baseline timings exclude the historical hyperparameter search. mBERT training timing starts after model initialization and includes checkpoint saving; the standalone calibration total also includes loading and GPU prediction needed to fit its sigmoid. Inference covers all 448 test records on CPU, four torch threads, tokenization/vectorization and combination included; model loading is excluded. Ensemble component batch timings are reused and summed for sequential execution. These are single-run host timings, not physical-device benchmarks.

The original process stopped during the second mBERT OOF fit between sessions. The completed first fold and every standalone model were preserved. The incomplete second-fold configuration is archived privately, and that fold was restarted from the same pinned base and seed on 12 October. No partial result was used. Completed fold-1 OOF probabilities reproduced exactly when re-scored to recover its lost timing. Training totals count successful required fits; elapsed time for the interrupted attempt was not captured and is excluded, not invented.

## Reproduction and artifacts

Protocol: [fixed-setting experiment](ensemble-comparison-protocol-20261011.md). Machine-readable [JSON](ensemble-comparison-20261011.json) and [CSV](ensemble-comparison-20261011.csv) retain full precision. The JSON includes per-model group-bootstrap intervals, audit aggregates, configuration status and selection evidence.

Private run: `research/data/ensemble-20261011/experiment-v1`. It contains dataset/case snapshots, original split indices and IDs, hashes, source code snapshots, pip environment, classical baselines/calibrators, every outer and nested classical fold fit, mBERT checkpoints/tokenizers, OOF arrays, meta-training matrices/models, frozen selection, validation/test predictions and timings. No app assets or historical models were changed. No private weights or message-bearing files are published.

Verification: all 103 research tests passed, including eight new ensemble tests. Saved-artifact checks verified 40 classical fold vocabularies/IDFs, 25 nested SVM calibration folds, five mBERT OOF folds, exact baseline parameter reproduction and validation export parity. All four standalone test confusion matrices and metrics exactly reproduce the historical baseline evaluation. The 17 confusion matrices each cover the same 448 test records, and their F1 values were independently recomputed from counts. There are no unsupported final experiments; the interrupted attempt and successful recovery are explicitly recorded.

```powershell
$env:PYTHONPATH='research'
$python='research/data/mbert-20261002/venv/Scripts/python.exe'
$run='research/data/ensemble-20261011/NEW-RUN'
& $python -m smishguard.ensemble_compare audit $run --source research/data/expanded-20261005/experiment-v1 --base research/data/mbert-20261002/base
& $python -m smishguard.ensemble_compare train $run
& $python scripts/audit_ensemble_lineage.py $run
& $python scripts/audit_ensemble_oof.py $run
& $python -m smishguard.ensemble_compare freeze $run
& $python -m smishguard.ensemble_compare evaluate $run
& $python scripts/report_ensemble_comparison.py $run --output docs/ensemble-comparison-REPRODUCTION.md
```

Use a fresh directory; existing training, selection and test markers refuse overwrite. A failed fit is recorded rather than silently changing devices, batch sizes, budgets or hyperparameters. The test evaluation rejects changed sealed models/configurations. Reproduction requires the existing private data and pinned local base checkpoint.

For an interrupted mBERT OOF phase with completed standalone baselines and no selection/test marker, run `scripts/resume_ensemble_training.py $run` with the same environment after confirming the previous process has stopped. It retains completed folds, archives incomplete attempts within the run, and records recovery. It does not resume after final selection.

Dataset SHA-256: `c3abc4bb23742226deab491821c1828559d895242da55267c77ae6f7dfa07b21`. Split SHA-256: `67e064af947e5194cada9facff7fa02663d02dd2fff0756acbee9c58c50c4b1f`.
