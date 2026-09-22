# Same-phone installation investigation — 2026-09-22

## Current status update — 2026-09-23

The team now reports Xiaomi M2103K19G / Android 13 / MIUI 14.0.6 with `secure_frp_mode=1`, `user_setup_complete=1` and `device_provisioned=1`. Restart did not clear the restriction. Xiaomi support is being contacted. **Installation is blocked by device state, not an established APK failure.** These are user-supplied findings, not new readings from this workstation. No new installation or protected-setting change was attempted. Keep support correspondence private. Use [the post-resolution checklist](physical-device-checklist.md) after official resolution; do not repeat the older collection/restart/install steps while the restriction remains active. The investigation below is preserved as historical evidence, including its older APK checksum.

Status: **Blocked pending authorized phone connection or owner-collected evidence**. No physical phone was listed by local ADB. No device settings, accounts or logs were inspected, and no installation attempt was made on the phone. Installation, opening and offline manual scanning remain pending.

Remote tester update: use [the phone-only / standalone Windows guide](remote-phone-diagnostics.md). The script now defaults to `platform-tools/adb.exe` beside itself, not a developer's local SDK. Existing SDK users must pass `-Adb` explicitly. The tester can use his own computer; connection to the project coordinator's laptop is unnecessary.

## Established artifact checks

`deliverables/SmishGuard-0.2.0-dev.apk`: 13,032,755 bytes; SHA-256 `3ca8237395f94f52638c27169024568c48262ff879daebb9231998c7ab02c3f1`.

SDK aapt/apksigner/zipalign and ZIP inspection confirm:

- Application ID `ph.smishguard.dev`, version `0.2.0-dev` / code 2; minimum API 26, target API 36. Target SDK is not the minimum OS requirement.
- Valid v2 signature, one Android Debug RSA-2048 signer; certificate SHA-256 `7b15b0a216a5e78a2db8e4e9c489c0515ded705c683e7b3e0262c5e3c811c8c4`.
- Complete standalone APK: manifest, resources and DEX present; no split/uses-split/isSplitRequired declaration; testOnly absent (false); debuggable true. No `-t` install flag needed.
- Native libraries `libandroidx.graphics.path.so` and `libdatastore_shared_counter.so` provided for arm64-v8a, armeabi-v7a, x86 and x86_64. ZIP CRC and `zipalign -c -P 16 4` checks pass. Actual phone ABI/OS still needs collection.
- Supplied model asset SHA-256 `9026c925679f9667b5bd09e34f31dd884cdb72607650d97f9a0708c86fa6bab2`, unchanged. No packaging defect found, so no rebuild or app changes made.

The screenshot reports the exact secure-FRP error. Owner-reported phone: M2103K19G, MIUI Global 14.0.6 / 14.0.6.0(TKSMIXM), approximately 81 GB available; normal installer crashes, alternate installer exposes the error. These are reports, not remotely verified device readings.

## Cause traced, device diagnosis still open

