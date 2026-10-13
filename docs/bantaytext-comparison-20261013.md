# SmishGuard baseline-first BantayText experiment — 13 October 2026

**Decision: retain the active supplied model.** The grouped validation-selected research candidate is svm-C-10.0. Improvements are retrospective, with inherited labels and no genuinely unseen cohort. Its source stress results do not establish reliable deployment generalization. No app weights, inference policies, permissions, consent, receiver behavior or reporting controls changed.

The executed [notebook](../research/SmishGuard_Model_Training_and_Evaluation.ipynb) contains actual training, prediction, confusion-matrix arithmetic, tables and plots. All 62 configurations (31 per track, including diagnostics) completed; the baseline phase was frozen, tested and saved before improvements. The [CSV](bantaytext-comparison-20261013.csv) separates all 124 validation/test rows. [JSON](bantaytext-comparison-20261013.json) retains full metrics/configuration, memory/latency and subgroup counts.

## Data and leakage

The latest supplied package contains 4,261 records: 3,184 ham, 577 smishing and 500 unmapped gambling ads. Existing source/privacy rules hold 921 rows, leaving 3,340 masked fitting records. This experiment holds 59 flagged records and removes 727 masked casefold duplicates, leaving **2,554 records (2,229 ham, 325 smishing; 12.73% scam)**. No 25.5% ratio was forced. [Input/source audit](bantaytext-input-audit-20261013.json) documents source contributions, schemas, original categories, rule mappings, missing fields, placeholder counts and active-model baseline.

Pinned source snapshots contain 3,454 Tagalog-SMS, 8,895 Chua marketing and 1,021 bwandowando records. Two Chua CSV rows have extra-field overflow; the established source matcher only admits documented exact source joins. A full raw-source build cannot be reproduced because upstream package inputs are incomplete. We did not execute the supplied builder or invent permissions.

English stopword filtering does not remove po/paki/nyo/ninyo/na. The selected grouped training vocabulary includes po/na, while paki/nyo/ninyo are absent because they were not observed in that training view. This limits local coverage; these words are not hard-coded scam indicators. Unicode word TF-IDF preserves Filipino text in masked views, and character features test misspellings/obfuscation. Raw URL hosts, shorteners, sender and identifiers were masked or excluded upstream; their causal contribution cannot be recovered.

| Track | Train ham/scam | Validation ham/scam | Test ham/scam | Cross-partition template groups |
|---|---:|---:|---:|---|
| random | 1337/195 | 446/65 | 446/65 | {'train-validation': 94, 'test-train': 97, 'test-validation': 47} |
| grouped | 1345/195 | 459/57 | 425/73 | {'train-validation': 0, 'test-train': 0, 'test-validation': 0} |

The cleaned corpus has 31 template components spanning multiple sources (176 records). These potential reused messages/campaigns are grouped together; similarity is not confirmed campaign identity.

Random uses a two-step stratified 60/20/20 split, seed 42. Grouped uses 1,840 connected components and 10 stratified group folds assigned 6/2/2. Supplied template equivalence and normalized SequenceMatcher ≥.85 form label-blind edges. No grouped component crosses boundaries; this heuristic cannot establish complete campaign independence. Random and grouped test sets differ: compare conditions within each track. Dates have unverified receipt meaning/timezone, so temporal testing is unavailable. Every eligible message already had historical exposure; re-splitting does not make it prospectively unseen.

## Baseline and selected candidates

Standard baselines share unrestricted Unicode word unigrams, raw TF-IDF/smooth IDF/L2, no stopwords, seed 42. NB alpha=1; LR C=1/liblinear; LinearSVC C=1/dual=auto, no class weights. Native SVM uses margin ≥0 and ranking margins, with no probability/calibration claim. Improved SVM probabilities come from 3 training-only grouped OOF folds with fold-local TF-IDF and a sigmoid fit; calibration quality remains unvalidated.

| Track/model | Validation F1 | Test precision | Test recall | Test F1 | AP | ROC AUC | TN/FP/FN/TP |
|---|---:|---:|---:|---:|---:|---:|---|
| random/baseline-nb | 0.6598 | 1.0000 | 0.6000 | 0.7500 | 0.9464 | 0.9877 | 446/0/26/39 |
| random/baseline-lr | 0.6598 | 1.0000 | 0.6154 | 0.7619 | 0.9794 | 0.9939 | 446/0/25/40 |
| random/baseline-svm | 0.9180 | 1.0000 | 0.8923 | 0.9431 | 0.9974 | 0.9996 | 446/0/7/58 |
| grouped/baseline-nb | 0.4167 | 1.0000 | 0.4658 | 0.6355 | 0.8878 | 0.9687 | 425/0/39/34 |
| grouped/baseline-lr | 0.5750 | 1.0000 | 0.5753 | 0.7304 | 0.9512 | 0.9875 | 425/0/31/42 |
| grouped/baseline-svm | 0.8367 | 0.9683 | 0.8356 | 0.8971 | 0.9867 | 0.9976 | 423/2/12/61 |
| random/svm-combined | 0.9683 | 1.0000 | 0.9692 | 0.9844 | 0.9989 | 0.9998 | 446/0/2/63 |
| grouped/svm-C-10.0 | 0.9655 | 0.9459 | 0.9589 | 0.9524 | 0.9853 | 0.9973 | 421/4/3/70 |

