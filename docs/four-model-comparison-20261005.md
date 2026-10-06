# SmishGuard expanded four-model comparison — 5 October 2026

All four models were trained, evaluated, exported and verified in separate offline Android APKs. This remains preliminary development evidence using source/rule labels and substantially exposed messages. No final algorithm winner, independent prospective validation or physical-phone performance is claimed.

## Dataset, scope and review

The supplied package reports adviser-directed expansion to all SMS phishing; that statement is recorded without independently verifying adviser approval. Positives describe deceptive phishing attempts; negatives are purported genuine messages. Advertising and job/loan fraud remain excluded. Eighteen excluded job/loan records have possible phishing signals and require scope adjudication; none was silently relabeled or included as ham.

The CSV matches all reported counts: **3,552 included, 468 smishing, 3,084 ham, 2,594 supplied template groups, 71 flags, and 2,272 excluded** (1,950 advertising / 322 fraud). There are no duplicate IDs, cleaned exact duplicates, conflicting redacted labels, mixed-label supplied groups or template-key mismatches. Missing sender/date values are 261/60; all prediction-text, label and grouping fields are populated. Included and excluded files have zero cleaned-exact overlap. Raw sources are absent from the ZIP, so this validates the CSV and matching source snapshots, not a reproduced original build. The unchanged original package and builder remain private.

**Used: 3,340 records (393 smishing, 2,947 ham). Held: 212** — 60 GitHub records with unresolved permission evidence, 13 team/social records with unresolved origin/consent/use evidence, and 139 automated privacy holds. No new permission or independent human annotation is inferred. All 71 flagged and 300 validation-review entries have blank labeler/final-label fields; 59 supplied flags survive in the eligible subset. Every eligible record still awaits independent label/privacy review.

| Pinned source | Used ham | Used smishing | Local research basis |
|---|---:|---:|---|
| tagalog | 2053 | 66 | ZERO v1, CC0 1.0 |
| marketing | 877 | 164 | Scott Lee Chua v15, CC BY 4.0 |
| bwandowando | 17 | 163 | BwandoWando v49, CC BY-NC-SA 4.0; noncommercial local use |

[Existing attribution/source evidence](source-evidence.md) is retained. The new view uses direct cleaned matches to pinned source copies, automated URL/email/digit minimization and conservative privacy holds. Human redaction review and original acquisition/consent are not established. No raw text, source/sender/ID/date/review metadata is supplied as a prediction feature; only redacted text is used. Package IDs are version-specific and mapped to private content fingerprints.

## Frozen partitions and exposure

| Partition | Records | Ham | Smishing | Groups | Positive groups |
|---|---:|---:|---:|---:|---:|
| train | 1860 | 1637 | 223 | 1044 | 104 |
| validation | 622 | 561 | 61 | 283 | 30 |
| calibration | 410 | 357 | 53 | 270 | 25 |
| test | 448 | 392 | 56 | 251 | 25 |

The label-blind audit merged 616 supplied groups, producing 1848 components. All six partition-pair group-overlap counts are zero. Deterministic SequenceMatcher >=0.85 and supplied-template unions reduce near-copy leakage, but cannot establish perfect semantic independence. Calibration and each evaluation partition meet the predeclared >=20 positives / >=10 positive-group floor; grouped CV fallback was unnecessary.

Exactly 1,032 eligible messages match the cleaned original-source text of the previous experiment (555 training, 159 validation, 165 calibration, 153 test); eight corresponding labels changed. The broader normalized exact/near-copy audit finds **3,269/3,340** exposed to earlier supplied training corpora or previous partitions. The 71 unmatched messages are not certified unseen. Historical full-data training membership is incomplete.

The new test has 439/448 records with detected historical overlap. New package IDs and this new split do not reset exposure. GitHub-source evaluation is held because its permitted use is unresolved.

Dataset SHA-256: `c3abc4bb23742226deab491821c1828559d895242da55267c77ae6f7dfa07b21`. Split SHA-256: `67e064af947e5194cada9facff7fa02663d02dd2fff0756acbee9c58c50c4b1f`. Cased-view SHA-256: `67300b1401200ec34e7b8ee05bf3918f7f4f04bdd8a8dbe9bde1165dca27e954`. Public fingerprints identify whole manifests; row-level membership and fingerprints remain private.

## Training and final evaluation

LR/NB/SVM reuse sg-ascii-v1 and raw-count unigram TF-IDF with smooth IDF and L2 normalization. Five grouped training folds select parameters with TF-IDF fitted afresh inside every fold. Only training records fit the final pipeline. Sigmoid calibration is fitted once on calibration records; thresholds maximize validation F1 with the predeclared tie rule. All four pipelines were frozen before opening final test predictions.

mBERT fine-tuned `google-bert/bert-base-multilingual-cased`, revision `3f076fdb1ab68d5b2880cb87a0886f315b8146f8`, matching tokenizer, new binary head, all 177,854,978 parameters trainable. Two epochs, seed 20261005, Adafactor 2e-5, batch 1 / accumulation 8, gradient checkpointing and float16 CUDA autocast; selected epoch 2 by validation AP. Checkpoints include optimizer/scaler/RNG for resumption. The training-only p95 of 151.05 tokens selected **160 tokens**: 67/1860 truncated versus 193 at 128. Training used 668.80 seconds of a 2,700-second budget, with 2,227,597,824 peak allocated CUDA bytes on the RTX 3050 Laptop 4 GiB. This is a bounded configuration, not an exhaustive BERT search.

