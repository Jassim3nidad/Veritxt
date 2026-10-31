# Veritxt model-selection recheck — 13 October 2026

Linear SVM remains the validation-selected single-model candidate in the latest grouped experiment. It is not a demonstrated universal or prospective traffic winner. The installed APK matches this selected fitted artifact exactly.

Replayed all 62 saved candidate configurations (both random/grouped tracks, including diagnostic configurations) on their original validation and test partitions without fitting, threshold tuning or changing app assets. All scores match saved predictions exactly; all confusion matrices and metrics reproduce. Diagnostic configurations were excluded from selection. All 9 stricter source-held-out evaluations also reproduce from their frozen fitted models. Dataset, splits and pipeline hashes passed the original freeze checks. Grouped train/validation/test partitions have disjoint record and template-group membership.

Each family below uses its feasible improvement candidate selected by validation scam-class F1 under the original rule. Thresholds are fixed at their original validation-selected values; test results are descriptive evaluations, not a new selection search.

| Family | Candidate | Validation F1 | Retrospective test F1 | Test precision | Test recall | TN/FP/FN/TP |
|---|---|---:|---:|---:|---:|---|
| svm | svm-C-10.0 | 96.55% | 95.24% | 94.59% | 95.89% | 421/4/3/70 |
| lr | lr-C-10.0 | 89.29% | 91.67% | 92.96% | 90.41% | 420/5/7/66 |
| nb | nb-word1-english | 91.07% | 87.41% | 95.16% | 80.82% | 422/3/14/59 |

The primary grouped candidate is `svm-C-10.0`, threshold ≥0.37. It correctly flags 70/73 smishing messages, misses 3, and flags 4/425 ham messages in the 498-record retrospective test. Several other SVM configurations tie its 95.24% test F1; its original selection is supported by the highest feasible grouped validation F1, not by a unique test-score lead. Random validation separately selects `svm-combined`; those different partitions do not give a directly comparable candidate ranking.

## Conditional uncertainty

Two thousand paired whole-template bootstrap draws on the same grouped test predictions give the following SVM-minus-comparator F1 differences. These conditional intervals do not include model/threshold selection, fitting variability, source transfer, historical exposure or label uncertainty; they do not establish prospective statistical superiority.

| Comparator | Observed difference, percentage points | Conditional 95% interval |
|---|---:|---|
| lr | 3.57 | 0.76 to 9.80 |
| nb | 7.83 | 0.86 to 18.86 |

## Source-transfer counterevidence

### English language subgroup

The same grouped test contains 347 English messages: 284 ham and 63 smishing. Saved predictions at the frozen thresholds give:

| Candidate | Detected smishing /63 | Missed smishing | False positives /284 ham | Scam-class F1 |
|---|---:|---:|---:|---:|
| svm-C-10.0 | 61 | 2 | 4 | 95.31% |
| lr-C-10.0 | 57 | 6 | 5 | 91.20% |
| nb-word1-english | 50 | 13 | 2 | 86.96% |

SVM leads these validation-selected family candidates on English subgroup F1 and recall. NB gives fewer false positives at the cost of more missed scams. The language subgroup is a descriptive retrospective evaluation with inherited labels and historical exposure; it does not establish prospective English-traffic superiority.

### Filipino/Taglish language subgroup

The current grouped test contains 151 records labeled `Filipino/Taglish`: 141 ham and only 10 smishing. Rechecking the saved predictions for each family’s validation-selected candidate gives:

| Candidate | Detected smishing /10 | Missed smishing | False positives /141 ham |
|---|---:|---:|---:|
| svm-C-10.0 | 9 | 1 | 0 |
| lr-C-10.0 | 9 | 1 | 0 |
| nb-word1-english | 9 | 1 | 1 |

SVM and LR tie on these aggregate subgroup counts. Ten positive examples and inherited labels do not establish a language-specific winner. The dataset combines Filipino and Taglish, so separate Tagalog-versus-Taglish rankings are unavailable. The held-source experiments below measure transfer across corpora and are not equivalent to this language subgroup or the installed APK’s exact fitted model.

| Held source | NB F1 | LR F1 | SVM F1 | SVM false positives |
|---|---:|---:|---:|---:|
| bwandowando | 81.48% | 76.92% | 80.37% | 0 |
| marketing | 81.15% | 87.97% | 92.09% | 6 |
| tagalog | 40.78% | 30.60% | 38.96% | 133 |

These source-held-out experiments refit models and choose operating thresholds using only the source complement. They evaluate model-family transfer; their fits/thresholds differ from the installed APK. NB leads on two held sources; SVM leads on marketing. The SVM Tagalog-held-out model yields only 25.28% precision and 133 false positives among 1,371 ham records. All three families struggle on that source. Bwandowando contains only smishing labels, so it cannot establish ham false-positive performance.

## Earlier ensemble/mBERT comparison

The separate [3,340-record fixed-setting study](new-dataset-comparison-20261013.md) selected `(LR + SVM + NB) → LR` stacking on validation F1 (93.22% versus standalone SVM 91.38%). On that study’s retrospective test, standalone SVM scored 92.45% and the selected stack 91.59%; choosing a new winner from that test ranking would reuse test evidence for selection. Standalone SVM led LR, NB and mBERT in that older study. Its 448-record test and differently prepared corpus must not be combined with the current 498-record grouped comparison to claim a single universal ranking. The older ensemble results were inspected from saved aggregate evidence here; the neural fits were not rerun.

## Assessment

Keep the current SVM as an experimental single-model candidate under the latest selection criterion. Present its grouped validation/test results with inherited-label and historical-exposure limitations. The source-held-out results prevent a claim that SVM is consistently best for new Philippine SMS traffic. This recheck does not supply new labels, new sources, prospective results, or a replacement model. The APK/model parameters were preserved.

[scikit-learn evaluation guidance](https://scikit-learn.org/1.6/modules/cross_validation.html) explains why model settings should be selected with validation evidence while test data is reserved for evaluation, and why preprocessing should be fitted inside the training folds. F1 reflects the precision/recall balance, not overall accuracy.

Private reproducible audit: `output/model-selection-recheck-20261013/recheck.py`, `aggregate.json`, `recheck.log`. Source artifacts: `research/runs/bantaytext-20261013/notebook-run-v3/`, `validation-v2/`. No raw message text or fitted coefficients are included in this report.
