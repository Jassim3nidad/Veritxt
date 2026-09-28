# SmishGuard — experimental model development milestone

Dataset team handoff: [specific human tasks and private file locations](docs/dataset-team-task-sheet.md), [completed automated audit](docs/dataset-preparation-audit.md), and [provenance of the 1,200-record rule](docs/sample-size-provenance.md). Existing review IDs/packets were preserved; no independent labels, permissions or unseen status were fabricated.

29 September comparison preparation: [protocol](docs/algorithm-comparison-protocol.md), [review prerequisites](docs/comparison-data-review.md), and [results/build status](docs/algorithm-comparison-results.md). Shared minimalist UI is preserved. Separate `lr`, `nb`, `svm` build types have distinct application IDs and require privately reviewed model assets. Only the previously permitted historical LR is currently available for an experimental comparison-variant APK; no new research training or winning-algorithm claim has been made.

Thesis completion materials: [gap analysis](docs/thesis-gap-analysis.md), [completion plan](docs/thesis-completion-plan.md), [requirements matrix](docs/requirements-traceability-matrix.md), [current verification](docs/verification-safe-handoff.md), [reproducibility guide](docs/reproducibility-guide.md), [Chapters 3–5 drafting support](docs/thesis-drafting-materials.md) and [defense materials](docs/defense-materials.md). Research performance remains pending independent evidence. Xiaomi installation is blocked by reported secure FRP; no bypass or repeated installation is part of this work.

The latest private package is under `deliverables/thesis-20260923/`; older deliverables are preserved. The development APK contains the supplied model and is not cleared for public redistribution. Source-only sharing excludes that model and all private research artifacts.

Native Kotlin/Compose research prototype for Philippine financial-institution impersonation in SMS. **Version 0.2.0-dev includes the supplied LR model for offline manual paste/share testing.** The interface identifies its output as an uncalibrated model score with unverified research performance and a provisional 0.5 threshold. Automatic model-driven SMS inference/warnings and reporting remain disabled. The separate default `debug` variant still says **Model not installed**. No dataset is bundled in either APK. Read the [package audit](docs/dataset-audit.md) before using the data for research.

Project/client authorization is recorded as **reported authorized to proceed**, supported by the signed client-request letter. See [separate authorization and data/model statuses](docs/project-authorization.md) and [source-specific evidence still needed](docs/source-evidence.md). Development is not blocked by unresolved dataset research eligibility.

This public checkout includes the converter and tests but excludes the supplied model asset, private datasets/reviews and generated deliverables. The existing local APK is preserved. See [co-developer setup and sharing policy](docs/repository-sharing.md).

## Open and build on Windows

Open this repository root (the folder containing `settings.gradle.kts`) in Android Studio. Let Gradle sync. Use **JDK 17**, Android **SDK Platform 36**, SDK Build Tools **35.0.0**, and current platform-tools. The app supports Android 8.0/API 26 and later; compile/target SDK is 36.

Pinned build stack: Gradle **8.13** with checksum-verified wrapper; Android Gradle Plugin **8.13.2**; Kotlin/Compose compiler plugin **2.3.21**; Compose BOM **2025.12.01**; Activity **1.13.0**; Lifecycle **2.10.0**; DataStore **1.2.1**; coroutines **1.11.0**. These are stable versions selected for compatibility, not a claim that every dependency is the newest. The newer Compose 2026.08 bundle required SDK 37/AGP 9.1+ during verification and was not used.

Android Studio creates `local.properties` for your SDK. If creating it yourself, escape the drive colon, e.g. `sdk.dir=C\:/Users/YourName/AppData/Local/Android/Sdk`.

### Android Studio import troubleshooting

If Studio reports that Gradle 8.13 is incompatible with JVM 25, open **Settings → Build, Execution, Deployment → Build Tools → Gradle**. Set **Gradle JDK** to the installed **Eclipse Temurin 17** (or use **Add JDK from disk…** to select the JDK 17 installation directory). Check the actual Java version: a misleading SDK name such as `jbr-21` can still point to a Java 25 installation.

Keep **Distribution** set to **Wrapper**. **Gradle user home** is a separate cache directory, normally `C:\Users\YourName\.gradle`; do not put the JDK path in that field. Click **OK**, then sync the project. This matches the JDK 17 used for the verified command-line build.

```powershell
.\gradlew.bat :app:assembleDebug :app:lintDebug :app:testDebugUnitTest
# On this host, use the helper for a Java/Windows loopback socket workaround:
.\scripts\build.ps1 -Variant development
```

The helper changes `JAVA_TOOL_OPTIONS` only within its process and restores it afterward. It does not alter Windows or Android security settings. Ensure `C:/sg-nonexistent-socket-dir` does not exist; the deliberately invalid Unix-domain socket directory makes Java use its TCP pipe fallback.

Development APK output: `android\app\build\outputs\apk\development\app-development.apk` (package `ph.smishguard.dev`). This is a development-signed APK, not a production release. Release signing and distribution governance remain future work. First-time dependency downloads require internet on the build computer; app detection has no internet dependency.

Prepared deliverables are in `deliverables/`: `SmishGuard-0.2.0-dev.apk`, a portable `SmishGuard-source.zip`, and `SHA256SUMS.txt`. Regenerate after a successful build with `python scripts\package.py --variant development`. The source archive excludes SDK paths, build caches, virtual environments, research data and model runs.

