# Verification — supplied-model development milestone

Updated 21 September 2026. The supplied dataset/model package has been inspected and technically integrated; previous no-package statements describe the [historical milestone](verification-20260920.md), not current inputs. No research performance, calibration quality or approval for automatic warnings is established.

## Three separate model states

| State | Current result |
|---|---|
| Technically integrated | Supplied LR parameters converted unchanged to schema 2; five guide references reproduced within 0.00005; safe full-precision probes used for Android parity. |
| Experimentally evaluated | Unverified. Export was trained on all supplied rows; no same-row held-out claim or new research metrics were produced. Retrospective refitting tooling is prepared. |
| Approved for user-facing automatic warnings | No. Receiver policy returns before experimental-model inference, regardless of consent/permissions. Reporting also remains disabled. |

Version **0.2.0-dev**, application ID `ph.smishguard.dev`, bundles the supplied model only for manual paste/share testing. Results say experimental, unverified and uncalibrated; the score is not a percentage likelihood of fraud. Threshold 0.5 is provisional and uses strict greater-than. The default debug variant remains model-free.

## Software verification

| Check | Result / evidence |
|---|---|
| Development and baseline debug APK build | Passed on JDK 17.0.16, Gradle 8.13, AGP 8.13.2, SDK 36. |
| Development lint | 0 errors, 5 warnings; [review of all previous 10 warnings](lint-review.md). |
| JVM tests | 6 passed; 1 legacy schema-1 research-export parity test explicitly skipped because no newly evaluated export was supplied. Supplied schema-2 parity is exercised on Android separately. |
| Python tests | 30 passed after the source/review-packet update. Intake/labels/agreement, split isolation, train-only fitting, calibration/threshold/final boundaries, sealed selection, subgroup guards and model conversion. Synthetic fixtures only; not research metrics. |
| Five supplied guide scores | All pass four-decimal rounding tolerance 0.00005. No weights changed. [Full-precision outputs](model-conversion.json). |
| Python portable versus sklearn | Maximum safe-probe absolute error 5.551115123125783e-17. |
| API 36 emulator | **16 passed**, no skips: UI/lifecycle/decoder 9, notification denial 1, offline/parity/invalid models 3, modem SMS 1, notification posting/channel block 1, large-font accessibility 1. [Raw results](development-emulator-results.json). Two private files inspected; zero raw fixture markers. |
| API 26 emulator | **4 passed**: supplied offline parity/policy and malformed models (2), manual development share and 2.0 font accessibility (2). [Raw results](api26-results.json). SMS/notification delivery was not rerun on API 26. |
| APK contents/signature | Signature Scheme v2 verified; only RECEIVE_SMS, POST_NOTIFICATIONS and AndroidX internal permission. Packaging rejects dataset/CSV/parity fixtures. Model parameters/hash and archive contents checked separately. |

Supplied parity tests require identical token lists and score error <=1e-10. This is tighter than rounded guide tolerance, allowing only floating-point accumulation differences. Frozen Python Unicode 15 tables cover single-character tokens, ñ, accented letters, underscores, expanding casing, Greek final sigma, numeric Unicode and supplementary-plane letters independently of Android's Unicode version. Probes cover English/Taglish, empty/blank, unknown-token, long and over-limit input. Malformed schema, wrong class order/dimensions, invalid bias, unsupported Unicode and unauthorized metadata states fail closed.

## Privacy and behavior boundaries

The APK has no INTERNET, READ_SMS or SEND_SMS permission and no network/report queue implementation. Model and metadata are local assets. Raw text is held in memory, cleared after inference/navigation/background/recreation, and not included in saved state, notifications or logs. The verifier searches app-private regular files for safe fixture markers after the exercised paths. This is bounded software evidence, not forensic memory erasure or packet capture; Android's separate messaging provider, clipboard and keyboard are outside app-private storage.

Missing/invalid/inference-failure states, denied permissions, manual paste/share, navigation and disabled reporting remain covered. A synthetic test-only detector can exercise SMS plumbing but never creates model-driven warnings. Notification-service tests intentionally post a clearly labeled software notification; this is distinct from enabling the supplied model's warnings.

## Emulator limitations and corrections

- API 36 `adb emu sms send` tests single and multipart Unicode SMS, requires multiple Android PDUs and checks intact assembly, consent-off suppression and no synthetic warning. Custom `sms pdu` was accepted but not delivered in two historical attempts; arbitrary reordered/missing/duplicate carrier segments remain unverified.
- An emulator System UI ANR dialog stole window focus and blocked clipboard access. Dismissing that system dialog allowed the focused paste test to pass. The verifier now detects ANR dialogs before running, and the paste test checks focus/platform clipboard/action acceptance and waits for the asynchronous update. No message content is logged for diagnostics.
- API 26 `svc wifi` exited 137 because that image denies CHANGE_WIFI_STATE to the shell (confirmed by the system exception), even when run alone. The focused verifier uses normal Android Settings switches instead; no permissions were bypassed. Earlier failed setup attempts are not counted as passed tests.
- Large-font instrumentation found the switch semantic height was 32 dp. An explicit 48 dp minimum now passes on API 36 and API 26.
- The long-input test uses the accessible click action after scrolling; other manual/share flows exercise ordinary clicks. Test preferences wait for onboarding transitions. Test synchronization changes do not establish detector accuracy.
- Large-font checks use 2.0 scale and inspect headings, accessible labels, minimum targets and reachable controls. TalkBack, switch access, landscape, all screen sizes, API 27–35/37 and manufacturer configurations are not comprehensively tested. Earlier static screenshots are historical, not a current visual certification.

