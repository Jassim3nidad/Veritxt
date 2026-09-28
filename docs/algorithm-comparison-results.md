# Algorithm comparison preparation — 29 September 2026

**No winning algorithm is established.** The team confirmed the documented pending-data status and instructed that no new research models be trained. Logistic Regression has not been shown to perform best on phishing F1, precision, recall, FPR or calibration under the new fair protocol. Historical supplied result tables are not substituted for a shared, eligible, unseen-test comparison.

## Thesis comparison table

All entries below refer to the planned common-data experiment, not the older supplied LR or synthetic fixtures. Pending is missing evidence, not zero performance.

| Algorithm | Phishing precision | Recall | F1 (primary) | FPR | TN/FP/FN/TP | Calibration and uncertainty | Reviewed comparison model |
|---|---|---|---|---|---|---|---|
| Logistic Regression | Pending | Pending | Pending | Pending | Pending | Pending | Not trained |
| Multinomial Naive Bayes | Pending | Pending | Pending | Pending | Pending | Pending | Not trained |
| Linear SVM + fitted sigmoid | Pending | Pending | Pending | Pending | Pending | Pending | Not trained |

Interpretation: current evidence is insufficient for an algorithm ranking. Android/Python parity establishes implementation agreement, not detection accuracy. The old full-data LR cannot be evaluated as an unseen model simply by repartitioning its training corpus. No model score in the app is a validated chance of fraud.

The [pre-training protocol](algorithm-comparison-protocol.md) fixes eligibility, group assignments, training-only vocabulary/IDF, equal tuning budgets, independent calibration, validation threshold selection, final evaluation of all three frozen candidates, paired uncertainty and implementation constraints. The [review checklist and commands](comparison-data-review.md) identify the exact pending work. A complete approved-data run and deployment abstention-coverage evaluation remain unexecuted.

## Private Android deliverable

The new algorithm variants share the existing minimalist Compose screens/theme unchanged. IDs are ph.smishguard.lr, ph.smishguard.nb and ph.smishguard.svm; launcher names identify the algorithm. All are experimental debug build types. Build guards reject missing/changed models, wrong algorithm tags and synthetic or raw-margin exports. Runtime enforces the manual-only experimental policy and abstention. The historical supplied LR is a pinned schema-v2 exception, not the new comparison baseline.

| APK filename | Algorithm | Model version | SHA-256 | Model included / experimental | Minimum Android | Verification |
|---|---|---|---|---|---|---|
| SmishGuard-lr-supplied-lr-0.2.0-historical-experimental-debug.apk | Logistic Regression | supplied-lr-0.2.0-historical | `62f1a7c96b4bbd59d95f9c6ab1f73aba27d3d2dbea1c7b3c43c774c0ca6526f0` | Yes / yes | 8.0, API 26 | Build, lint, JVM, API 36 ordinary/specialized and API 26 focused checks passed |
| Not built | Multinomial Naive Bayes | None reviewed | N/A | No APK | Configured API 26 | Interface and fixture parity pass; build rejects missing model |
| Not built | Linear SVM | None reviewed | N/A | No APK | Configured API 26 | Interface and fixture parity pass; build rejects missing model |

Private local location relative to the repository: `deliverables/algorithm-comparison-20260929/SmishGuard-lr-supplied-lr-0.2.0-historical-experimental-debug.apk`. Its adjacent `lr-apk-manifest.json` records complete metadata. Both stay ignored. Share the APK only through the team's private channel; it contains the historical model whose public redistribution remains unresolved. Do not upload it to GitHub releases/issues or a public source archive.

APK inspection passed: exact model/review hashes; only model.json and review.properties in assets; no datasets, fitted pickle/joblib or software test fixtures; expected application ID, API 26 minimum, permitted permissions and valid APK signature. No INTERNET permission was added. Reporting, automatic model warnings, preferences, backups and message lifecycle policies remain unchanged. ph.smishguard.lr coexists with ph.smishguard.dev on API 36. The ordinary model-free debug APK was rebuilt for regression checking and is not the model-bearing deliverable.

