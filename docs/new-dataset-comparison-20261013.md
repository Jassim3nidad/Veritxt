# SmishGuard supplied-update audit and fixed-setting comparison

The configuration selected on validation was **LR + Linear SVM + Multinomial NB → LR** (stacking, F1 0.9322). The descriptive test leader(s) were **Linear SVM, LR + Linear SVM**, F1 0.9245. No model was changed or reselected after test evaluation.

**This is retrospective reproduction, not evidence of performance on newly admitted data.** The 12 October package contains 4,261 rows, but its eligible binary fitting corpus remains exactly the previous 3,340 ordered records (2,947 ham, 393 smishing). The rebuilt template groups, four partitions and five training folds also exactly match the earlier experiment. All 448 reserved test messages have exact historical exposure. They are held out of current fitting, calibration and selection, but cannot be described as untouched or prospective.

## Data audit and confirmed limitations

- Original ZIP and all eight members are preserved privately. Supplied scripts were inspected and never executed. Strict UTF-8 parsing, schema/identity checks, source joins, label orientation, grouping and history checks preceded fitting. Smishing maps to 1 and ham to 0; source spam labels are not directly mapped to smishing.
- Supplied labels: 577 smishing, 3,184 ham, 500 gambling_ad. The third label is preserved and held; there is no authorized binary mapping. Advertising is not silently converted to either class.
- The remaining holds are 263 GitHub rows (including 203 A.S.E.A. rows with explicitly pending permission), 19 team rows with unresolved origin/use evidence, and 139 existing automated privacy holds. This retains the established experiment source/privacy policy. The 709 additions (203 ASEA, 6 screenshots, 500 ads) contribute zero newly eligible binary records.
- Earlier message texts, labels, IDs and order are unchanged. Eight date metadata fields changed; dates are not model inputs. The auxiliary ASEA CSV duplicates its 203 final-dataset rows and is not appended a second time. The 500 ads were moved from the old excluded corpus; they are not 500 newly collected independent messages.
- README contains stale earlier-version counts and a binary column description despite three labels. Source categories and heuristic confidence do not establish truth. The updated review workbook contains 118 flagged records and a 300-row sample, with zero filled labeler/final-label cells; empty review cells are not approvals.
- Exact cleaned duplicates: 0; normalized conflicting-label groups: 0; supplied template-key mismatches: 0; full-package near-template groups: 2595. Near groups with differing labels are documented, not automatically relabeled.
- Historical inventory: 22 available corpora, 2978 distinct normalized messages. Among all 4,261 supplied rows, 3595 have exact and 13 have additional near-only overlap; 653 have no detected overlap. Files with unknown fitting membership are recorded as possible prior corpus exposure. No detected match does not establish independent unseen data.
- Missing fields, per-source labels, label-method/confidence counts, historical label disagreements, workbook review counts and file hashes are retained in the JSON audit. Original labels are preserved even when they disagree with earlier labels. Independent labels/privacy reviews remain pending.
- Included/excluded overlap: no exact cleaned text overlap, but 114 excluded messages collide after preprocessing, 316 share a template, and 346 have a direct near witness in the included corpus. Near witnesses occur against 10 smishing, 16 ham and 321 gambling-ad records (counts can overlap). These are scope/representation ambiguities, not automatic label errors; all excluded records remain excluded.
- No current training, labeling-conversion or probability-order bug was confirmed. Historical supplied pre-vectorized CV was already corrected by the established fold-local TF-IDF pipeline; no new bug fix was applied.

## Fixed settings and fitting evidence

Freshly refitted standalone LR, NB, SVM and mBERT use the previous settings and training budgets. LR C=10/liblinear, NB alpha=.1, SVM C=10/dual=auto; unigram TF-IDF and seed 20260929. Baseline calibration uses only the reserved calibration partition. Saved thresholds remain LR .82, NB .63, SVM .59 and mBERT 0.8899999999999999. No hyperparameter, threshold or weight search ran.

mBERT uses the pinned multilingual cased base/tokenizer, seed 20261005, two epochs, Adafactor 2e-5, weight decay .01, microbatch 1, accumulation 8, deterministic CUDA float16, training-only p95 length and a 2700-second fit budget. Standalone checkpoint selection uses validation AP. Stacking bases use fixed epoch 2, their own training-only length rule and no outer-validation checkpoint selection.

