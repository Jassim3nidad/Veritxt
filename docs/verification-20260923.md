# Verification on 23 September 2026

This record separates software verification from research evidence. Source implementation commit: `314a5d8` on `codex/thesis-completion-package`. The companion `verification-20260923.json` records environment, manuscript input hashes, artifact hash, exact JVM counts and the intermediate failure. Dates use Asia/Manila; raw tool timestamps can be 22 September UTC. No physical phone was connected or installed by this pass.

## Commands and results

Environment: Windows, repository Python 3.12 environment with pinned requirements, Temurin JDK17.0.16, Gradle8.13, AGP8.13.2, compile/target SDK36, minimum26, Build Tools35.0.0. Set `PYTHONPATH=research` for module commands. For Gradle set `JAVA_HOME` as in the reproducibility guide and `JAVA_TOOL_OPTIONS=-Djdk.net.unixdomain.tmpdir=C:/sg-nonexistent-socket-dir`. Put SDK platform-tools on PATH for emulator verifiers.

| Exact command from repository root | Actual outcome |
|---|---|
| `git status --short`; `git branch --show-current`; `git remote -v`; `git log -5 --oneline`; `git fetch --all --prune` | Initially clean `main` at `c0623c8`; origin is existing SMISHGUARD GitHub repository; no incoming co-developer commits |
| `research\.venv\Scripts\python.exe -m unittest discover -s research/tests -v` before edits | 30 passed, 0 failed, no skips |
| `research\.venv\Scripts\python.exe scripts/verify_research.py` after changes | 38 passed, 0 failed, no skips; `pip check`: No broken requirements found; synthetic fixtures only |
| `research\.venv\Scripts\python.exe -m unittest discover -s research/tests -p test_completion.py -v` after manifest eligibility refinement | 8 passed, 0 failed; included in the 38-test final suite, not additional unique tests |
| `.\scripts\build.ps1 -Variant development` initial baseline | Build/lint/unit tasks successful; most were cached, therefore not described as fresh execution |
| `.\gradlew.bat :app:testDevelopmentUnitTest :app:lintDevelopment :app:assembleDevelopment :app:assembleDevelopmentAndroidTest -PinstrumentedBuild=development --rerun-tasks --console=plain` | BUILD SUCCESSFUL, 87 tasks executed; JVM 6 passed, 1 skipped, 0 failures/errors; lint 0 errors, 5 warnings |
| `.\gradlew.bat :app:assembleDebug :app:testDebugUnitTest :app:lintDebug --console=plain` | BUILD SUCCESSFUL; model-free variant; JVM 6 passed, 1 skipped, 0 failures/errors; lint 0 errors, 5 warnings |
| `.\scripts\build.ps1 -Variant development -EmulatorTests` on dedicated API36 AVD | Final full run 16 passed, 0 failed/skipped; fixture-marker storage check passed; intermediate failure disclosed below |
| `research\.venv\Scripts\python.exe scripts/emulator_api26_verify.py` on dedicated API26 port5556 | Final focused run 4 passed, 0 failed/skipped; offline parity/model rejection plus manual share/accessibility; not an API26 carrier/SMS suite |
| `.\gradlew.bat :app:dependencies --configuration developmentRuntimeClasspath --console=plain` | Dependency graph resolves; BUILD SUCCESSFUL. No external vulnerability-database scan performed |
| SDK35.0.0 `apksigner.bat verify --verbose --print-certs android/app/build/outputs/apk/development/app-development.apk` | Verifies; v2 true; one Android Debug RSA2048 signer. Not production signing |
| SDK35.0.0 `zipalign.exe -c -P 16 4 android/app/build/outputs/apk/development/app-development.apk` | Exit0 |
| SDK35.0.0 `aapt.exe dump permissions android/app/build/outputs/apk/development/app-development.apk` | RECEIVE_SMS, POST_NOTIFICATIONS and AndroidX internal receiver permission only; no INTERNET/READ_SMS/SEND_SMS |
| `research\.venv\Scripts\python.exe scripts/check_staged.py` before source commit | 17 staged files passed bounded private-path, credential, raw-message and learned-numeric-token matching; manual diff reviewed |
| `git diff --cached --check` | No whitespace errors; ordinary Windows LF/CRLF notices are not test failures |

JVM skip: `ExportParityTest` requires a newly trained schema1 export via `modelParityDir`, which is absent. It is **skipped**, not passed. Supplied schema2 parity is independently exercised in instrumentation. Both debug/development suites share the six core tests; do not add them as twelve unique behavioral tests.

