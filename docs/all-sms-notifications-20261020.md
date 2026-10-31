# Notify for every incoming SMS

Incoming SMS now posts one notification for every valid SMS while the incoming-SMS setting is on and Android permissions and the relevant notification channel are enabled. The settings subtitle is **Notify me about every SMS** in English and **Abisuhan ako sa bawat SMS** in Filipino/Tagalog. The consent and home-screen explanations describe the same behavior.

| Incoming result | Notification | Action |
|---|---|---|
| Low Risk | New text received | Check now |
| Medium Risk | New text received | Check now |
| High Risk | High Risk SMS | See why |
| Unable to assess, missing model, failed or busy inference | New text received | Check now |

High Risk warnings remain restricted to detectors that already permit automatic warnings. Other builds offer the neutral prompt for every SMS. A five-second cooperative inference deadline also falls back to a neutral prompt. The receiver rechecks privacy acceptance, incoming-SMS consent and permissions before posting. Notification checks use the channel being posted to, so muting High Risk alerts does not mute neutral prompts. App-level notification denial still suppresses both.

Message text, sender number and links never appear in notification extras or PendingIntents. Pending messages remain in process memory, expire after ten minutes, and are checked when their notification is opened. Sender metadata continues to support the existing optional manual blocking flow. Malformed, empty and oversized PDU assemblies remain excluded. Android delivery restrictions still apply; this receiver handles SMS broadcasts rather than RCS or other messaging apps.

## Model and delivery

The updated APK is `deliverables/Veritxt-All-SMS-20261020/Veritxt-0.3.0-Ham-Smishing-All-SMS.apk`. It uses the same package `ph.smishguard.svm.oldbinary` and existing debug signing key, allowing installation over the previous Ham/Smishing app.

The classifier is unchanged: SHA-256 `15cc0105b0e51e5342682ea36896c4436e515c39d165faf040476046b6b8059c`. The raw-SMS adapter, coefficients, calibration, model threshold and risk weights are unchanged. Earlier delivered APKs remain available in their original folders.

## Verification

- Current application assembly, test APK assembly, lint and JVM checks passed. JVM results: 46 passed, 11 conditional skips, zero failures or errors. Lint: zero errors and 12 warnings, including the now-unused historical `incoming_ask` string.
- Six new Android routing checks cover all risk levels, missing/invalid/failed/busy models, a thrown inference error, a timeout, disabled scanning, missing privacy acceptance and consent revoked during inference.
- Frozen-model Android parity passed: 515 model fixtures and 33 raw-SMS preparation fixtures.
- Four actual emulator modem SMS tests used the real bundled classifier. Low Risk (0/100), Medium Risk (40/100), High Risk (100/100) and Unable to assess each produced exactly one notification on the correct channel. Tapping each opened its exact received message and reproduced the expected risk result.
- Four existing Android privacy/action tests passed, covering the privacy gate, neutral Check now, High Risk See why, sender confidentiality and an expired pending message.
- Total Android tests: 15 on API36. The normal app launch passed. No physical-phone run is claimed.

Build logs and detailed results are under `output/all-sms-notifications-verification-20261020/` and the delivery folder. Rebuild with `scripts/build_old_binary_svm.ps1`; run `python scripts/verify_all_sms_notifications.py --output <fresh-output-directory>` after assembling the Android test APK. The host verifier only accepts a booted emulator and restores its prior airplane-mode setting.

The shared receiver and translations apply to all variants when rebuilt. This delivery packages and verifies the user-requested Ham/Smishing variant.