## Run on an emulator

Create an Android API 36 virtual device in Android Studio Device Manager, start it, then:

```powershell
adb devices
adb install -r android\app\build\outputs\apk\development\app-development.apk
adb shell am start -n ph.smishguard.dev/ph.smishguard.MainActivity
.\scripts\build.ps1 -Variant development -ConnectedTests
```

An API 36 `SmishGuard_Test_API36` emulator was created for this milestone. The tests cover manual entry, empty/long Taglish input, share/clear, denied SMS state, unavailable reporting, lifecycle clearing and static-screen capture. Synthetic inputs remain within test code. Do not use real private SMS for screenshots or test logs. `VisualReviewTest` disables screenshot protection **only within instrumentation** while capturing static, empty screens; production always enables protection.

For expanded emulator verification (software models, modem SMS, multipart receipt, notifications and private-storage inspection):

```powershell
$env:PYTHONPATH='research'
research\.venv\Scripts\python.exe -m smishguard.software_fixtures
.\scripts\build.ps1 -Variant development -EmulatorTests
```

The verifier installs both APKs, clears SmishGuard's emulator data, controls emulator permissions/radios, restores airplane/Wi-Fi state, and leaves the app at onboarding. Use the dedicated test AVD: Android's messaging app may retain the synthetic incoming messages. Specialized modem/offline/notification tests require the verifier's setup and are skipped by the ordinary connected suite. No physical phone is required. See [the verification checklist](docs/verification.md) and [development emulator evidence](docs/development-emulator-results.json).

## Physical device

Enable developer options/USB debugging if using adb, connect a trusted computer and approve its debugging prompt, then use the same install/start commands. Alternatively transfer the APK and follow the phone's normal per-installer installation prompts. **Sideloading does not guarantee SMS permission**: RECEIVE_SMS is hard restricted and depends on installer allowlisting, runtime consent, telephony and device policy. Never bypass these restrictions. Manual/share checking works without SMS permission.

Onboarding explains processing and limitations. Home shows the real model and scanning states. Settings lets the user consent to new-SMS checks, request notification permission, review Android permission settings, choose a city manually, or clear preferences. This experimental model cannot enable automatic warnings, even with consent and permissions granted. Permission denial, force-stop and battery/vendor policies can prevent automatic checks. The app does not monitor RCS, Messenger, WhatsApp or other services and never replaces the default SMS app.

Share plain text from the existing messaging app using Android **Share → SmishGuard**, or type/paste into **Check**. Checking clears text; leaving the app or changing configuration also clears the session. Verify requests independently through official channels. No score could guarantee that a message is legitimate.

## Project map

- `android/app/`: Compose UI, transient ViewModel, preferences, receiver, notifications, offline detector, report contract and Android tests.
- `research/`: dataset schema, preprocessing, group/random/time splits, classical training/export, calibration/evaluation, shortcut comparisons, optional transformer adapter and software tests.
- `docs/dataset-audit.md`: verified supplied-package counts and unresolved eligibility/provenance.
- `research/intake-template.csv`: ready-to-fill independent-annotation intake; see the labeling guide.
- `docs/decisions.md`: source-document reconciliation and assumptions.
- `docs/privacy.md`: data lifecycle, conservative domain policy and permission limitations.
- `docs/model-contract.md`: portable inference schema and deployment procedure.
- `docs/verification.md`: actual checks, remaining checks and requirement mapping.
- `backend/`: tested local reporting-readiness prototype; Android remains disconnected.

For research setup and commands, see [research/README.md](research/README.md). No app scans feed the research dataset. Collection requires the separate consent, redaction and ethics process described in the supplied thesis documents.

Build references checked during implementation: [AGP 8.13 compatibility](https://developer.android.com/build/releases/agp-8-13-0-release-notes), [Kotlin compatibility](https://developer.android.com/build/kotlin-support), [Compose BOM](https://developer.android.com/develop/ui/compose/bom), [BOM mapping](https://developer.android.com/develop/ui/compose/bom/bom-mapping). SMS policy references are linked in `docs/privacy.md`.

## Safe backend and model evidence handoff

Training and evaluation procedure documented with reproducible scripts and supplied result tables; dataset-dependent reproduction was not independently rerun in this handoff.

[Sanitized evidence](research/model_evidence/README.md) preserves aggregate tables and scripts, with numerical conflicts and CV limitations explicitly recorded. [Backend setup](backend/README.md) is local-only; [all deployment gates](docs/reporting-readiness.md) remain pending. Offline manual scanning and Android model integration are implemented. Calibration is not established; prospective evaluation is pending; automatic warnings are disabled/unapproved; Android reporting is disabled; public backend deployment is not approved. Xiaomi installation remains blocked by secure FRP and physical-device SMS testing remains pending. No approved Chapters 1 or 2 were rewritten.

The API 36 Settings state race and result-flow test synchronization failures are resolved in the [24 September reliability follow-up](docs/api36-reliability.md): 10 successful isolated repeats per affected test, 19 specialized passes, and 15 ordinary passes with 5 explicit skips. Earlier failures remain recorded in [the historical handoff report](docs/verification-safe-handoff.md). Physical-device and research limitations remain pending.
