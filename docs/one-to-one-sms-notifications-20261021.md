# One SMS, one Veritxt notification

Each processed incoming SMS has its own Veritxt report, including when multiple messages have the same body and sender. The existing risk gauge, initial score/category and View report/Dismiss actions remain on every report. Multipart SMS segments still assemble into one message and produce one report.

Previously, Veritxt already posted once per received SMS, but Android could put several reports into an automatic bundle. Test messages also left notifications in the separate Android Messages app after their Veritxt reports had been opened or dismissed. A screenshot of old Messages notifications therefore did not represent the number of pending Veritxt reports. Veritxt checks new arrivals while enabled; it does not reconstruct reports from old inbox messages.

The updated notification builder assigns an opaque UUID tag per message. The tag prevents two messages from overwriting each other even if their integer notification hashes collide. Open and Dismiss PendingIntents have distinct opaque data URIs, so a request-code collision cannot redirect an older report. Cancellation supplies both the tag and integer ID; opening or dismissing one report removes only that report and its matching pending message. No new persistent history, raw message/sender display, model change or permission was added.

Android controls visual bundling. A bundle header is a platform display item rather than another SMS report. On the API 36 emulator, assigning different group keys still allowed the system to bundle reports. The app uses standard notification presentation and retains one child report per SMS under any platform bundle. The count verifier excludes Android's generated summary and checks the actual SMS reports. See [Android notification groups](https://developer.android.com/develop/ui/compose/notifications#notification-updates-and-groups) and [Android 16 GroupHelper](https://android.googlesource.com/platform/frameworks/base/+/android16-release/services/core/java/com/android/server/notification/GroupHelper.java).

Android Messages notifications are managed by that separate application. This change does not disable or modify them. Android permissions, muted channels, force-stop, background policies and pending-message expiry still apply.

Build with `scripts/build_old_binary_svm.ps1`. Verify with `python scripts/verify_all_sms_notifications.py --initial-reports --one-to-one --linked-cashback --output <fresh-output-directory>`. The added real-modem test sends five identical SMS from the same sender and requires exactly five Veritxt SMS reports, five tags/notification keys, and independent dismissal/opening of all five. Any system-generated bundle header is recorded separately.

## Delivery and verification

Updated APK: `deliverables/Veritxt-One-SMS-One-Report-20261021/Veritxt-0.3.0-One-SMS-One-Report.apk`, same package and existing debug signing key. APK SHA-256: `82657a0ded1b416b02b630cd0c81d76d9f46255bb71abca847289032afa82f52`.

All 23 Android checks passed on API 36. Five identical actual emulator SMS from sender 5550601 produced exactly five reports, five distinct tags and five distinct notification keys. Android added one platform bundle summary, recorded separately. Dismissing one report left the remaining four; opening each remaining report removed only that report and opened the matching SMS/sender. No SMS reports remained after all five actions. Existing three-message routing, five risk/model modem cases, notification privacy, localization, gauge and frozen-model parity checks passed. Unit tests: 53 passed, 11 conditional skips, no failures/errors. Lint: zero errors, 15 warnings. APK v2 signature verified. The model and raw-SMS adapter are byte-identical to the previous delivery; no physical-phone verification is claimed.

The normal installed app also received three fictional messages and displayed separate Low, Medium and High Risk report cards. The delivery preview stacks crops of those actual cards captured while scrolling the same notification shade. Full capture metadata and verification are under `output/one-to-one-sms-verification-final-20261021/`. Earlier deliveries are preserved.