Selection maximizes validation scam F1 subject to precision ≥.90 and TP≥5; ties prefer fewer serialized bytes then experiment ID. Threshold grid .05–.95 in .01 steps. Each phase saves model hashes and selection before any test transform. Tests were evaluated once per configuration; no test-driven retuning or replacement occurred. False negatives miss phishing; false positives can disrupt trust in legitimate OTP/transaction messages. The precision floor is a provisional research operating criterion, not approval for automatic warnings.

## Controlled comparisons on grouped validation

| Experiment | Threshold | Default-threshold F1 | Tuned validation F1 | Test F1 (descriptive) | Features | Pickle bytes | Train seconds | Host test ms/message |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| nb-word12-english | 0.12 | 0.8125 | 0.9027 | 0.8777 | 18473 | 1058408 | 0.067 | 0.032 |
| nb-word12-no-stop | 0.11 | 0.8041 | 0.8727 | 0.8905 | 22052 | 1242005 | 0.085 | 0.040 |
| nb-char | 0.11 | 0.8125 | 0.8824 | 0.8444 | 38000 | 1912422 | 0.317 | 0.170 |
| nb-combined | 0.17 | 0.8367 | 0.8932 | 0.8636 | 56473 | 2969558 | 0.371 | 0.200 |
| nb-alpha-0.03 | 0.14 | 0.8400 | 0.9027 | 0.8714 | 18473 | 1058404 | 0.061 | 0.031 |
| nb-alpha-0.3 | 0.12 | 0.6744 | 0.8654 | 0.8741 | 18473 | 1058403 | 0.067 | 0.031 |
| nb-alpha-1.0 | 0.10 | 0.4384 | 0.8400 | 0.8031 | 18473 | 1058403 | 0.075 | 0.030 |
| nb-word1-english | 0.26 | 0.8515 | 0.9107 | 0.8741 | 3883 | 204689 | 0.033 | 0.020 |
| lr-word12-english | 0.18 | 0.2462 | 0.8269 | 0.8060 | 18473 | 615160 | 0.095 | 0.033 |
| lr-C-0.1 | 0.19 | 0.0000 | 0.5316 | 0.6786 | 18473 | 615151 | 0.075 | 0.033 |
| lr-C-10.0 | 0.13 | 0.7473 | 0.8929 | 0.9167 | 18473 | 615152 | 0.083 | 0.034 |
| lr-balanced | 0.45 | 0.8544 | 0.8598 | 0.8444 | 18473 | 615168 | 0.077 | 0.033 |
| lr-oof-calibrated | 0.52 | 0.8269 | 0.8269 | 0.8060 | 18473 | 629039 | 0.375 | 0.033 |
| svm-word12-english | 0.38 | 0.9174 | 0.9649 | 0.9241 | 18473 | 629002 | 0.344 | 0.033 |
| svm-combined | 0.23 | 0.9273 | 0.9580 | 0.9524 | 56473 | 1628148 | 1.623 | 0.200 |
| svm-C-10.0 | 0.37 | 0.9464 | 0.9655 | 0.9524 | 18473 | 628994 | 0.382 | 0.032 |
| lr-portable | 0.87 | 0.8182 | 0.7959 | 0.8372 | 4093 | 130854 | 0.216 | 0.044 |
| lr-remove_urls | 0.17 | 0.2462 | 0.8519 | 0.8000 | 18420 | 613171 | 0.096 | 0.039 |
| lr-placeholders_only | 0.50 | 0.0000 | 0.0000 | 0.0000 | 9 | 2042 | 0.011 | 0.010 |
| lr-source_only | 0.95 | 0.5750 | 0.5750 | 0.5962 | 3 | 1793 | 0.006 | 0.004 |

Interpret these alpha/feature comparisons using validation and the same partitions. Threshold tuning is a separate changed factor; default-threshold metrics are saved alongside tuned metrics. No arbitrary feature pruning was needed for this host experiment; no phone memory/latency claim follows. Sparse matrix byte counts exclude Python object/string and runtime overhead. Pickle size is a measured research serialization size, not an Android asset size. Combined features concatenate equally weighted individually L2-normalized word and char blocks. Source-only and URL/placeholder ablations are prespecified diagnostics, excluded from model selection. Source prevalence is strongly confounded: the cleaned bwandowando source contains only positive labels.

