# Chapter 4 — Results and limitations (draft)

Revised thesis title: **Pending finalization**. The original manuscript title remains historical; title-dependent edits are pending. Current scope is **all SMS phishing**, clarified by the team without assuming adviser approval. See [current scope and working questions/objectives](scope-clarification-20261006.md).

This chapter reports the completed expanded retrospective experiment. Its labels await independent human review, and **439 of 448 test records have detected historical overlap**. The results are preliminary development evidence. Planned annotation, prospective collection and physical-phone tests have no findings yet; placeholders below must be replaced only by verified human evidence.

## 4.1 Data audit and experimental support

The supplied package's reported totals were confirmed: 3,552 included records, 468 smishing, 3,084 ham, 2,594 supplied template groups, 71 review flags and 2,272 excluded records. The usable subset contained 3,340 records (393 smishing and 2,947 ham). Source/consent/use issues held 73 records, while automated privacy concerns held 139. No excluded record was silently admitted as ham. Eighteen job/loan records with possible phishing signals await scope adjudication.

The audit found no duplicate IDs, cleaned exact duplicates, conflicting redacted labels, mixed-label supplied groups or template-key mismatches under its implemented checks. Missing sender/date values were 261/60. This does not certify independent labels or complete privacy review. The original raw-build process was not reproduced because the package lacked the original raw sources.

The frozen partitions contained 1,860 training, 622 validation, 410 calibration and 448 test records. The test had 392 ham and 56 phishing records across 251 groups, including 25 positive-bearing groups. Within the new assignment, audited template components did not cross partitions. Historical overlap remained substantial: 3,269/3,340 retained records and 439/448 test records matched earlier normalized exact or near-copy views. The nine unmatched test records are not certified independently unseen.

## 4.2 Four-model predictive results

All figures below use the identical frozen test cohort and inherited labels. Values are percentages except confusion counts.

| Model | Phishing precision | Recall | Phishing F1 | Macro-F1 | Accuracy | False-positive rate | TN / FP / FN / TP |
|---|---:|---:|---:|---:|---:|---:|---|
| Logistic Regression | 96.88 | 55.36 | 70.45 | 83.62 | 94.20 | 0.26 | 391 / 1 / 25 / 31 |
| Multinomial NB | 83.33 | 35.71 | 50.00 | 72.55 | 91.07 | 1.02 | 388 / 4 / 36 / 20 |
| Linear SVM | 98.00 | 87.50 | **92.45** | 95.72 | 98.21 | 0.26 | 391 / 1 / 7 / 49 |
| mBERT | 100.00 | 41.07 | 58.23 | 77.09 | 92.63 | 0.00 | 392 / 0 / 33 / 23 |

**SVM achieved the highest observed phishing F1 of 92.45%.** It detected 49 of the 56 phishing records with one false positive. LR and NB missed 25 and 36 phishing records respectively. mBERT produced no false positives in this sample but missed 33 phishing records. Its 100% observed precision therefore does not imply broad reliability or zero population false positives. Class imbalance also makes accuracy alone insufficient to characterize detection quality.

The selected thresholds and unfavorable results were preserved. No post-test retuning was performed. Differences from the older four-model experiment cannot alone establish improvement because membership, labels and scope changed.

## 4.3 Uncertainty and score calibration

| Model | F1, 95% group-bootstrap interval | Brier score | Log loss |
|---|---|---:|---:|
| Logistic Regression | 0.5455–0.8571 | 0.02576 | 0.09309 |
| Multinomial NB | 0.2521–0.8090 | 0.06899 | 0.22882 |
| Linear SVM | 0.7755–0.9787 | 0.02403 | 0.09549 |
| mBERT | 0.3278–0.9020 | 0.06533 | 0.24637 |

Intervals used 2,000 group resamples conditional on the fitted models. The paired SVM-minus-mBERT F1 interval was −0.0801 to 0.6331, spanning zero. LR-minus-SVM was −0.3723 to −0.0493 and NB-minus-SVM was −0.6971 to −0.0655. These are unadjusted exploratory comparisons; group imperfection, label uncertainty, historical exposure and omitted fitting/selection uncertainty prevent a final population-level winning-algorithm claim.

The [reliability plots](expanded-reliability-20261005.png) show empirical agreement between calibrated scores and inherited labels. They do not validate scores as real-world probabilities. The UI therefore continues to use “Model score.” Full reliability-bin counts and metric intervals appear in the [aggregate results](expanded-four-model-results-20261005.json).

