# SmishGuard preliminary comparison

This is a development demonstration with inherited/AI-assisted labels awaiting human confirmation. It is not a final thesis evaluation. The internal test messages were previously exposed; mBERT was added after the three baseline results were viewed. There is no independent prospective test, adviser scope approval, or predetermined winning algorithm.

## Records, permission evidence and scope

The supplied `smishguard_PRIVATE_data (1).zip` and `HANDOFF (1).md` were available and reconciled locally. The primary file has 1,276 rows; this experiment includes **1,068** and holds **208**: 83 personal/social/UCI records, 96 without a supported source match, 11 automated privacy holds, and 18 normalized duplicates. All 1,050 everyday-ham supplementary rows and all 417 reviewed-addition rows remain excluded. Exact/whitespace matches exist for 823 and 265 of those supplementary rows respectively, but this does not admit them to the already frozen experiment. The addition file overlaps one selected normalized message. No new records, labels or partitions were added for mBERT.

Text was drawn directly from hash-pinned source copies: ZERO (onzero0), *Tagalog SMS*, version 1, CC0 1.0; Scott Lee Chua, *PH Spam + Marketing SMS with Timestamps*, version 15, CC BY 4.0. Exact/whitespace source joins transfer the supplied labels, not permissions or human review. Attribution and source fingerprints are in [source evidence](source-evidence.md) and the aggregate manifest. These license observations support this bounded source-based development subset; they do not attest the original acquisition chain, donor consent, or final thesis eligibility. The user authorized preliminary development with inherited/AI-assisted labels. That decision is not adviser approval or confirmation of permissions for held records. Existing pending review fields were preserved. Both supplied human-review packets have zero completed decisions (65 primary and 605 addition review rows).

The implemented target remains the inherited binary ham/smishing labels, including inherited casino-ad positives. Whether institution-branded casino advertising belongs in the thesis phishing definition remains unresolved. Historical screenshot claims that SVM won conflict with the handoff's rejection of that SVM run; they are not reproduced findings. No fitted NB/SVM pipeline was found in the inspected supplied artifacts. The historical `lr-calibrated-4` is a separate full-data candidate, not the LR baseline in this comparison. Its 2,738-row training claim is not the membership of this 1,068-row experiment. See the earlier LR4 audit for folded calibration and vocabulary findings.

| Partition | Records | Ham | Smishing | Template groups |
|---|---:|---:|---:|---:|
| Training | 574 | 513 | 61 | 424 |
| Validation | 163 | 143 | 20 | 127 |
| Calibration | 172 | 158 | 14 | 128 |
| Exposed internal test | 159 | 132 | 27 | 126 |

Dataset SHA-256: `1d62dc1a25d86eeead92ec88109cfdd12d235edef596b51b969cb9a61f80a408`.
Grouped split SHA-256: `12f62d292dc9b4948faa755eedb79fcc499ba32e69c700a38f39f4dfce16339d`.
mBERT case-preserving redacted view SHA-256: `84ac296cd927491a526bb97ba02795bd49237f99faca98f870d9fc7a3da84537`.
All 1,068 IDs and labels match; normalizing each case-preserving view reproduces its frozen baseline text. mBERT receives native cased WordPiece inputs, not TF-IDF.

## Training and evaluation

The fresh LR, Multinomial NB and Linear SVM use identical `sg-ascii-v1` preprocessing, raw-count unigram TF-IDF with smooth IDF and L2 normalization, 2,008 final training features, grouped folds and partitions. TF-IDF is fitted inside each training fold. Five-fold development selection (seed 20260929) selected LR C=10, NB alpha=0.1 and SVM C=10. Each fitted a sigmoid only on the calibration partition, with thresholds selected on validation: LR 0.74, NB 0.30, SVM 0.4099999999999999. The exported SVM preserves its decision margin and applies its separately fitted calibrator exactly once; margins are not directly displayed as percentages. No full-data refit or test-based selection occurred.