Five mBERT OOF fits were reused after verifying identical ordered fitting views, labels, groups/folds, settings, fitting code after universal-newline decoding, dependency versions and frozen artifact hashes. They are saved in the new directory with explicit reuse provenance. Their original successful OOF training costs are included when assessing the cost to build a stack; these are not newly performed training seconds.

Eleven voting combinations use equal-weight soft voting on correctly ordered valid probabilities. LR/NB probabilities are native; mBERT predictions come from its independently fitted model; SVM has a distinct sigmoid fitted only on training-fold OOF margins. Every vocabulary/IDF is fitted inside its own fold. Threshold .5, equality to ham. NB receives nonnegative TF-IDF.

The two LR meta-classifiers are separate from standalone LR. They fit only training OOF matrices: (LR,SVM,NB)→LR and (mBERT,SVM,NB)→LR. SVM OOF calibration uses five nested grouped folds per outer fold. Meta C=1/lbfgs/max_iter=2000/seed=20260929; threshold .5, equality to ham. Both OOF matrices and actual fold pipelines/checkpoints are saved. Selection uses validation smishing F1; ties use lexicographic experiment ID. Fixed historical hyperparameters are prespecified inputs to this run; OOF predictions do not undo their historical selection on this same training corpus or constitute an unbiased assessment of that earlier selection.

## Standalone

Ranks are global across finalized configurations. Metrics are percentages; confusion order is TN / FP / FN / TP.

### Validation

| Model | Val rank | Test rank | Accuracy | Precision | Recall | F1 | Macro-F1 | FPR | TN / FP / FN / TP | Required train s | CPU infer s | ms/record |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| Linear SVM | 5 | 1 | 98.39 | 96.36 | 86.89 | 91.38 | 95.25 | 0.36 | 559 / 2 / 8 / 53 | 0.063 | 0.0112 | 0.0180 |
| Multinomial NB | 10 | 15 | 98.23 | 100.00 | 81.97 | 90.09 | 94.56 | 0.00 | 561 / 0 / 11 / 50 | 0.049 | 0.0109 | 0.0175 |
| LR | 12 | 7 | 98.07 | 98.04 | 81.97 | 89.29 | 94.11 | 0.18 | 560 / 1 / 11 / 50 | 0.068 | 0.0112 | 0.0181 |
| mBERT | 16 | 9 | 97.75 | 97.96 | 78.69 | 87.27 | 93.02 | 0.18 | 560 / 1 / 13 / 48 | 529.171 | 85.4093 | 137.3140 |

### Reserved retrospective test

| Model | Val rank | Test rank | Accuracy | Precision | Recall | F1 | Macro-F1 | FPR | TN / FP / FN / TP | Required train s | CPU infer s | ms/record |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| Linear SVM | 5 | 1 | 98.21 | 98.00 | 87.50 | 92.45 | 95.72 | 0.26 | 391 / 1 / 7 / 49 | 0.063 | 0.0086 | 0.0193 |
| Multinomial NB | 10 | 15 | 91.07 | 83.33 | 35.71 | 50.00 | 72.55 | 1.02 | 388 / 4 / 36 / 20 | 0.049 | 0.0088 | 0.0198 |
| LR | 12 | 7 | 94.20 | 96.88 | 55.36 | 70.45 | 83.62 | 0.26 | 391 / 1 / 25 / 31 | 0.068 | 0.0087 | 0.0195 |
| mBERT | 16 | 9 | 92.63 | 100.00 | 41.07 | 58.23 | 77.09 | 0.00 | 392 / 0 / 33 / 23 | 529.171 | 60.5237 | 135.0975 |

All requested configurations in this family completed.

## Voting

Ranks are global across finalized configurations. Metrics are percentages; confusion order is TN / FP / FN / TP.

### Validation