## Errors and targeted legitimate-message evaluation

Targeted categories join original metadata by ID only **after selection**, without changing text, labels, partitions or fitted parameters. Category membership comes from original source categories; binary ham labels remain inherited and unverified. Bank/e-wallet notifications are not separately validated, and the broad `notifs` category must not be presented as bank-specific. No confirmed-malicious category is claimed.

| Track/category | Ham support | Smishing support | False positives | FPR |
|---|---:|---:|---:|---:|
| random/otp | 33 | 0 | 0 | 0.0000 |
| random/gov | 21 | 0 | 0 | 0.0000 |
| random/ads | 190 | 0 | 0 | 0.0000 |
| random/notifs | 202 | 0 | 0 | 0.0000 |
| grouped/otp | 55 | 0 | 0 | 0.0000 |
| grouped/gov | 21 | 0 | 0 | 0.0000 |
| grouped/ads | 176 | 0 | 3 | 0.0170 |
| grouped/notifs | 173 | 0 | 1 | 0.0058 |

Rates are descriptive and suppressed below 20 relevant-class records, not statistically powered guarantees. Private error ledgers contain row indices and predictions only. No SMS text is emitted publicly. The grouped selected model has 4 FP and 3 FN; its English subgroup has 284 ham/63 smishing with 4 FP/2 FN, and Filipino/Taglish has 141 ham/10 smishing with 0 FP/1 FN. The latter FNR is suppressed because its positive denominator is below 20. URL-removal stress and source/category counts are in JSON. No test-derived data correction or feature retuning was performed.

| Held source (diagnostic) | Test records | F1 | Recall |
|---|---:|---:|---:|
| bwandowando | 128 | 0.8821 | 0.7891 |
| marketing | 1002 | 0.9371 | 0.9306 |
| tagalog | 1424 | 0.3509 | 0.9434 |

Each source stress fit excludes that source and every overlapping template group. Settings and threshold remain fixed from main grouped validation, which included the source earlier; these post-selection diagnostics are not an unbiased nested source-holdout estimate. The weak Tagalog result, source imbalance, inherited labeling rules and historical exposure prevent a reliable deployment-winner claim.

## Android/model handoff

The active supplied schema-2 LR remains byte-identical. Its full-training-corpus resubstitution baseline is separately labeled in the input audit and must not be compared with held-out candidate metrics. Exact original artifact training reproduction remains unresolved despite supplied procedure evidence. Existing score presentation is an uncalibrated model score, not fraud probability; prior automatic-warning behavior and disabled reporting are preserved.

The selected research SVM uses Unicode English-stopword word bigrams and training-OOF calibration, which the current Android word-unigram contract cannot consume. Its private pipeline stores the exact ordered vocabulary, IDF, class order [0,1], coefficients, calibration and validation threshold. Independent labels, unseen evaluation and a separately reviewed native feature contract are needed before integration. Do not silently truncate features or substitute preprocessing.

A separately fitted portable LR comparator exports the existing schema-1 contract for parity only: ASCII word unigrams, raw TF-IDF, exact ordered vocabulary/IDF, L2, class [not_suspicious,suspicious], inclusive threshold and a fitted training-OOF sigmoid with calibration_evaluated=false. Python and JVM fixed synthetic probes agree within 1e-10. Empty/oversized comparator inputs fail; unknown/malformed input scores remain explicitly non-probability. The comparator is not installed or approved. Active-model safe probes include legitimate-style OTP/bank/e-wallet, Taglish, malicious-style, empty, malformed, URL-only and random text; these are software checks, not accuracy labels.

Verification: 62 test metric records independently recomputed; 18 notebook code cells executed without errors; 11 protected app/model hashes unchanged. JVM: 34 tests, 0 failures, 0 errors, 4 conditional skips. Active parity: 16 probes, max score error 5.55e-17, 7 required abstentions. Assemble/lint/JVM development checks passed. No emulator or physical-device testing was performed in this task.

Vocabulary coverage and score-reliability bins/ECE are in JSON. Coverage counts analyze held-out word features against training vocabulary without fitting on held-out messages; low support and masked text limit interpretation. Reliability is retrospective under inherited labels, not a risk-percentage validation.

See [reproduction and test report](bantaytext-reproduction-20261013.md) and [research candidate model card](bantaytext-model-card-20261013.md). Public outputs contain aggregate metrics only. Fitted artifacts/vocabulary, row membership and datasets stay in ignored research storage. The first execution failed on record copying before training, was fixed and retained privately; the complete delivered run is notebook-run-v3, including original-category targeted notebook outputs.