mBERT follows the separately frozen [exploratory protocol](mbert-exploratory-protocol-20261002.md). Base `google-bert/bert-base-multilingual-cased`, revision `3f076fdb1ab68d5b2880cb87a0886f315b8146f8`, matching tokenizer, new binary head, all parameters trainable. Two epochs, seed 20261002, Adafactor at 2e-5, batch 1 with eight-record accumulation, CUDA float16 autocast and checkpointing, at most 45 minutes. Maximum length comes only from training lengths, epoch selection from validation AP, sigmoid from calibration data, threshold from validation F1. This low-resource setup is one exploratory configuration, not a claim of optimal BERT training.

All four models were trained and evaluated. mBERT completed two epochs in 299.781 seconds on the RTX 3050 Laptop, with 177,854,978 trainable parameters and 2,227,494,912 bytes peak CUDA allocation. Validation AP rose from 0.6779 to 0.7845, selecting epoch 2. The training-only length rule selected 128 tokens; 103/574 training messages were truncated. Its validation-selected threshold is 0.09, applied to `sigmoid(1.9890286443665295 × (logit1 − logit0) + 9.645893735282968)`, exactly once. No test-based adjustment followed. Baseline training duration was not captured separately and is not inferred from file timestamps.

All rows below use identical 159 test IDs (132 ham, 27 smishing) and the dataset/split fingerprints above. Values are percentages; confusion entries are counts.

| Algorithm / model ID | Trained / evaluated | Precision | Recall | Phishing F1 | Macro-F1 | FPR | TN / FP / FN / TP | APK |
|---|---|---:|---:|---:|---:|---:|---|---|
| LR / `prelim-20261001-lr-1d62dc1a` | Yes / yes | 100.00 | 74.07 | 85.11 | 91.26 | 0.00 | 132 / 0 / 7 / 20 | Built, verified |
| NB / `prelim-20261001-nb-1d62dc1a` | Yes / yes | 96.15 | 92.59 | 94.34 | 96.60 | 0.76 | 131 / 1 / 2 / 25 | Built, verified |
| SVM / `prelim-20261001-svm-1d62dc1a` | Yes / yes | 100.00 | 81.48 | 89.80 | 93.97 | 0.00 | 132 / 0 / 5 / 22 | Built, verified |
| mBERT / `mbert-exploratory-20261002` | Yes / yes | 88.89 | 88.89 | 88.89 | 93.31 | 2.27 | 129 / 3 / 3 / 24 | Built, verified |

NB has the highest observed F1 in this run. This is not a final algorithm winner: the labels, scope and groups await review, messages were exposed, and mBERT is a later exploratory addition. Preserve the results regardless of ranking.

Research metrics score every test message; app abstention is reported separately and is never counted as a correct negative. Calibration diagnostics describe these exposed inherited labels, not independently validated real-world probabilities. The small calibration set has only 14 positive records; reusing validation for checkpoint and threshold selection adds selection uncertainty.

| Algorithm | F1 95% group-bootstrap interval | Brier | Log loss | ECE (10 equal-width bins) |
|---|---|---:|---:|---:|
| LR | 0.5556–0.9565 | 0.01761 | 0.06904 | 0.03048 |
| NB | 0.8125–1.0000 | 0.01587 | 0.06566 | 0.02353 |
| SVM | 0.6897–0.9796 | 0.02796 | 0.10544 | 0.07320 |
| mBERT | 0.6957–0.9678 | 0.04613 | 0.16772 | 0.05474 |