| Model | Val rank | Test rank | Accuracy | Precision | Recall | F1 | Macro-F1 | FPR | TN / FP / FN / TP | Required train s | CPU infer s | ms/record |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| LR + Linear SVM + mBERT | 3 | 8 | 98.71 | 100.00 | 86.89 | 92.98 | 96.14 | 0.00 | 561 / 0 / 8 / 53 | 521.529 | 85.4333 | 137.3526 |
| Linear SVM + Multinomial NB + mBERT | 4 | 13 | 98.55 | 100.00 | 85.25 | 92.04 | 95.62 | 0.00 | 561 / 0 / 9 / 52 | 521.520 | 85.4332 | 137.3524 |
| Linear SVM + Multinomial NB | 6 | 5 | 98.39 | 98.11 | 85.25 | 91.23 | 95.17 | 0.18 | 560 / 1 / 9 / 52 | 0.314 | 0.0224 | 0.0361 |
| LR + Linear SVM + Multinomial NB + mBERT | 7 | 14 | 98.39 | 100.00 | 83.61 | 91.07 | 95.09 | 0.00 | 561 / 0 / 10 / 51 | 521.567 | 85.4444 | 137.3704 |
| LR + Linear SVM | 8 | 2 | 98.23 | 96.30 | 85.25 | 90.43 | 94.73 | 0.36 | 559 / 2 / 9 / 52 | 0.323 | 0.0226 | 0.0363 |
| LR + Linear SVM + Multinomial NB | 9 | 6 | 98.23 | 98.08 | 83.61 | 90.27 | 94.65 | 0.18 | 560 / 1 / 10 / 51 | 0.361 | 0.0336 | 0.0541 |
| LR + Multinomial NB + mBERT | 11 | 16 | 98.23 | 100.00 | 81.97 | 90.09 | 94.56 | 0.00 | 561 / 0 / 11 / 50 | 521.291 | 85.4331 | 137.3522 |
| LR + mBERT | 13 | 10 | 97.91 | 100.00 | 78.69 | 88.07 | 93.46 | 0.00 | 561 / 0 / 13 / 48 | 521.253 | 85.4220 | 137.3344 |
| Multinomial NB + mBERT | 14 | 12 | 97.91 | 100.00 | 78.69 | 88.07 | 93.46 | 0.00 | 561 / 0 / 13 / 48 | 521.244 | 85.4219 | 137.3342 |
| Linear SVM + mBERT | 15 | 11 | 97.91 | 100.00 | 78.69 | 88.07 | 93.46 | 0.00 | 561 / 0 / 13 / 48 | 521.482 | 85.4223 | 137.3349 |
| LR + Multinomial NB | 17 | 17 | 97.75 | 100.00 | 77.05 | 87.04 | 92.90 | 0.00 | 561 / 0 / 14 / 47 | 0.085 | 0.0223 | 0.0359 |

### Reserved retrospective test

| Model | Val rank | Test rank | Accuracy | Precision | Recall | F1 | Macro-F1 | FPR | TN / FP / FN / TP | Required train s | CPU infer s | ms/record |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| LR + Linear SVM + mBERT | 3 | 8 | 93.75 | 100.00 | 50.00 | 66.67 | 81.61 | 0.00 | 392 / 0 / 28 / 28 | 521.529 | 60.5409 | 135.1359 |
| Linear SVM + Multinomial NB + mBERT | 4 | 13 | 91.96 | 100.00 | 35.71 | 52.63 | 74.12 | 0.00 | 392 / 0 / 36 / 20 | 521.520 | 60.5412 | 135.1366 |
| Linear SVM + Multinomial NB | 6 | 5 | 95.31 | 94.87 | 66.07 | 77.89 | 87.64 | 0.51 | 390 / 2 / 19 / 37 | 0.314 | 0.0178 | 0.0398 |
| LR + Linear SVM + Multinomial NB + mBERT | 7 | 14 | 91.74 | 100.00 | 33.93 | 50.67 | 73.08 | 0.00 | 392 / 0 / 37 / 19 | 521.567 | 60.5499 | 135.1561 |
| LR + Linear SVM | 8 | 2 | 98.21 | 98.00 | 87.50 | 92.45 | 95.72 | 0.26 | 391 / 1 / 7 / 49 | 0.323 | 0.0175 | 0.0392 |
| LR + Linear SVM + Multinomial NB | 9 | 6 | 94.87 | 97.14 | 60.71 | 74.73 | 85.93 | 0.26 | 391 / 1 / 22 / 34 | 0.361 | 0.0265 | 0.0592 |
| LR + Multinomial NB + mBERT | 11 | 16 | 91.52 | 100.00 | 32.14 | 48.65 | 72.01 | 0.00 | 392 / 0 / 38 / 18 | 521.291 | 60.5411 | 135.1364 |
| LR + mBERT | 13 | 10 | 92.63 | 100.00 | 41.07 | 58.23 | 77.09 | 0.00 | 392 / 0 / 33 / 23 | 521.253 | 60.5321 | 135.1163 |
| Multinomial NB + mBERT | 14 | 12 | 92.41 | 100.00 | 39.29 | 56.41 | 76.13 | 0.00 | 392 / 0 / 34 / 22 | 521.244 | 60.5324 | 135.1170 |
| Linear SVM + mBERT | 15 | 11 | 92.63 | 100.00 | 41.07 | 58.23 | 77.09 | 0.00 | 392 / 0 / 33 / 23 | 521.482 | 60.5323 | 135.1168 |
| LR + Multinomial NB | 17 | 17 | 91.07 | 100.00 | 28.57 | 44.44 | 69.80 | 0.00 | 392 / 0 / 40 / 16 | 0.085 | 0.0177 | 0.0396 |

