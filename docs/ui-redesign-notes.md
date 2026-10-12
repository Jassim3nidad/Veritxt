# Veritxt UI — change notes

Branch: `ui-liquid-glass`. Prompts: [ui-redesign-prompt.md](ui-redesign-prompt.md) (round 1) and [veritxt-prompt.md](veritxt-prompt.md) (round 2).
Screenshots: `docs/screenshots/veritxt/api36/` (Android 16) and `docs/screenshots/veritxt/api30/` (Android 11), light and dark, English and Filipino, plus the incoming-SMS notification. Round-1 screenshots are in `docs/screenshots/redesign/`.

## Round 2 — what changed for users
- **Name and logo:** the app is now **Veritxt** ("Check the text before you tap"). New adaptive launcher icon (with Android 13 themed-icon layer), notification icon, and in-app mark. Package name `ph.smishguard` is unchanged so phones and tests treat it as the same app.
- **Privacy notice first:** on first open, Veritxt shows a privacy notice (what it checks, on-device only, what's saved, SMS is optional, rights under the Data Privacy Act of 2012 / RA 10173, contact). Nothing works until the user ticks "I have read and understood this notice" and taps **Agree and continue**. **Not now** closes the app. Only the notice version and date are stored. It can be reread in Settings → Privacy notice; clearing local data shows it again. Increase `PRIVACY_NOTICE_VERSION` to make everyone agree again after a wording change.
- **"New text received — check it?"** When incoming checks are on and an SMS arrives, Veritxt shows a neutral notification with **Check now** and **Dismiss**. It never shows the message, the sender, or a verdict. **Check now** opens Veritxt, fills in the text, and checks it. The text is held only in memory for 10 minutes; if it's gone, the app explains how to share the message instead.
- **Why incoming checks "didn't work" before:** the receiver stopped silently because no model was allowed to warn automatically (`automaticWarningsAllowed` was false in every detector).
- **Real automatic warnings (team decision, 2026-10-12):** the experimental supplied model now sets `automaticWarningsAllowed = true`. When it flags a new SMS, Veritxt posts **"Possible scam text"** (no message content, hidden on the lock screen); **See why** opens the experimental result with warning signs. Texts it doesn't flag stay silent. Builds without the model (e.g. this repo's debug build) fall back to the neutral "check it?" prompt. The model metadata still says `automatic_warnings_approved=false`; evaluation is pending, so results stay labelled experimental.
- **Settings → "Why didn't I get a notification?"** checks live: SMS permission, incoming checks on, notifications allowed, battery optimization. It also explains Autostart steps for the phone's brand (Xiaomi/Redmi/POCO, OPPO/realme/OnePlus, vivo, Huawei/Honor, Samsung), force stop, Android 13+ "restricted settings" for APK installs, and that RCS chat messages are not SMS. **Send a test notification** works without a real SMS.
- **Filipino:** every screen and notification is translated. **Language: System default / English / Filipino** in Settings and on the privacy screen (works on Android 8–16 via AppCompat per-app locales). The Filipino text is a draft — have a native speaker on the team review `values-b+fil/strings.xml` (keep `values-tl/strings.xml` identical).
- **"Your city" removed** from Settings, saved preferences (deleted on upgrade), and report metadata. Reports no longer carry a location.
- **Real blur:** on Android 12+ the floating nav bar blurs whatever scrolls under it (Haze 1.7.2). Android 8–11 and "Reduce transparency" use a solid bar.
- **Android 11 fixes found in testing:** the keyboard now closes when you leave the Check screen (it used to stay open over other screens), and a solid strip sits behind 3-button navigation so text doesn't show through the system buttons.

## Round 1 — Liquid Glass redesign
Glass panels over a drifting teal-green background, floating pill nav bar, Material icons, light/dark themes; verdict card (red / amber / green / grey) with score bar; "Warning signs found" pattern checks (labelled as not the model's reasoning); "What to do" step; report brand chips; grouped Settings with Reduce transparency.

## How to test the incoming-SMS flow
1. Settings → turn on **When a new SMS arrives** → agree → allow SMS (and notifications on Android 13+).
2. Emulator: `adb emu sms send 5550100 "BDO: Your account is on hold. Verify at bdo-verify.example.com"` — or send a real SMS to the phone.
3. Expect the "New text received" notification; tap **Check now**.
4. Automated: `IncomingPromptModemTest` (run with `-e modemPrompt true`, then send the SMS above within 60 s) and `PrivacyAndCheckPromptTest`.
5. Real Android 11 phone checklist: permission flow, notification appears, Check now works, after force-stop (no notification until the app is opened again — expected), after reboot.

## Kept the same (by design)
Model code and loading; the meaning of `automaticWarningsAllowed`; `FLAG_SECURE`; no saved UI state; text cleared after checking and on leaving the app; no internet permission; links never opened; "Experimental result" tag and uncalibrated-score wording; reporting disabled.

## Verification (Oct 12, 2026)
- Unit tests and lint pass.
- Instrumented suite: **21/21 pass on Android 16 (API 36)** and **21/21 on Android 11 (API 30)**, including the privacy gate, Check-now flow, expired-text message, and real modem SMS end-to-end tests.
- Build with a full JDK 17+ (`JAVA_HOME` pointing at a JDK, not a JRE).

## Known limits
- RCS / chat messages never reach SMS receivers — users must copy and paste them.
- Some phone brands block background apps until Autostart / battery settings are changed (see the in-app helper).
- On Android 12 and older, a notification posted while the app process is cold may appear in the system language until the app has been opened once.
- Glass panels sit over the already-blurred background; only the nav bar does a live blur of content.
- Real verdicts need the trained model (Jassim's part); screenshots use a test-only stub detector.
- Privacy-notice contact is a placeholder: set `privacy_contact_value` in `res/values/strings.xml`.