Paired F1 difference intervals use 2,000 common template-group resamples, seed 20260929: LR−NB [−0.3297, −0.0014], LR−SVM [−0.1974, 0.0000], LR−mBERT [−0.2407, 0.0606], NB−SVM [−0.0294, 0.1981], NB−mBERT [−0.0393, 0.2143], SVM−mBERT [−0.1609, 0.1739]. These are descriptive marginal intervals conditional on fixed models; no fitting uncertainty or multiple-comparison correction is covered. Imperfect template groups and source sampling also limit interpretation. A degenerate zero-FPR interval does not prove zero population false positives. Full precision, per-metric uncertainty and reliability-bin counts are in [aggregate results](four-model-results.json); private paired predictions are retained outside Git.

## Software evidence and artifacts

The three completed APKs are preserved under local `deliverables/comparison-20261001/`, with distinct `ph.smishguard.lr`, `.nb`, `.svm` IDs and the shared minimalist UI. Full identities, hashes, model sizes and checks are in [three-model verification](preliminary-three-model-verification.json). Each passed build/lint, 18 JVM tests (2 unrelated private-candidate tests skipped), and 25 specialized API-36 emulator tests. Actual trained exports passed 172 Python/JVM/Android parity cases each: 165 scored, 7 abstained; maximum score errors below 4e-15 and margin errors below 5e-14. All 159 internal test messages passed the app input policy.

The first LR emulator run exposed a numeric-only abstention defect. Reserved redaction placeholders no longer count as meaningful words. That failure is retained privately; after correction all three APKs were rebuilt and passed. This changed no fitted scores, partitions or reported research predictions.

Each app was exercised with paste/share, offline scanning, empty/random input, English/Taglish examples, repeated scans, failed/missing models, lifecycle/privacy, permissions and large-text UI checks. Twelve actual screenshots use fictional messages and actual bundled inference. No physical-device testing is claimed. Reporting and automatic warnings remain disabled; no APK has INTERNET permission. The historical LR4 rollback APK is unchanged, SHA-256 `5f50dad2a92b601af810f189ec3c233e35a12821cb4d8b029a5cfa3efe6609ef`.

mBERT passed build/lint (0 errors, 5 dependency-version warnings), 18 JVM tests (3 unrelated private-parity tests skipped), and 24 specialized emulator tests. Its native cased tokenizer exactly matches Python IDs, masks and type IDs on 179 cases. Full float32 ONNX Runtime 1.22.0 on Android agrees with the selected Python checkpoint: maximum logit error 6.79493e-6, margin error 1.10865e-5 and calibrated-score error 1.52098e-6, within the declared 1e-4/1e-4/1e-5 tolerances. No classification changes; zero reference scores within 1e-5 of threshold; nearest distance 0.00227296. All 159 test messages and 20 additional probes were checked, including multilingual, special-token and long-input cases. No quantization or smaller model substitution was used. [Full mBERT verification](mbert-verification.json).

The first export check failed because the export wrapper restored training mode on the Python reference model, re-enabling dropout. Setting the wrapper to evaluation mode fixed the reference; the research metrics and frozen selected weights were preserved. Failed diagnostics are retained privately. The first emulator lacked installation storage; its artifacts were preserved and a separate `SmishGuard_Comparison_API36` emulator was created with 4 virtual CPUs, 4096 MiB configured RAM and a 12 GiB data partition. mBERT then installed and passed. This is a substantial local model: its APK is 800,401,584 bytes, with an unquantized 711,555,082-byte ONNX graph plus tokenizer, metadata and native runtime. Resource requirements on physical phones remain unmeasured.

The synthetic Taglish demo receives a positive mBERT decision in the captured screenshot; it is preserved as an illustrative false positive, not relabeled or hidden. The classifier uses the validation-selected 0.09 threshold, so a displayed score below 50% can still receive a positive decision. No settings were changed after seeing this demonstration.

Baseline latency conditions: same x86_64 API-36 emulator, four virtual cores, 2 GiB guest RAM, Intel i5-11400H host, approximately 24 GiB host RAM. Four identical fictional inputs, 20 warmups and 200 scans; 150 scored and 50 abstained. Model loading and UI rendering excluded. LR median/p95 0.3456/0.8364 ms; NB 0.3917/1.3334 ms; SVM 0.3246/0.7728 ms. These are emulator measurements, not phone performance or all-positive inference timing.

