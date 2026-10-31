# Risk gauge in incoming-SMS notifications

The user requested a dial like the supplied visual reference. The app draws an original gauge with Android Canvas and supplies it as the native notification large icon, alongside the existing initial report. The dial is generated from the actual risk index for each message; it is not a fixed illustration or a copied stock image. Android controls its size and placement in the notification.

The needle traverses 270 degrees as the evidence index rises from 0 to 100. Green segments cover 0–29, yellow/orange cover 30–69, and red segments cover 70–100, matching the existing risk thresholds. The number appears on the dial and remains in the accessible notification text. Unavailable assessments show a gray dial, a question mark and a dash, with no needle and no numerical score.

The native expanded text analysis, View report and Dismiss actions are preserved. No model, risk weight, threshold, permission, pending-message lifetime or automatic-SMS routing change was made. No message text, sender or URL is rendered into the gauge. The public lockscreen notification has no gauge; High Risk reports retain their secret visibility.

Build: `scripts/build_old_binary_svm.ps1`. Verify: `python scripts/verify_all_sms_notifications.py --initial-reports --linked-cashback --output <fresh-directory>`. Routing checks assert a gauge on each report, its absence from the public lockscreen version, and distinct needle endpoints for 0/100 and 100/100. Actual modem checks also assert the gauge is present.

## Delivery and verification

Updated APK: `deliverables/Veritxt-SMS-Risk-Gauge-20261021/Veritxt-0.3.0-SMS-Risk-Gauge.apk`, same package `ph.smishguard.svm.oldbinary` and existing debug key. Install over the previous Ham/Smishing app. The delivery contains an actual normal-app notification preview, verification JSON, build log, signature verification and SHA-256 sums. Previous APKs are preserved.

Build, lint and JVM checks passed: 53 unit tests passed, 11 conditional skips, zero failures/errors. Lint: zero errors, 13 warnings, including the optional KTX createBitmap suggestion. All 22 Android checks on API 36 passed, covering routing, gauge endpoints, unavailable and failed scans, privacy, localization, five actual modem cases, three SMS arriving together, and exact notification actions. The classifier and raw-SMS adapter passed 515 and 33 frozen parity fixtures respectively. Their bytes match the previous delivery. No physical-phone test is claimed.

The normal installed app also displayed a gauge pointing into red for a fictional High Risk 100/100 SMS, alongside its score/category, expanded analysis and View report action. Detailed evidence is under `output/sms-risk-gauge-verification-20261021/`. APK SHA-256: `316dbc5388d635ba9687d23d1c80474aa459f11ff78fadf2752f40e1cee79160`.