All rows below use the identical 448 test records (392 ham, 56 smishing), 251 groups and 25 positive-bearing groups. Percentages are shown; confusion entries are counts.

| Model | Precision | Recall | Phishing F1 | Macro-F1 | Accuracy | FPR | TN / FP / FN / TP |
|---|---:|---:|---:|---:|---:|---:|---|
| Logistic Regression | 96.88 | 55.36 | 70.45 | 83.62 | 94.20 | 0.26 | 391 / 1 / 25 / 31 |
| Multinomial NB | 83.33 | 35.71 | 50.00 | 72.55 | 91.07 | 1.02 | 388 / 4 / 36 / 20 |
| Linear SVM | 98.00 | 87.50 | 92.45 | 95.72 | 98.21 | 0.26 | 391 / 1 / 7 / 49 |
| mBERT | 100.00 | 41.07 | 58.23 | 77.09 | 92.63 | 0.00 | 392 / 0 / 33 / 23 |

Linear SVM has the highest observed phishing F1 in this run. This does not establish a final winner. The older experiment has different membership, labels and scope; score differences alone cannot establish improvement. Unfavorable predictions are retained and no test-based retuning followed.

| Model | Threshold | F1 95% group interval | Brier | Log loss | Training seconds | Model bundle bytes | APK bytes |
|---|---:|---|---:|---:|---:|---:|---:|
| Logistic Regression | 0.82 | 0.5455–0.8571 | 0.02576 | 0.09309 | 1.041 | 266,600 | 12,943,387 |
| Multinomial NB | 0.63 | 0.2521–0.8090 | 0.06899 | 0.22882 | 0.939 | 261,988 | 12,943,667 |
| Linear SVM | 0.59 | 0.7755–0.9787 | 0.02403 | 0.09549 | 1.030 | 249,821 | 12,933,907 |
| mBERT | 0.89 | 0.3278–0.9020 | 0.06533 | 0.24637 | 668.797 | 712,625,479 | 1,511,956,972 |

Intervals use 2,000 group resamples, conditional on fixed fitted models. They omit fitting/selection uncertainty and multiple-comparison correction. Imperfect groups, source sampling and unconfirmed labels further limit inference. A zero-FPR sample or degenerate interval does not prove zero population false positives. Validation is reused for selection and threshold choice. Brier/log loss and [reliability plots](expanded-reliability-20261005.png) measure agreement with inherited labels, not validated real-world probabilities. Baseline CPU durations are measured; their failed process-memory probes are marked unavailable, not zero usage.

| Paired F1 difference | 95% group interval |
|---|---|
| lr-nb | -0.0460 to 0.3964 |
| lr-svm | -0.3723 to -0.0493 |
| lr-mbert | -0.1948 to 0.3450 |
| nb-svm | -0.6971 to -0.0655 |
| nb-mbert | -0.2487 to 0.0669 |
| svm-mbert | -0.0801 to 0.6331 |

Full class/group support, all metric intervals, reliability-bin counts and language/category/source breakdowns are in the [aggregate results](expanded-four-model-results-20261005.json). Subgroup metrics require >=20 records and >=5 per class, otherwise only support is reported. Languages are supplied rough guesses. Categories partly derive from label rules and are descriptive, not independent annotation.

Test breakdown by supplied language (F1 percentages):

| Subgroup | Ham / phishing | Groups | LR | NB | SVM | mBERT |
|---|---:|---:|---:|---:|---:|---:|
| English | 270 / 45 | 158 | 71.43 | 42.11 | 94.12 | 52.46 |
| Filipino/Taglish | 122 / 11 | 98 | 66.67 | 69.57 | 85.71 | 77.78 |

Test breakdown by supplied source (F1 percentages):

| Subgroup | Ham / phishing | Groups | LR | NB | SVM | mBERT |
|---|---:|---:|---:|---:|---:|---:|
| bwandowando | 0 / 44 | 16 | insufficient support | insufficient support | insufficient support | insufficient support |
| marketing | 130 / 8 | 109 | 71.43 | 77.78 | 87.50 | 93.33 |
| tagalog | 262 / 4 | 129 | insufficient support | insufficient support | insufficient support | insufficient support |

Category support is listed in the aggregate JSON; category-specific full metrics are suppressed when either class lacks the predeclared support. No category label is an input feature.

## Offline app verification and presentation

An interrupted LR verification and a stale screenshot-test model-version assumption are preserved in private logs. The harness now reads the bundled version, and final verification repeats the affected checks without changing any fitted model or research result. The minimalist UI, Model score wording, privacy controls and abstention behavior are preserved. Reporting and automatic warnings remain disabled. All APKs have no INTERNET permission, verified signatures, correct distinct package IDs and matching bundled model hashes. Old model assets, app/test APKs and rollback deliverables remain local and unchanged. The mBERT export is faithful float32 ONNX with the original multilingual architecture; there is no quantization or replacement.