All requested configurations in this family completed.

## Stacking

Ranks are global across finalized configurations. Metrics are percentages; confusion order is TN / FP / FN / TP.

### Validation

| Model | Val rank | Test rank | Accuracy | Precision | Recall | F1 | Macro-F1 | FPR | TN / FP / FN / TP | Required train s | CPU infer s | ms/record |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| LR + Linear SVM + Multinomial NB → LR | 1 | 3 | 98.71 | 96.49 | 90.16 | 93.22 | 96.25 | 0.36 | 559 / 2 / 6 / 55 | 2.308 | 0.0338 | 0.0544 |
| mBERT + Linear SVM + Multinomial NB → LR | 2 | 4 | 98.71 | 98.18 | 88.52 | 93.10 | 96.20 | 0.18 | 560 / 1 / 7 / 54 | 2835.482 | 85.4335 | 137.3528 |

### Reserved retrospective test

| Model | Val rank | Test rank | Accuracy | Precision | Recall | F1 | Macro-F1 | FPR | TN / FP / FN / TP | Required train s | CPU infer s | ms/record |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| LR + Linear SVM + Multinomial NB → LR | 1 | 3 | 97.99 | 96.08 | 87.50 | 91.59 | 95.22 | 0.51 | 390 / 2 / 7 / 49 | 2.308 | 0.0267 | 0.0596 |
| mBERT + Linear SVM + Multinomial NB → LR | 2 | 4 | 95.98 | 97.50 | 69.64 | 81.25 | 89.50 | 0.26 | 391 / 1 / 17 / 39 | 2835.482 | 60.5414 | 135.1370 |

All requested configurations in this family completed.

## LR and error patterns

Standalone LR test F1 is 0.7045, recall 0.5536, with 25 false negatives and 1 false positives. Standalone SVM has 7 false negatives and 1 false positives. SVM catches 18 smishing messages missed by LR; LR catches 0 missed by SVM. LR errors span 13 template groups. This describes poor recall at its fixed operating point, without establishing a software defect or requiring LR to win.

LR false-negative source counts: {'marketing': 3, 'bwandowando': 22}. Its false-negative category counts: {'Fake prize / reward / refund': 7, 'Impersonation (bank, e-wallet, government, courier, or brand)': 18}. These are post-evaluation descriptive counts under unconfirmed inherited labels, not causal explanations or independently validated subgroup estimates.

Validation-only native/calibrated LR diagnostics at the preserved threshold and fixed .5 are saved in JSON. They did not change its eligible threshold or configuration. Standalone LR performance is distinct from using LR to combine OOF component predictions.

## Ensemble complexity and paired uncertainty

| Family | Validation-selected entry | Test F1 difference vs selected standalone | Paired 95% group interval |
|---|---|---:|---|
| standalone | Linear SVM | +0.00 pp | [+0.00, +0.00] pp |
| voting | LR + Linear SVM + mBERT | -25.79 pp | [-43.02, +2.04] pp |
| stacking | LR + Linear SVM + Multinomial NB → LR | -0.86 pp | [-3.86, +0.00] pp |

The validation-selected voting changes test F1 by -25.79 percentage points versus Linear SVM. Required training cost is 521.529s versus 0.063s; sequential CPU test inference is 60.5409s versus 0.0086s. There is no observed test-F1 gain to justify its added components in this comparison.