## Engineering measurements, not research results

| Artifact | Portable model size | APK size | Warm scan p50 | Warm scan p95 | Scope |
|---|---:|---:|---:|---:|---|
| Historical experimental LR | 438,618 bytes | 12,981,599 bytes | 0.5228 ms | 1.8985 ms | SmishGuard_Test_API36 x86_64 emulator, debug build; four invented probes, 20 warmups, 200 sequential scans, model load excluded |
| New LR / NB / SVM comparison models | Pending | Pending | Pending | Pending | No new models trained or reviewed |

Timing includes the manual detector/abstention path and inference, excluding UI rendering, model loading and assertion/report checks. It does not characterize long messages, cold startup, physical devices, battery use or real-world accuracy. [API 36 aggregate evidence](comparison-lr-emulator-results.json) records the benchmark and software outcomes.

## Exact checks and limitations

| Check | Passed | Failed at final check | Skipped / caveats |
|---|---:|---:|---|
| Python research software suite | 51 | 0 | 0; only synthetic/test data; dependency check passed |
| Safe source/evidence checks | 8 | 0 | 0 |
| Isolated Gradle model guards | 9 | 0 | All three variants tested for missing, altered and wrongly labeled assets |
| LR JVM tests | 12 | 0 | 1: real newly trained export unavailable |
| Model-free debug JVM tests | 12 | 0 | 1: same unavailable real export |
| LR and model-free debug assembly | 2 builds | 0 | NB/SVM model-bearing assembly intentionally blocked |
| LR and debug lint | 2 runs | 0 errors | Five warnings per run: old target API, two Compose BOM and two Lifecycle update notices; pinned stack preserved |
| API 36 ordinary instrumentation | 22 | 0 | 6 setup-dependent tests; all exercised successfully in specialized suite |
| API 36 specialized instrumentation | 27 | 0 | 0; includes offline parity, real-model policy/latency, UI/lifecycle, modem fixture, notification suppression and large text |
| API 26 focused instrumentation | 4 | 0 | 0; offline historical-model parity, invalid models, share flow and large-text accessibility; [evidence](comparison-lr-api26-results.json) |
| API 36 storage marker inspection | Passed | 0 | Two app files inspected; zero fixture markers; bounded check, not forensic erasure proof |

Ordinary-suite skips were ComparisonRuntimeTest.bundledModelOfflinePolicyAndWarmLatency, ModemSmsTest.modemDeliveryMultipartConsentAndSyntheticSuppression, both NotificationBehaviorTest methods, OfflineModelTest.exportedSklearnModelsRunOfflineAndStaySynthetic and SuppliedModelTest.offlinePythonParityAndDevelopmentPolicy. They require explicit radio/modem/permission setup; the specialized verifier provided it. JVM ExportParityTest.realExportMatchesFrozenPythonPipeline remains skipped because no new eligible trained export exists. Existing LR/NB/SVM golden fixtures passed both Python arithmetic and JVM/Android parity at 1e-10 tolerance; the historical LR passed its separate Python reference fixtures on Android.

Failures encountered and resolved: the first Gradle configuration failed on a Properties import; two new JVM tests initially lacked their fixture resource directory. Both were corrected and passed on rerun. The first API 36 ordinary run had 20 passes, two failures and six skips: AccessibilityTest and clipboardPasteWorksWithoutSmsPermission failed while an emulator System UI ANR dialog held focus. The observed dialog was closed; no app UI or test assertions were weakened. The complete rerun passed 22 with six expected skips, followed by all 27 specialized tests. A packaging recheck exposed Windows' default text encoding; explicitly reading the Unicode model as UTF-8 resolved it. Earlier emulator/build failure logs remain local under research/runs.

Physical-device install/latency, battery and vendor behavior remain untested. The previously reported Xiaomi secure-FRP installation restriction is not bypassed. Broader Android versions, prospective calibration, eligible-data training, final comparative metrics, uncertainty, new model vocabulary/privacy review and public model redistribution remain pending. Successful engineering checks are not thesis performance evidence or approval for reporting/automatic warnings.