## 4.4 Language and source findings

| Language | Ham / phishing | LR F1 | NB F1 | SVM F1 | mBERT F1 |
|---|---:|---:|---:|---:|---:|
| English | 270 / 45 | 71.43% | 42.11% | 94.12% | 52.46% |
| Filipino/Taglish | 122 / 11 | 66.67% | 69.57% | 85.71% | 77.78% |

Language assignments were supplied rough guesses, not independently validated language annotation. Subgroup results are descriptive. Of the test sources, marketing had 130 ham/8 phishing and met the prespecified support floor. BwandoWando had 0 ham/44 phishing and Tagalog had 262 ham/4 phishing; full source-specific metrics were suppressed for these sparse class distributions. Category support was retained, but category labels partly derived from the same labeling rules and cannot independently validate classifier behavior.

## 4.5 Training, deployment and runtime

| Model | Recorded training seconds | Cold detector load, ms | Warm median, ms | Warm p95, ms |
|---|---:|---:|---:|---:|
| Logistic Regression | 1.041 | 260.025 | 0.302 | 0.646 |
| Multinomial NB | 0.939 | 232.313 | 0.286 | 0.626 |
| Linear SVM | 1.030 | 219.413 | 0.314 | 0.668 |
| mBERT | 668.797 | 8,238.566 | 154.173 | 167.034 |

Baseline training durations include grouped selection, final fitting, calibration, threshold selection and export serialization. mBERT duration includes epochs, validation and checkpoint selection/writes, excluding initial loading and final calibration; the differing boundaries limit direct training-time comparisons. mBERT peak allocated CUDA memory was 2,227,597,824 bytes. Initial Windows process-memory probes failed and are reported unavailable rather than zero.

Runtime results are from the common emulator session, not physical phones. Each variant scored all 200 benchmark scans. The research-test app coverage was separately 448/448 for each model. No abstention was counted as a correct negative. Different devices, message lengths, cold-cache states and manual UI timing may produce different performance.

All four Android variants passed build, lint-error checks, JVM checks, model guards and offline emulator verification. Each baseline had 461 export parity cases, while mBERT had 468 and additional tokenizer/logit checks. The original baseline APKs were approximately 12.94 MB. The original expanded mBERT APK was 1,511,956,972 bytes despite a 712,625,479-byte asset bundle.

A subsequent packaging audit identified approximately 711.55 MB outside referenced ZIP entries. Rebuilding from a fresh packaging state reduced the mBERT APK to **800,410,184 bytes**, with the same model, tokenizer, metadata and referenced file contents. No quantization or retraining occurred. The original artifact is preserved. Repackaged mBERT also passed offline parity/scanning and privacy checks. This engineering result does not alter the historical model metrics or replace the original timing session.

Actual fictional-message screenshots were retained, including mBERT missing the English phishing demonstration at a 1.9% model score. LR, NB and SVM flagged that example; all four classified the benign Taglish example as non-phishing. These demonstrations are presentation evidence, not extra accuracy observations.

## 4.6 Pending independent evidence

| Evidence | Current status | Required insertion |
|---|---|---|
| Independent A/B annotation | Packets prepared; no completed decisions | [Actual reviewer attestations, dates, completed/missing counts and pre-adjudication agreement] |
| Adjudication/privacy/scope | Workflow and blank fields prepared | [Actual third-review decisions, privacy releases and 18 job/loan conflict outcomes] |
| Prospective evaluation | Intake/checks and model freeze prepared; no new records evaluated | [Receipt/source evidence, cohort flow, duplicates/holds, frozen labels and once-only model results] |
| Physical phones | Guide and blank results form prepared; no returns received | [Actual device/Android details, APK hashes, observations, timing method and evidence] |

The completed experiment supports a bounded engineering and retrospective comparison. Its strongest observed F1 belongs to SVM, while independent human labels, prospective generalization and physical-phone performance remain unestablished. These missing findings must remain placeholders until actual evidence is received.

Primary evidence: [frozen comparison report](four-model-comparison-20261005.md), [aggregate results](expanded-four-model-results-20261005.json), [verification](expanded-four-model-verification-20261005.json), [common emulator session](expanded-four-model-benchmark-20261005.json). The dated reports remain unchanged.