The validation-selected stacking changes test F1 by -0.86 percentage points versus Linear SVM. Required training cost is 2.308s versus 0.063s; sequential CPU test inference is 0.0267s versus 0.0086s. There is no observed test-F1 gain to justify its added components in this comparison.

Intervals use 2,000 paired draws of whole template groups, seed 20260929. Per-model intervals and the paired LR−SVM difference are in JSON. Intervals are conditional on fixed fitted models, with no fitting or label uncertainty and no simultaneous multiple-comparison correction. Training costs count shared components once per hypothetical configuration, so summing table rows double-counts shared work. Inference includes each input transformation and combination, excludes model loading, and uses four torch CPU threads. Cached component timings are summed for sequential execution. These single-run host times are descriptive, not phone benchmarks.

LR + SVM voting makes exactly the same 448 test decisions as standalone SVM. Its tied test F1 adds no observed detection benefit while requiring another fitted component and training-only SVM calibration.

## Reproduction and preservation

All 17 of 17 comparable configurations reproduce the previous experiment's prediction-derived metrics exactly. The full supplied package changed, but the eligible fitting corpus and splits did not. This is a reproduction check, not a new-dataset improvement claim. Comparisons to the earlier 1,068-record dataset remain descriptive because that corpus differs.

Private artifacts: `research/data/newdata-20261013/experiment-v2/`. Original input archive/members, complete intake/hold ledger, full-package template groups, historical corpus inventory and exact/near ledgers, dataset/case snapshots, split IDs, fitted vectorizers/models/calibrators, OOF fold fits and matrices, tokenizers, configurations, code/dependency snapshots, frozen selection and finalized predictions remain private. The first audit attempt was interrupted before fitting to finalize the adapter and is preserved as `interrupted-audit-v1/`. Previous datasets, splits, fitted models and app assets were preserved; no deployment, push or external messaging occurred.

The initial cache gate compared raw saved LF source to the CRLF checkout and rejected reuse despite identical Python source. It triggered a fresh OOF fallback; that incomplete fold was stopped and preserved under `interrupted-attempts/`. Recovery verifies original raw source/artifact hashes, identical universal-newline source and ASTs, and the identical complete dependency lock including the original torch direct-wheel reference. The first recovery rejected that direct reference because it expected a version-pin line; this metadata parser was corrected before reuse. Neither fix changes fitting logic, settings, thresholds or predictions. No partial fallback result is used, and its unmeasured duration is excluded rather than invented. The cache-verification amendment and every attempt status were saved before selection. The reproduction driver performs this verification directly.

Verification: 108 research tests passed. 174 frozen artifacts, 73 historical input/model/app-asset files and all eight original archive members passed final hash checks. Both ZIP copies match the supplied download. All 17 test confusion matrices cover the same 448 reserved records, and every saved metric was independently recomputed from finalized scores.

Protocol: [frozen supplied-update procedure](new-dataset-comparison-protocol-20261013.md). Aggregate [JSON](new-dataset-comparison-20261013.json) and [CSV](new-dataset-comparison-20261013.csv) contain full-precision results; CSV includes validation and test separately.

Dataset SHA-256: `c3abc4bb23742226deab491821c1828559d895242da55267c77ae6f7dfa07b21`. Split SHA-256: `67e064af947e5194cada9facff7fa02663d02dd2fff0756acbee9c58c50c4b1f`.

```powershell
$env:PYTHONPATH='research'
$env:PYTHONIOENCODING='utf-8'
$python='research/data/mbert-20261002/venv/Scripts/python.exe'
$run='research/data/newdata-20261013/NEW-RUN'
& $python -m smishguard.new_dataset_compare audit research/data/newdata-20261013/original/smishguard_dataset_2026-10-12 $run --source research/data/expanded-20261005/experiment-v1 --base research/data/mbert-20261002/base --snapshots research/data/source-evidence-pinned
& $python scripts/train_update_with_verified_cache.py $run
& $python scripts/audit_ensemble_lineage.py $run
& $python scripts/audit_ensemble_oof.py $run
& $python -m smishguard.ensemble_compare freeze $run
& $python -m smishguard.ensemble_compare evaluate $run
& $python scripts/report_new_dataset_comparison.py $run --output docs/new-dataset-comparison-REPRODUCTION.md
```