Lint warnings: one `OldTargetApi` and four `GradleDependency` warnings (Compose BOM referenced twice and two Lifecycle dependencies). Dependencies were not upgraded speculatively. Supported target API36 is tested; newest-platform/API37 compatibility is pending. Dependency resolution/`pip check` is not a security-vulnerability certification. The staged scanner is bounded, not a complete secret/PII detector.

## Failure and correction

An intermediate API36 run completed 15 tests and failed the one large-font accessibility test: the Settings heading was not present immediately after navigation. The raw incomplete result is retained privately at `research/data/thesis-audit-20260923/api36-failed-accessibility.json`. `AccessibilityTest` previously used only `waitForIdle`, which does not explicitly establish window focus and asynchronous navigation state. Added bounded waits for those observable conditions while preserving the real click and heading/size/reachability assertions. The subsequent complete API36 suite passed all 16 tests. This supports a synchronization correction; it does not prove every possible UI race is absent. No failed attempt was counted as passed.

## Reproduced research evidence

The audit command in `reproducibility-guide.md`, using private output `research/data/thesis-audit-20260923`, produced a JSON object exactly equal to the existing `dataset-audit.json`. It reproduced 1,276 rows, inherited labels/languages, missing values, 4 exact duplicate excess rows, 27 normalized duplicate excess rows, 940 heuristic groups and 2 conflicting-label near-template groups. Original-byte hashes match. `dataset-freeze-summary.json` records median 167.5 characters, range 4â€“718, mean 215.533699, URL indicators 120, phone-like 147 and financial-keyword 1192. These overlapping heuristic counts do not clear privacy, source rights or labels. The private v2 manifest explicitly marks the known primary nonfinancial exclusion and preserves anonymous hashes/group membership.

No completed real annotations, agreement statistics, independent performance metrics, human usability responses or device results were created. Test metrics are fictional software fixtures. Real-data fitting was not performed; supplied model parameters and converted asset hash remain unchanged.

Converter command: `research\.venv\Scripts\python.exe -m smishguard.convert_supplied research/data/package-audit/original/model_export_final.json research/data/package-audit/original/MODEL_INTEGRATION.md --output research/data/thesis-audit-20260923/model-converted.json --parity research/data/thesis-audit-20260923/safe-parity.json --report research/data/thesis-audit-20260923/conversion.json`. All original files and the development asset were preserved.

## Android parity and readiness scope

Fixed non-sensitive supplied-model probes compare Python-reference token lists, local model feature indices and TF-IDF/L2 values, scores within 1e-10, strict >0.5 labels, unknown/empty-feature behavior, blank/long-input rejection and experimental metadata. A zero-margin test checks that exactly 0.5 is not suspicious. Expected feature values are calculated inside instrumentation from the private asset, not exported as public model parameters. The converter was rerun into fresh private outputs: five guide-score rounding checks passed, Python/sklearn maximum absolute error was 5.551115123125783e-17, and the converted model was byte-identical to the app asset. These are not private-message Android tests. No broad real-message parity or research accuracy is claimed.

API36 covers UI/lifecycle/decoder 9, denial 1, offline/export/supplied-model 3, modem SMS 1, notification/channel 1, accessibility 1. API26 covers supplied parity/rejection 2 and manual share/accessibility 2. Background and Activity recreation are tested; true OS process-death recovery, comprehensive rotation/landscape, TalkBack, permanent permission denial on the Xiaomi, carrier multipart/dual-SIM, vendor battery policies, real lock-screen behavior and phone latency/memory remain Pending. Experimental automatic warnings stay disabled even when permissions/consent are granted. Reporting has a disabled repository and no network permission/path.

## Packaging and physical restriction

The local APK passes ZIP CRC, dataset/test-asset exclusion and intended-model hash checks. Its SHA-256 is in the companion JSON and local `deliverables/thesis-20260923/SHA256SUMS.txt`. The source ZIP is built from reviewed Git-index bytes with fixed ZIP timestamps; no model asset, raw dataset, private packet, letter, local configuration, key or build directory is included. A local sharing notice marks the APK experimental and redistribution unresolved. No GitHub release was created.

The Xiaomi secure-FRP state is user-reported: restricted mode 1, setup/provisioning 1, restart ineffective, Xiaomi support pending. All physical checklist rows remain Pending. Do not attribute this restriction to the APK unless a new concrete package error supplies different evidence.

Packaging correction in `629bc95`: the initial broad directory guard rejected the legitimate Android `data/PreferencesRepository.kt` path. It was narrowed to private `research/data/` and `research/runs/`, and the resulting 134-member source archive passed exact tracked-membership, CRC, required-source and whole-archive raw-message/learned-numeric-token/credential-pattern checks (zero matches). An extra final blank line and Windows helper encoding errors were corrected before delivery. No original private data or old deliverable was deleted.
