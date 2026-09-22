# SmishGuard: remote tester checklist

Same phone only. Status: unresolved; installation/opening/offline scanning remain pending. No APK recheck is needed for this collection. Send results privately to the group, not GitHub.

## Path 1 — phone only (Taglish)

1. Sa phone, check kung may **Finish setup / Verify your account / Unlock after factory reset** prompt. Sabihin lang kung meron o wala. Kung meron, owner lang ang mag-complete sa official screen. Huwag i-send ang email, password, PIN o verification code.
2. Kung normal nang nagagamit at walang pending verification, puwedeng normal restart once. Buksan ulit ang existing SmishGuard APK gamit ang usual installer. Kapag nag-crash, note lang ang installer name/version at kung kailan nag-close. Sa alternate installer, reproduce once at kunan ang exact error dialog. Hindi kailangang paulit-ulit mag-install.
3. Send **cropped/redacted** screenshot ng error at Android/MIUI version lang. Takpan ang account address, pangalan, notifications, phone/serial/IMEI numbers at ibang personal info. Para sa setup prompt, mas okay ang typed prompt title lang kaysa screenshot na may account details. Huwag isama SMS o inbox.
4. I-send privately: pending setup yes/no; Android version; installer name/version; exact error; nangyari ba ulit after restart; main owner profile ba o Second Space/ibang profile. Kung hindi alam, sabihin unknown.

Phone-only evidence can establish visible prompts, the exact error and reproducibility. It cannot read secure_frp_mode or prove whether the system state is stale, distinguish the installer's crash cause, or confirm package-manager/receiver execution. Walang prompt does not prove restricted FRP is off. Huwag reset/remove account/bypass; kung verification remains blocked, use Xiaomi support below.

## Path 2 — his own Windows computer

No Android Studio, repository, APK, model or Python is needed. The diagnostic ZIP contains this README and one read-only PowerShell script. It does not install apps, change phone settings, save logs or upload anything.

1. Extract the diagnostic ZIP. Download **SDK Platform-Tools for Windows** from Google's official page: https://developer.android.com/tools/releases/platform-tools . Accept its terms and extract the whole `platform-tools` folder beside `phone-install-diagnostics.ps1`. Keep its DLLs with adb.exe. Expected layout:

```text
SmishGuard-diagnostics/
  README.md
  phone-install-diagnostics.ps1
  platform-tools/
    adb.exe
    (other official Platform Tools files)
```

2. On the unlocked phone, Settings > About phone/My device > All specs > tap MIUI version seven times; Additional/More settings > Developer options > **USB debugging**. Connect to **his own trusted PC** with a data cable, accept the phone's RSA authorization prompt. This is ordinary USB debugging only: no OEM unlocking, extra security overrides, wireless debugging, port forwarding or internet ADB. If official setup blocks access, stop. Xiaomi instructions: https://www.mi.com/global/support/article/KA-06515/ .
3. Open PowerShell in the extracted diagnostic folder (Explorer address bar: type `powershell`, Enter). Run:

```powershell
.\phone-install-diagnostics.ps1
```

If Platform Tools is elsewhere, use `-Adb 'C:\your-folder\platform-tools\adb.exe'`. No administrator access is needed. If Windows blocks script execution, do not change execution policy or disable security. Open the script in Notepad, review it, then paste its contents into this PowerShell window, replacing the first line with `$Adb = (Join-Path (Get-Location) 'platform-tools/adb.exe')`. On a managed PC where this is also prohibited, stop and use Path 1; do not evade organizational controls.
4. Copy back only the printed model/OS/API/build/security patch/ABI values, three setup-state values, SmishGuard presence and any `STOP` line. The script suppresses native error details and does not request serials, accounts, SMS or logs. Tell us if Second Space/another profile is used: settings are read for owner user 0. `null`/`unavailable` is inconclusive, not FRP-off proof. Send text privately, not a full desktop screenshot. Do not send `adb devices` output.
5. If no connection: unlock/accept the prompt; connect only this Android phone; try another data cable/USB port. Use official vendor/Android driver guidance if Windows needs a driver, not random driver packs: https://developer.android.com/studio/run/oem-usb . Do not change security toggles to force it. After collecting, disconnect and turn USB debugging off if no longer needed.

Only read-only diagnosis is included. No ADB installation is attempted while restricted-state/account verification remains unresolved. Future installation and offline scanning require actual results before being marked passed; automatic warnings/reporting remain disabled.

## Exact Xiaomi support request (copy/paste)

Hello Xiaomi Support. Please help resolve an installation restriction on my existing phone without erasing data or replacing the phone. Model: **M2103K19G**. Firmware: **MIUI Global 14.0.6 / 14.0.6.0(TKSMIXM)**. Available storage: approximately **81 GB**. The normal package installer reportedly crashes; another installer displays exactly **"Can't install packages while in secure FRP"** while installing **SmishGuard-0.2.0-dev.apk**, package **ph.smishguard.dev**. The developer verified the standalone APK's signature and structure and previously installed it on an emulator. Please determine whether official setup/account verification is incomplete or the firmware retains an inconsistent restricted-FRP state, and diagnose the installer crash. Please provide a supported, non-destructive resolution on this same phone; no factory reset, wipe, flashing, root, account removal or security bypass. I can provide the visible setup status, Android version, installer version and narrowly scoped read-only state values when available. Please direct any necessary ownership/account verification through your official private process.

Add only actual collected observations, not guesses. Xiaomi's official owner-verification guidance: https://www.mi.com/global/support/faq/details/KA-42580/ . It describes completing the existing verification challenge or obtaining after-sales assistance with proof of purchase when needed; this is not an instruction to reset. Submit to Xiaomi's official support channel, never send account credentials to the project team.