## Research readiness

See [dataset audit](dataset-audit.md), [ready-to-fill intake](../research/intake-template.csv), [labeling guide](../research/LABELING_GUIDE.md) and [exact import/compare/evaluate/export/parity/build commands](../research/README.md).

Verified raw counts: 1,276 rows (1,054 ham / 222 smishing), 1,149 English / 127 Taglish. After UCI and one explicit nonfinancial exclusion there are 1,205 nominal candidates, 1,201 unique texts and 869 heuristic groups; these are not certified eligible. **Primary-study eligibility not yet verified**; eligible counts are unknown, not zero valid records. Project/client authorization is recorded as reported authorized in [the authorization record](project-authorization.md). UCI stays supplementary. Date meaning, source-specific permitted-use documentation, redaction and independent annotation remain unresolved; see [the operation-specific evidence list](source-evidence.md).

The prepared workflow refits LR/NB/SVM using train-only preprocessing, disjoint calibration/validation/final partitions, group isolation or declared permissive comparisons, and sealed validation PR-AUC model selection. Threshold selection uses validation F1; final evaluation is separate and non-overwriting. Uncertain labels are held until adjudication. Source/annotation metadata never enters model features. No unapproved supplied records were passed off as an approved research run. Transformer experiments and genuinely unseen confirmation remain pending.

## Reproduce

```powershell
$env:JAVA_HOME='C:\Program Files\Eclipse Adoptium\jdk-17.0.16.8-hotspot'
$env:PYTHONPATH='research'
research\.venv\Scripts\python.exe -m unittest discover -s research\tests -v
# Start the dedicated API 36 emulator, wait for boot, resolve any system dialogs.
.\scripts\build.ps1 -Variant development -EmulatorTests
# Stop API 36, start SmishGuard_Test_API26 on port 5556, wait for boot.
research\.venv\Scripts\python.exe scripts\emulator_api26_verify.py
research\.venv\Scripts\python.exe scripts\package.py --variant development
```

Both verifier scripts refuse physical devices and restore their radio/font settings. They install development/test APKs and clear only SmishGuard's emulator data. Keep synthetic SMS on dedicated AVDs. See research README for unchanged-weight conversion and future approved-data commands.

## Pending physical-device testing

| Check | Status |
|---|---|
| Real-device SMS delivery, carrier multipart and dual SIM | Pending physical-device testing. |
| Installer permission behavior / restricted RECEIVE_SMS availability | Pending physical-device testing. |
| Manufacturer-specific background, battery saver, reboot and force-stop restrictions | Pending physical-device testing. |
| Real lock-screen notification presentation | Pending physical-device testing. |

These do not block emulator development. Later phone checklist:

1. Install 0.2.0-dev normally; record model/Android/installer and permission availability. Deny SMS/notifications; check paste/share still works.
2. In airplane mode, scan safe English/Taglish examples; confirm experimental wording, uncalibrated score, session clearing and disabled reporting.
3. With consent/allowed permissions, receive safe single/multipart carrier SMS; verify the original messaging app is unaffected and this experimental model emits no automatic warning.
4. Repeat under screen-off, battery saver, reboot and force-stop/reopen; document manufacturer behavior. Do not interpret missed receipt as research detector error.
5. After a separately evaluated and approved warning model exists, test generic lock-screen posting and permission/channel denial. That approval has not occurred here.

## Authorization-gate update

Reported project/client go-ahead and signed request letter recorded separately from dataset use, label/redaction quality and model evaluation. Removed categorical aggregator rejection; source-specific permitted-use and study-role gates now have regression coverage: documented aggregator acceptance, pending/not-permitted evidence holds, donation-only consent requirements and supplementary isolation. No Android code/model/threshold changed in this update, so the API 26/36 evidence above remains the applicable app verification; unrelated emulator tests were not rerun.

## Source/review-packet update

30 Python tests pass, including blinded preparation/release, withholding unreviewed text, spreadsheet formula handling and conservative source matching. Pinned official downloads reproduced identical member/archive hashes and aggregate matches. No APK rebuild or unrelated Android tests were run: app/model bytes are unchanged. The public Git tree excludes the private model asset and generated deliverables; see repository-sharing.md. Real-data baseline comparison remains dependent on reviewed intake, not repeat project authorization.
