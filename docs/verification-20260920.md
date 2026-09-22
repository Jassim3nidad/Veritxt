# Historical verification — 20 September 2026

Updated 20 September 2026. Development and verification continue on an API 36 emulator. No approved dataset or evaluated model was supplied. Synthetic software checks below are not research results or detection-accuracy claims.

## Requirements to implementation

| Requirement | Implementation / scope |
|---|---|
| Read sources, preserve repository | Three supplied DOCX texts reviewed; workspace initially contained only `.idea`; conflicts documented in decisions.md |
| Native APK / Kotlin / Compose M3 | Root Gradle project, `android/app`, six screens, system light/dark theme |
| ViewModel / coroutines / StateFlow | `CheckViewModel`, background inference with cancellation and timeout |
| DataStore / minimal persistence | Three preference fields only; no scan/report history, no need for Room |
| Manual and share checking | Edit/clear/scan/error/loading, ACTION_SEND text/plain, 10,000-character bound |
| Honest result | Missing/invalid/failure/success states; no invented score; uncertainty guidance |
| Incoming SMS | Consent, RECEIVE_SMS only, protected SMS_RECEIVED receiver, multipart joining, bounded async work |
| Notification privacy | Channel and runtime/app/channel permission checks, generic private warning, no message text |
| SMS integrity | No read-inbox, send, delete, block or default-SMS APIs/permissions |
| Raw message privacy | Memory only; no saveable state/backup/logging/jobs/network; clears on scan/end/background/rotation |
| Optional reporting | Allowlisted factory, exact preview after real result/city, disabled repository; no fake success |
| URL safety | URI parser, conservative registry suffixes, removes tenants/paths/credentials; malformed inputs tested |
| Model availability | No main model asset; debug-only fixtures cannot drive receiver warnings |
| Portable inference | Versioned TF-IDF/L2/linear double runtime, JSON validation, sigmoid calibration support |
| Training foundation | LR/NB/SVM; frozen manifest and train-only fitting; separate calibration/validation/final evaluation |
| Evaluation | Random/group/time strategies, template grouping, lexical/URL/shortcut conditions, classification/calibration/base-rate metrics |
| Transformers | Optional local XLM-R/RoBERTa-Tagalog adapter; unexecuted without data/checkpoints; phone export deferred |
| Dashboard | Contract and future-work documentation only; voluntary counts not prevalence |

## Automated and emulator results — 20 September 2026

Host: Windows, JDK 17.0.16, Python 3.12. AVD: `SmishGuard_Test_API36`, Android 16/API 36, x86_64, build `BP22.250221.010`. Machine-readable instrumentation evidence: [emulator-results.json](emulator-results.json).

| Check | Result and scope |
|---|---|
| Debug build and lint | Passed; 0 lint errors, 10 existing nonblocking target/dependency/style warnings |
| JVM tests | 6 passed; real-export parity test skipped explicitly because no evaluated model exists |
| Python software tests | 10 passed: export/calibration arithmetic, split/vocabulary isolation, preprocessing, metric math, URL separation and rejection of synthetic/unverified research records |
| Emulator UI/lifecycle/decoder group | 8 passed: paste, share/clear, empty and long input, permission-denied manual flow, navigation clearing, missing/invalid/failed/synthetic results, disabled reporting, background/recreation clearing, UCS-2 PDU decoding |
| Emulator offline model test | Passed: LR/NB/SVM exports from the shared Python exporter; 12 reference scores/classes match Android to 1e-10 with airplane mode on and Wi-Fi off; all remain synthetic, no probability claims |
| Emulator modem SMS test | Passed: `adb emu sms send`, complete single message and a 277-character multipart message including ñ; Android delivered multiple PDUs (two observed), full text matched once; consent off stopped inference; synthetic suspicious result did not post a warning despite granted notification permission |
| Emulator notifications | 2 passed: runtime denial suppresses warnings; generic secret-visibility notification construction, explicitly labelled software-test posting, cancellation and channel-disabled suppression |
| App private storage | Inspected both regular files in SmishGuard's private directory after UI, lifecycle and SMS tests; no tested raw-message marker found |
| Transmission boundary | Installed app denies INTERNET; source has no network client, message logging or raw-message file writes; reporting remains disabled and does not queue payloads |
| Total emulator instrumentation | 12 passed in the expanded verification run, no skipped tests in that run |
| Packaged debug APK | APK Signature Scheme v2 verified; RECEIVE_SMS/POST_NOTIFICATIONS plus AndroidX internal permission only; no INTERNET/READ_SMS/SEND_SMS, model asset or test Application/runner in delivered APK |

Updated artifacts: [debug APK](../deliverables/SmishGuard-0.1.0-debug.apk), [portable source](../deliverables/SmishGuard-source.zip), [SHA-256 checksums](../deliverables/SHA256SUMS.txt). These replace the earlier 0.1.0 milestone artifacts; the application version is unchanged.