On 4 October all four preserved APKs were installed side by side and measured in the **same session of the larger comparison emulator**, with airplane mode on, Wi-Fi off and only one app process active at a time. The same four probes, 20 warmups and 200 scans produced 150 scores and 50 abstentions for every algorithm. This separates app-policy coverage (75% of these deliberately mixed probes) from research-test coverage (159/159 for each model). [Recorded common-device results](four-model-device-benchmark.json):

| Algorithm | Median scan ms | p95 ms | Android model bundle bytes | APK bytes |
|---|---:|---:|---:|---:|
| LR | 0.315210 | 0.971249 | 133,390 | 12,981,599 |
| NB | 0.368488 | 1.106410 | 130,956 | 12,941,707 |
| SVM | 0.654528 | 1.732461 | 126,557 | 12,937,536 |
| mBERT | 139.024904 | 160.072064 | 712,593,617 | 800,401,584 |

Model bundles include all asset files, including vocabulary and metadata. Separate complete research pickles are LR 90,056, NB 138,300 and SVM 90,017 bytes; the selected mBERT checkpoint/tokenizer directory totals 715,361,006 bytes. mBERT's measured load was 9,830.424 ms in the common-session run (4,562.895 ms in the earlier full verification); loading is excluded from scan timing. Host CPU testing, Android CPU inference, and CUDA training are different conditions. The latency sample is one sequential emulator run, with host/OS/cache variability and no performance confidence interval; it does not establish physical-device timing or a stable sub-millisecond ordering among baselines. mBERT's 179-case Android parity check also passed again in this session.

## Local APK identities

All files below are under local `deliverables/comparison-20261001/` and excluded from Git. They coexist as `ph.smishguard.lr`, `.nb`, `.svm` and `.mbert`. Signatures, bundled-model identities, permissions and SHA-256 were checked. Debug signatures are for local demonstrations.

| Algorithm | APK filename | SHA-256 |
|---|---|---|
| LR | `SmishGuard-lr-prelim-20261001-lr-1d62dc1a-experimental-debug.apk` | `7f6ce7c5b59bc4729ca6ac9492f4882e0f216bceaa46090ed05a0389540baff5` |
| NB | `SmishGuard-nb-prelim-20261001-nb-1d62dc1a-experimental-debug.apk` | `7e926826d421e98fe8f177b32f53ec06b54b6917b988ce07955fdb6d2b4ac94b` |
| SVM | `SmishGuard-svm-prelim-20261001-svm-1d62dc1a-experimental-debug.apk` | `8a3fe5492e654fbb5ea82bb87ee514a18b7231990787aa55699c6b61a3119d73` |
| mBERT | `SmishGuard-mbert-exploratory-20261002-experimental-debug.apk` | `5a898829f674af7f2a9958630367d6a12a28c127a8146bbbbf6c267c3b65a075` |

The Python suite passed 70 research tests; unchanged backend behavior passed 46 tests. Eight safe-handoff checks and 20 isolated model-build guards passed. The public commit contains source, tests, dependency pins and sanitized aggregates only. Fitted weights, predictions, private test fixtures and all APKs remain local.

## Remaining research requirements

Independent human label confirmation/adjudication, human privacy and template-group review, adviser resolution of casino/marketing scope, and a genuinely new prospective evaluation remain pending. Held-source records require specific acquisition/use evidence before any separate future experiment; they are not needed for this frozen subset. The source-supported subset is below the existing final-protocol 1,200-record intake requirement; the new development protocol does not bypass or alter that guard. Physical-device performance and deployment eligibility remain pending. Software parity and fitted calibration do not resolve these research requirements.

See [reproduction and demonstration](four-model-demo.md) for commands, private artifact locations and an identical-message walkthrough.
