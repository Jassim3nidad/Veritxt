# Automatic initial reports for incoming SMS

With privacy acceptance, incoming SMS consent, SMS permission and notifications enabled, new SMS are scanned on the phone automatically in builds that already permit automatic analysis. Notifications now show the initial report without requiring a tap first:

| Result | Title | Compact report |
|---|---|---|
| Low Risk | Low Risk SMS | Risk Score: 0–29/100 · model category, when available |
| Medium Risk | Medium Risk SMS | Risk Score: 30–69/100 · model category, when available |
| High Risk | High Risk SMS | Risk Score: 70–100/100 · model category, when available |
| Unavailable or unassessable | Unable to assess SMS | Automatic scan unavailable; open Veritxt to check again. No score. |

The category and risk level are separate outputs. For example, Smishing can have Medium Risk when only the model signal contributes to the evidence index. Scores remain provisional evidence indices, not fraud probabilities. The expanded report includes a short analysis and that qualification. **View report** opens the full analysis for the exact received message, rechecking it through the existing app flow.

Nearby incoming messages retry a busy inference permit within the existing five-second cooperative inference deadline. Every processed valid SMS gets a separate notification; Android may group them. Privacy, consent and permissions are rechecked before publication. The receiver retains its seven-second cooperative outer deadline. No persistent queue or inbox scan was added. Android force-stop, battery policies, denied permissions or muted channels still limit delivery.

Message bodies, sender numbers and links stay out of notification extras and PendingIntents. Initial reports contain only fixed localized labels, category and risk index. High Risk reports retain the secret lockscreen visibility; other reports retain a generic public lockscreen version. Pending messages stay in process memory for up to ten minutes. Closing or restarting the process may make an old pending message unavailable. Detection parameters, preprocessing, risk weights and thresholds are unchanged.

English, Filipino and Tagalog notification and consent copy are updated. Existing manual-only model variants remain manual-only and show an unscored automatic-report fallback.

Build with `scripts/build_old_binary_svm.ps1`. Verify the current Ham/Smishing APK using `python scripts/verify_all_sms_notifications.py --initial-reports --linked-cashback --output <fresh-output-directory>`. The host verifier accepts only a booted emulator and restores its previous airplane-mode setting. Build and device verification are recorded alongside the dated APK after completion.

## Delivery and verification

The updated APK is `deliverables/Veritxt-Auto-SMS-Reports-20261021/Veritxt-0.3.0-Auto-SMS-Reports.apk`, package `ph.smishguard.svm.oldbinary`, signed with the existing debug key. It installs over the previous Ham/Smishing app. Earlier deliveries are preserved.

Assembly, lint and JVM checks passed: 53 unit tests passed, 11 conditional skips, no failures/errors. Lint reported zero errors and 12 warnings. All 21 Android checks on API 36 passed: nine routing/consent/failure/timeout/concurrency/localization checks, frozen-model parity, the existing linked-cashback flow, five actual modem cases, one three-message modem burst, and four existing notification privacy/action checks. Parity covers 515 frozen model fixtures and 33 raw-SMS preparation fixtures. The real modem cases showed Low Risk 0/100, Medium Risk 40/100, High Risk 100/100, an unscored Unable to assess result, and the existing linked-cashback High Risk 70/100 result directly in notification extras. Each opened result matched its initial risk score. The three-message burst verified separate report IDs and exact received-message/sender routing for every report.

A normal application launch also displayed a High Risk 100/100 · Smishing initial report, with the short analysis and View report action, before any manual scan. The delivery includes a crop of that actual emulator notification. No physical-phone run is claimed.

Detailed results: `output/initial-sms-reports-verification-final-20261021/verification.json`. The delivery includes the verification summary, SHA-256 sums, v2 signature verification and build log. Classifier SHA-256 remains `15cc0105b0e51e5342682ea36896c4436e515c39d165faf040476046b6b8059c`; APK SHA-256 is `cf22ddc94f1901a306e945fd818d953845c3b61f1724fb48cfc6f8f66d0f8feb`.