In [AOSP Android 13 PackageInstallerSession.java](https://android.googlesource.com/platform/frameworks/base/+/refs/tags/android-13.0.0_r1/services/core/java/com/android/server/pm/PackageInstallerSession.java), lines 1786–1790 check whether SECURE_FRP_MODE equals 1 and the caller is allowed before throwing the exact reported SecurityException. The helper at line 1741 excludes the known system installer and otherwise checks privileged installation permission. This happens before session sealing/package validation in this path. This is a framework restriction, not an error asking for a different APK signature, SDK or more storage. Xiaomi's exact firmware implementation has not been inspected.

[AOSP Settings.java](https://android.googlesource.com/platform/frameworks/base/+/refs/tags/android-13.0.0_r1/core/java/android/provider/Settings.java) defines this as restricted FRP mode, cleared when its challenge is solved. Merely having ordinary account-based FRP protection configured does not establish this active state.

- **Active setup/protection state:** supported hypothesis if secure_frp_mode=1 and owner sees unfinished verification. Complete the official visible setup/account challenge privately.
- **Stale state/firmware defect:** possible if official setup/verification is complete yet the restriction persists. Completed-setup flags alone do not prove successful account verification. No confirmed MIUI-specific defect or fixed firmware version was found in the official sources reviewed.
- **Installer failure:** the normal installer may mishandle the same exception, or have an independent crash. Screenshot alone cannot distinguish these; installer name/version and exception class are needed if it persists after state resolution.
- **APK compatibility/signing:** no current artifact evidence supports this cause. Download corruption, a previously installed differently signed copy or another later error remain possible, to be tested only if reported by package manager.

## Minimum collection on this same phone

1. Owner unlocks the phone and checks whether official setup or account verification is unfinished. Tell the team only yes/no and the prompt type, never credentials/codes. If setup blocks debugging, stop and use the official owner-verification route below.
2. Connect by a data-capable USB cable to the team's computer. Xiaomi documents Settings > My device/About phone > All specs > tap MIUI version seven times; then Additional/More settings > Developer options > ordinary USB debugging. Accept this trusted computer's RSA prompt while unlocked. Do not enable OEM unlocking, change MIUI optimization, disable security scanning, or change extra security toggles. [Xiaomi USB-debugging guidance](https://www.mi.com/global/support/article/KA-06515/), [Android ADB documentation](https://developer.android.com/tools/adb).
3. From this repository in PowerShell run `powershell -NoProfile -File scripts/phone-install-diagnostics.ps1`. It selects one physical USB device and reads only model, OS/API/build/security patch, ABIs, three setup-state settings and SmishGuard package presence. On another computer use `-Adb 'C:\path\to\platform-tools\adb.exe'`. If unauthorized, owner must accept the prompt; if no device, try another data cable/USB port and official USB driver guidance. Do not send serial numbers. Null/permission-denied values are inconclusive, not proof of FRP being off. These settings query owner user 0; disclose if testing in a secondary profile because scope then needs checking.
4. Compare the **actual downloaded phone file**, not a new download. Copy it from the phone's Downloads via USB file transfer to a private local directory, then run `Get-FileHash -LiteralPath 'C:\path\to\copied-phone-file.apk' -Algorithm SHA256`. Compare to the hash above. Alternatively, if the filename/location is exactly as below and shell access is allowed, use:

```powershell
$adb = "$env:LOCALAPPDATA/Android/Sdk/platform-tools/adb.exe"
& $adb -d shell sha256sum /sdcard/Download/SmishGuard-0.2.0-dev.apk
```

5. Return only the narrow script values, checksum match/mismatch, setup-prompt yes/no, and installer app name/version. Do not collect full logcat, bugreport, account dumps or unrelated screenshots. If the system installer still crashes after the state is resolved, reproduce once and provide only its exception class/message and relevant PackageInstaller stack frames through the private channel; redact unrelated data.

## Supported resolution and conditional install

If official setup requests verification, the owner completes it on-device using the previous screen lock or previously associated Google account as directed by the official flow. [Xiaomi's guidance](https://www.mi.com/global/support/faq/details/KA-42580/) recommends that route; for forgotten account details it points to account recovery and, when necessary, proof of purchase and after-sales assistance. Do not send the team passwords or codes. We are not asking for another factory reset.

If setup was already completed, a normal owner-initiated restart followed by checking for any outstanding official setup prompt is a non-destructive diagnostic step, not a promised fix. Recollect the three state values. If restricted mode remains active despite completed official verification, contact Xiaomi using the summary below and request a supported, data-preserving repair of the setup/FRP-state inconsistency. Ask about applicable official updater fixes; do not flash, wipe, root, remove accounts or modify secure_frp_mode. Do not clear setup/Google service data or disable security protections.

Only after there is no outstanding verification challenge/restricted state, and the owner explicitly authorizes an ordinary install, use one diagnostic attempt:

```powershell
$adb = "$env:LOCALAPPDATA/Android/Sdk/platform-tools/adb.exe"
& $adb -d install -r '.\deliverables\SmishGuard-0.2.0-dev.apk'
```

This is not an FRP workaround or guaranteed solution: caller policy differs and MIUI may reject USB installs independently. Record the precise Success / Failure result. Do not use privileged flags or change security settings to force it. If the same FRP error returns, stop and refer to Xiaomi. A signature mismatch requires comparison with the installed signing certificate, not automatic uninstall. A concrete SDK/ABI/parse error justifies further packaging investigation; do not lower SDK settings speculatively.

After Success, owner opens SmishGuard and follows [the phone guide](private-phone-testing.md): confirm experimental model, scan fictional English/Taglish text, repeat with airplane mode plus Wi-Fi off, and record actual results privately. Automatic warnings/reporting remain disabled. Installation success alone does not prove launch or inference. Mark each physical check passed only after its own observation.

## Copyable Xiaomi support summary

M2103K19G; MIUI Global 14.0.6.0(TKSMIXM); approximately 81 GB free (owner-reported). Normal package installer reportedly crashes; alternate installer reports "Can't install packages while in secure FRP". Standalone development APK ph.smishguard.dev 0.2.0-dev, min API 26, ARM32/ARM64 libraries, valid v2 signature and ZIP/alignment checks; previously installed in emulator. No reset, account removal or security-setting modification attempted by this investigation. Please diagnose official setup/FRP-state consistency and installer crash on this same phone and provide a supported data-preserving resolution. Attach only actual Android/API version, three read-only state values, installer version and exact package-manager error when collected. Account recovery/proof of purchase must go privately to official support, not GitHub.

Remaining inputs: owner-authorized connection/read-only values and setup-prompt status; actual downloaded-file checksum; conditional installation authorization only once appropriate. No raw device logs or identifying tester data belong in this public repository.
