# Retrained NB Android integration — 20 October 2026

The `nbGeneralization` Android variant loads the freshly retrained **original-alpha-0.1** Multinomial Naive Bayes pipeline from `group-fold-0` of the [generalization audit](nb-generalization-20261019/RESULTS.md). This is the predeclared first fold, selected independently of model scores. It uses 2,734 training messages and reserves 684 messages for testing. The APK does not refit on the entire corpus or combine the five models.

The exact fold's retrospective test accuracy is **97.22%**, scam precision **100.00%**, recall **73.97%**, and F1 **85.04%** (611 TN, 0 FP, 19 FN, 54 TP). The **98.07% accuracy / 90.00% F1** previously reported pools predictions from five separately fitted folds; it is not a separate measurement of this single APK model. Inherited labels, historical corpus exposure, and weak source-held-out results remain limitations. Packaging does not establish generalization or probability calibration.

## Model contract

The native scorer retains the frozen Python Unicode 15.0 lowercase tables, Unicode whitespace normalization, prioritized URL/currency/number/word tokenization, the same 13 stopwords, unigrams and bigrams, raw term counts, fitted IDF and L2 normalization. It keeps URLs and amounts intact. No raw-SMS masking adapter is applied. The 37,279 feature weights are the difference between the two NB class log probabilities; the bias is the difference between the fitted log priors. A stable sigmoid produces the same uncalibrated NB score, with an inclusive 0.5 decision threshold.

The tokenizer scans Unicode codepoints explicitly. This avoids Java/Android regex lookbehind differences after supplementary characters. It preserves Python's numeric-regex backtracking and exact URL punctuation semantics. The mathematical score path is tested independently of app abstention. The app abstains on unknown, numeric-only, or link-only content and rejects invalid or oversized input.

The existing consent-controlled incoming SMS behavior, manual/share flow, sender-blocking handoff and risk presentation remain available. The visible risk score uses the existing evidence index combining model signal with message indicators; it is not the NB probability or accuracy. The build remains experimental and reporting remains disabled.

| Identity | Value |
|---|---|
| Build type | `nbGeneralization` |
| App label | Veritxt · Retrained NB |
| Application ID | `ph.smishguard.nb.generalization` |
| Version | `0.3.0-nb-generalization-experimental` |
| Minimum Android | 8.0 / API 26 |
| Compile / target | API 36 |
| Signing | Local Android debug certificate |
| Source pipeline SHA-256 | `ec8e1b07515d19defc71f6712b7bebb3fa26c1a87cfbd1ef03d5e608be7ed14c` |
| Native model SHA-256 | `7cd219db2c9c4559aec60fdea2558821e48cc73085455a9c9caf0b5465d9df5c` |

The app installs beside the earlier Linear SVM package. A Gradle guard pins the model hash and forbids a shared model asset. Model assets, APKs and raw-message parity fixtures remain private and ignored by Git. Only the model parameters belong in the app APK; the 1,837 parity examples belong in the separate test APK.

## Reproduce locally

Private frozen artifacts are required. Use a new output directory for each export:

```powershell
research/.venv/Scripts/python.exe scripts/prepare_nb_generalization_apk.py --output research/runs/nb-apk-20261020/export-v1
$nbParityPath = (Resolve-Path research/runs/nb-apk-20261020/export-v1).Path
./scripts/build.ps1 -Variant nbGeneralization -NbParityDir $nbParityPath -EmulatorTests
research/.venv/Scripts/python.exe scripts/package_nb_generalization.py --export research/runs/nb-apk-20261020/export-v1 --emulator-evidence docs/nb-generalization-emulator-results.json
```

`-EmulatorTests` requires a booted emulator and refuses a physical device. The verifier exercises native score/feature/token parity against the saved sklearn pipeline, real app loading, share-to-check, privacy/lifecycle, incoming modem SMS and accessibility. APK signature, package identity, embedded model hash and absence of raw fixtures are verified separately before delivery. Verification evidence is recorded with the delivered APK.

## Completed verification

- APK assembly and Android test APK assembly passed. Lint reported 0 errors and 11 warnings (dependency/target updates, locale configuration and an unused resource).
- JVM: 49 tests discovered, 39 passed, 10 skipped because other variants' private model fixtures were not supplied; no failures. The new NB parity test ran and passed.
- API 36 emulator: 26 instrumentation tests passed, including the actual bundled NB loader, all 684 app assessment paths, shared-message results, clipboard/manual checks, privacy, modem SMS, actual-model automatic warning, notification permission/channel states and large-text accessibility.
- Python/JVM/Android parity: **1,837 cases**, comprising all 684 held-out messages, all vocabulary terms in probe batches, ordinary/scam examples, Unicode edge cases and seeded tokenization probes. Maximum feature error **8.89e-16**; maximum score error **2.05e-14** (upper-rounded). All held-out messages were assessed; native decisions matched Python.
- Emulator model load: 422 ms; scoring median 0.647 ms, p95 1.652 ms across the parity cases. These are emulator measurements, not phone benchmarks.
- The APK has one asset, `assets/model.json`, with the pinned hash above. No raw parity messages, datasets, pickles or test APK are included. The package declares SMS/notification permissions and no Internet permission. The Android v2 APK signature verifies.
- No physical-device test was performed. The temporary headless emulator was used only for software verification.

Delivered file: `deliverables/Veritxt-Retrained-NB-20261020/Veritxt-0.3.0-Retrained-NB-80-20.apk` (21,859,816 bytes).

APK SHA-256: `f1dd903e8696267e176904884bbe83a00158cba185080a8a459f4b7d911e1804`.

See [sanitized emulator evidence](nb-generalization-emulator-results.json). The delivery directory also contains the checksum and build manifest. Raw fixtures and detailed local build logs remain under ignored `research/runs/nb-apk-20261020/`.