| Model | Build / lint | JVM tests (skipped) | Emulator tests | Python/export parity cases | Test app coverage |
|---|---|---:|---:|---:|---|
| Logistic Regression | passed / 0 errors | 21 (3) | 25 | 461 | 448/448 |
| Multinomial NB | passed / 0 errors | 21 (3) | 25 | 461 | 448/448 |
| Linear SVM | passed / 0 errors | 21 (3) | 25 | 461 | 448/448 |
| mBERT | passed / 0 errors | 21 (3) | 24 | 468 | 448/448 |

Seventy-six research tests, eight safe-handoff tests, 20 existing model guards and six expanded-protocol guards passed. Emulator checks cover offline paste/share, actual model loading, missing/invalid models, long/empty/random inputs, English/Taglish, repeated scans, permissions and lifecycle/privacy. JVM/Android parity verifies actual fitted exports, class decisions and exactly-once calibration; mBERT additionally checks token IDs, masks, token types and full logits within predeclared tolerances. [Detailed verification](expanded-four-model-verification-20261005.json).

Classifier metrics above score every test record. App-policy coverage is separate and never credits an abstention as a correct negative. The four identical fictional benchmark probes deliberately include short text; their coverage is reported separately from research-test coverage. Actual screenshots are in local `deliverables/expanded-20261005/screenshots/<algorithm>/`, with the same fictional messages for all models.

| Model | Cold detector load ms | Warm median ms | Warm p95 ms | Scored / 200 scans |
|---|---:|---:|---:|---:|
| Logistic Regression | 260.025 | 0.302 | 0.646 | 200 |
| Multinomial NB | 232.313 | 0.286 | 0.626 | 200 |
| Linear SVM | 219.413 | 0.314 | 0.668 | 200 |
| mBERT | 8238.566 | 154.173 | 167.034 | 200 |

All four were benchmarked in one session of `SmishGuard_Comparison_API36` (API 36 x86_64, four virtual CPUs, 4096 MiB configured RAM). Host: Intel i5-11400H, approximately 24 GiB RAM, Windows 11. Airplane mode on, Wi-Fi off, one app process active, four fixed probes, 20 warmups, 200 scans. Cold detector loading is separated from warm inference; mBERT also records its internal model-copy/hash/session time. These are emulator measurements, not phone measurements. Sequential execution, OS/cache effects and one timing session limit performance comparisons. [Common-session conditions and results](expanded-four-model-benchmark-20261005.json).

Visual inspection retained the real demo outcomes: mBERT missed the fictional English phishing example (1.9% model score), while LR, NB and SVM flagged it. All four classified the benign Taglish example as non-phishing. These examples are presentation evidence, not additional evaluation data or a basis for retuning.

A final-session cold boot briefly stalled Android System UI before LR instrumentation began. Closing the stalled system interface restored the launcher; the failed startup log was preserved and the full LR verification was rerun. The common-session benchmark began only after the emulator recovered.

## Local APKs

All are under `deliverables/expanded-20261005/` and excluded from public Git. Debug signatures are for local demonstration. The four algorithm variants coexist as `ph.smishguard.lr`, `.nb`, `.svm` and `.mbert`; installing a new model variant replaces that same algorithm on the emulator, while preserved old APKs allow rollback.

| Model | APK filename | SHA-256 |
|---|---|---|
| Logistic Regression | `SmishGuard-lr-expanded-20261005-lr-c3abc4bb-experimental-debug.apk` | `3c498926bc0c281e68a5b29e05f12e5655a4a4bcc5682b5c24bf775b30c79963` |
| Multinomial NB | `SmishGuard-nb-expanded-20261005-nb-c3abc4bb-experimental-debug.apk` | `a61764d2201a111704f5338e5c9fa69cff94dfbb4223dcdc7c6fbfcf8f9ae560` |
| Linear SVM | `SmishGuard-svm-expanded-20261005-svm-c3abc4bb-experimental-debug.apk` | `a1bf985da00f21b7c91d43ce741058e17056d7fd3867fa808a750b1a3cbae03a` |
| mBERT | `SmishGuard-expanded-20261005-mbert-c3abc4bb-experimental-debug.apk` | `0ca13584fcd68d37809d33569a3e1e94aa244c569997b1911c0acb6d03be21ec` |

## Remaining human work

- Complete independent blinded label confirmation/adjudication, privacy review and semantic template review. The supplied review workbook exposes computer labels, so use a blinded copy for independent agreement measurement.
- Adjudicate the 18 excluded job/loan phishing conflicts against the supplied broad phishing definition.
- Obtain specific use/origin/consent evidence only for the held GitHub/team records if they are to enter a future experiment. No renewed project authorization is needed.
- Collect a genuinely new prospective evaluation set and measure performance on physical phones before deployment claims.

[Frozen protocol](expanded-comparison-protocol-20261005.md) · [Reproduction](expanded-comparison-reproduction-20261005.md) · [Prior preserved report](four-model-comparison.md).
