# Private phone testing: SmishGuard 0.2.0-dev

13 October 2026 update: the user reports physical-phone checks completed.
The pending status and 0.2.0-dev artifact details below describe the earlier handoff.
No additional model-specific phone measurements are invented from that report.

Status: **Pending physical-device testing**. No phone results have been supplied. Existing emulator results are separate software evidence, not phone results or research accuracy.

## Verified handoff artifact (2026-09-22)

- File: `deliverables/SmishGuard-0.2.0-dev.apk` (13,032,755 bytes).
- Version: `0.2.0-dev`, version code `2`; application ID: `ph.smishguard.dev`.
- Minimum Android: 8.0 / API 26; target API 36. This is a debuggable development build.
- APK SHA-256: `3ca8237395f94f52638c27169024568c48262ff879daebb9231998c7ab02c3f1`.
- SDK apksigner verification passed: APK Signature Scheme v2, one Android Debug RSA-2048 signer.
- Signing certificate SHA-256: `7b15b0a216a5e78a2db8e4e9c489c0515ded705c683e7b3e0262c5e3c811c8c4`.
- Bundled `assets/model.json` SHA-256: `9026c925679f9667b5bd09e34f31dd884cdb72607650d97f9a0708c86fa6bab2`. It matches the current converted supplied model. Its metadata says manual development use, evaluation unverified, uncalibrated, automatic warnings not approved.
- APK matches the existing development build output and previously verified APK hash. No rebuild was needed. No CSV/XLSX/ZIP datasets are bundled; manifest has no INTERNET permission.

The supplied model is technically integrated for offline manual scans. Its score is **not a validated fraud probability**; 0.5 is a provisional threshold. These tests do not establish model accuracy, calibration or approval for automatic warnings.

## Share and install

The coordinator uploads only the APK and this guide plus the blank feedback template to the team's private folder. Do not publish the APK/model, real SMS, completed feedback or device-identifying screenshots on GitHub. No upload is performed by the preparation tools.

Download the APK to the test phone and open it. If Android asks, allow installation for the particular app opening the APK; turn that installer permission off after installation. Record the exact error if blocked. Do not disable device security protections to force installation. A signature-conflict error may indicate an existing development app signed with another key: record it before considering removal, since uninstalling clears local settings. The model-free app can coexist under the other application ID, so ensure you open the experimental development app.

Optionally verify the download on Windows:

```powershell
Get-FileHash -LiteralPath '.\SmishGuard-0.2.0-dev.apk' -Algorithm SHA256
```

## Short test sequence

Use the blank [feedback template](phone-feedback-template.md); keep completed copies outside the repository. Record actual observations, including failures and not-tested cases.

1. Record a tester alias (no real name), phone manufacturer/model, Android version, app version, installation source and installation success or exact error. Do not collect IMEI, serial number or phone number.
2. Launch and choose **Continue without permissions**. Confirm the experimental-model notice. Paste E1 into **Check** and scan. Expect an experimental result and cleared message input; record the displayed result without treating its classification as a pass/fail criterion. Repeat with T1, E2 and T2.
3. Share one fictional example as plain text from a notes app to SmishGuard. Confirm the intended text arrives and a manual scan works. Record the sending app and steps if SmishGuard is missing from the share sheet.
4. Turn on airplane mode and explicitly switch Wi-Fi off. Scan the same example again. Expect a result without a connection and the same displayed score for identical text. Restore connectivity afterward.
5. In Settings, try incoming-SMS consent and deny SMS permission if a prompt appears. Deny notifications if prompted (some Android versions have no runtime notification prompt). If already granted, use Android app settings to revoke, then return. Paste/share scans should still work. Record installer/system restrictions rather than forcing grants.
6. Try blank input, then an ordinary fictional example. Navigate Home/Check/Settings, use Back, and background/reopen the app after entering fictional text. Check that scanned input clears and that leaving the checking session or backgrounding does not restore the raw text. Note crashes, stuck loading, keyboard overlap, unreadable text or confusing controls. Optionally rotate and increase font size.
7. Confirm the automatic-warning-disabled notice and reporting-unavailable behavior. No report should be sent or queued. A settings label such as incoming SMS enabled refers to permission/consent, **not approval of automatic model inference**. Do not change the warning gate.

## Fictional functional examples

These invented messages use no real institution, account, phone number or clickable URL. Do not replace placeholders with real credentials or links. Any prediction is a functional observation, not an accuracy measurement or a ground-truth label.

- **E1:** `FICTIONAL TEST: Cloud Mango Bank says your pretend account is locked. Enter your pretend password at [TEST LINK] to unlock it.`
- **E2:** `FICTIONAL TEST: Our imaginary study group will meet in the library after class. Please bring your notebook.`
- **T1:** `FICTIONAL TEST: Cloud Mango Bank daw ito. Na-lock ang kunwaring account mo. Ilagay ang pretend password sa [TEST LINK] para ma-unlock.`
- **T2:** `FICTIONAL TEST: Sa library tayo magkikita pagkatapos ng class. Pakidala ang notebook para sa imaginary group meeting.`

## What real SMS can and cannot show in this build

With willing groupmates, an optional ordinary carrier SMS containing only a fictional example can show delivery in the phone's messaging app and whether SmishGuard stays stable. Use SMS, not RCS/chat, for this observation. Share or paste that received fictional text into SmishGuard to test **manual** scanning.

The receiver may assemble incoming SMS when consent and permissions allow, but the supplied model gate returns before automatic inference and notification. There is no receiver receipt log or on-screen processing acknowledgement. Therefore neither inbox receipt nor the absence of a warning proves receiver execution, multipart assembly or model processing. A warning is not expected even when permissions are granted. Do not mark automatic detection, background processing or multipart processing as passed from these observations.

Real-device SMS receiver delivery/assembly, installer SMS-permission behavior, and manufacturer-specific background restrictions remain **Pending physical-device testing** until appropriate actual evidence is supplied. End-to-end automatic warnings additionally depend on a separately evaluated, approved model/build and cannot be validated with this build. Notification appearance/lock-screen behavior cannot be validated through model-triggered warnings here. Do not enable warnings just to test them.

Submit feedback privately. Include only fictional example IDs, reproduction steps and cropped/redacted screenshots; exclude message inboxes, contacts, notifications, credentials and other personal information.