The notification-settings button now opens Android notification settings when runtime permission is already granted but notifications/channel are disabled. It previously re-requested an already granted permission. Research training and synthetic fixture generation now share one validated linear exporter; every train/validation/calibration/test pair is included in template-overlap bookkeeping. Primary research validation/minimum dataset requirements remain intact.

Synthetic models and the custom test Application are confined to the separate instrumentation APK. The distributed debug app contains no model asset, cannot produce a real assessment, and rejects synthetic exports. Tests cover invalid/failure/synthetic presentation and ensure none enables reporting or displays a confidence percentage. No real warning based on a synthetic prediction was emitted; the notification-service test labels its notification explicitly as a software test.

Private-file inspection is a bounded check of known synthetic markers, not a forensic memory-erasure guarantee. Android's separate SMS provider/default messaging app may retain injected messages, as expected. System logs, clipboard and third-party keyboards are outside SmishGuard's private-storage boundary. No packet-capture claim is made: no INTERNET permission and no networking/reporting implementation prevent direct app transmission in this build.

## Emulator limitations and test corrections

- The console advertised `sms pdu` and accepted custom concatenated UCS-2 PDUs, but this AVD did not deliver them to Android/SmishGuard (two attempts timed out). That path is **not verified**. The supported `sms send` path then generated actual multipart delivery successfully; a test-side Android observer requires more than one PDU, so oversized single-part delivery cannot falsely pass. Arbitrary out-of-order, missing or duplicate modem segments remain unverified. Separate native decoder tests cover known UCS-2 PDUs and application joining bounds.
- Notification service posting is asynchronous. The first test checked immediately and failed; it now waits up to five seconds for the service state. The focused retest and complete verifier both passed. This was a test synchronization fix, not evidence of an app posting failure.
- Emulator permission grants are controlled test setup, not proof that a normal phone installer will allow restricted SMS access. Carrier transport, SIM provisioning, OEM background rules and real lock-screen behavior cannot be established here.
- Previous light/dark static screenshots remain in `docs/screenshots/`; they were reviewed in the earlier milestone and were not recaptured in this run. TalkBack, API 26, other Android versions and multiple screen/font configurations remain additional coverage.

Supported console reference: [Android emulator console SMS commands](https://developer.android.com/studio/run/emulator-console#sms). Actual command support was also checked with `adb emu help sms` on this AVD.

## Physical-device status

| Check | Status |
|---|---|
| Real-device SMS delivery, carrier multipart behavior, dual SIM | Pending physical-device testing. |
| Installer permission behavior and restricted RECEIVE_SMS availability | Pending physical-device testing. |
| Manufacturer-specific background restrictions, battery policies and force-stop recovery | Pending physical-device testing. |
| Real lock-screen warning presentation and notification settings | Pending physical-device testing. |

These items do not block emulator development, rebuilding or software verification.

## Remaining dependencies

- Ethics-approved Philippine financial-SMS dataset, labels/redaction review, evaluated model, threshold/calibration review and genuine model-export parity. No detection accuracy, research winner or real-model latency is claimed.
- Vetted transformer checkpoints/dependencies and the remaining research experiment matrix. The optional adapter is present but untrained.
- Reporting endpoint, privacy/security/retention review and dashboard acceptance; reporting intentionally remains disabled.
- Production signing and wider accessibility/device/API coverage.

## Repeatable verification

Start the dedicated API 36 AVD before running:

```powershell
$env:PYTHONPATH='research'
research\.venv\Scripts\python.exe -m unittest discover -s research\tests -v
research\.venv\Scripts\python.exe -m smishguard.software_fixtures
.\scripts\build.ps1 -EmulatorTests
research\.venv\Scripts\python.exe scripts\package.py
```

The emulator verifier refuses physical devices, installs both APKs, clears SmishGuard emulator data, sets test-only permissions/radios, restores airplane/Wi-Fi state, then clears test preferences and opens onboarding. Ordinary `-ConnectedTests` runs the general instrumentation suite; special modem/offline/notification checks are skipped unless the dedicated verifier supplies their required setup. It never substitutes synthetic data into the primary research pipeline.

## Short real-phone checklist for later

1. Install the debug APK using the intended installer; record Android/version/model and whether SMS access is available. Deny SMS and notifications first; verify paste/share still works.
2. With consent and allowed permissions, receive safe single and multipart test SMS through a real carrier. Verify messages remain in the original messaging app. A missing model must show no assessment or warning.
3. Once an evaluated model is integrated, check airplane-mode inference and generic lock-screen notifications. Disable/re-enable the warning channel and runtime permission.
4. Check screen-off/background, battery saver, reboot and force-stop/reopen behavior under manufacturer defaults. Record missed delivery without assuming emulator results apply.
5. Confirm session clearing after navigation/background and that reporting remains unavailable until an approved service is configured.
