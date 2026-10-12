# Prompt: Veritxt rebrand, privacy consent, "check this SMS?" flow, Filipino, real glass

You are continuing work on the Android app in this repository (Kotlin + Jetpack Compose, minSdk 26, targetSdk 36), on branch `ui-liquid-glass`. Read `docs/ui-redesign-notes.md` first: it describes the Liquid Glass redesign that is already done (glass components in `ui/Glass.kt`, warning-sign hints in `ui/Hints.kt`, screens in `MainActivity.kt`).

We are the **frontend team**. The trained model is handled separately by Jassim; do not change model code. The UI must keep working in all three model states: *Model not installed*, *experimental model*, and a future approved model.

Do the work in the order below, one commit per section, and keep every existing test passing.

---

## 1. Rename the app to **Veritxt**
- Change the user-visible name everywhere: launcher label, in-app header, onboarding, notifications, notification channel name, dialogs, and the docs README title. The tagline is "Check the text before you tap".
- **Keep** `applicationId`, the Kotlin package `ph.smishguard`, and class names. Changing them would make phones treat it as a different app and would break the tests. List them as a possible later change.

## 2. New logo
- The source artwork is `docs/brand/veritxt-icon.svg` (a teal rounded square with a white chat bubble and a check mark). The full wordmark is `docs/brand/veritxt-wordmark.svg`.
- Create an **adaptive launcher icon**: vector foreground (bubble and check inside the 66 dp safe zone), solid `#1F6457` background, and a **monochrome** layer for Android 13 themed icons. Add a round icon. Remove the old `ic_shield` launcher usage.
- Create a single-colour **notification small icon** (white bubble-and-check silhouette, no background).
- Use the mark in the in-app header and on the first onboarding card.

## 3. Data privacy notice with "Agree to continue"
- The **very first screen** on first open must be a privacy notice. Nothing else, including onboarding or the Check screen, is usable until the user agrees.
- Content, in plain words and short sections:
  - what Veritxt processes (SMS text you paste, share, or allow it to receive);
  - that processing happens only on this phone;
  - that message text is not stored or sent, and there is no internet permission;
  - what *is* saved locally (consent, settings);
  - that SMS access is optional and can be turned off;
  - your rights under the **Data Privacy Act of 2012 (RA 10173)**;
  - a research-team contact placeholder.
- Controls:
  - a checkbox "I have read and understood this notice";
  - an **Agree and continue** button that only works when the box is checked (keep it enabled, and show a short inline message if it is tapped while unchecked);
  - a "Not now" button that closes the app.
- Store only `privacy_notice_version` and the date it was accepted, in DataStore, with no personal data. Show the notice again whenever `PRIVACY_NOTICE_VERSION` is increased.
- Add **Settings → Privacy notice** to reread it, and include the consent in "Clear local data" (clearing it shows the notice again).

## 4. Remove the "Your city" setting
- Remove the city picker from Settings and anywhere else in the UI.
- Remove `city` from `Preferences`, `PreferencesRepository` (delete the old `manual_city` key on first launch after upgrade), and `ReportPayload` (drop the `"city"` field and the "city required" rule).
- Update the affected tests (`CoreTest`, `SuppliedModelTest`, and any test that selects a city) and the docs that mention city dashboards (`docs/privacy.md`, `docs/project-authorization.md`). Add a note that reports no longer carry a location.

## 5. Incoming SMS: "New text — check it?" (advisor's request) and fix "scanning doesn't work"

### Why it currently does nothing
`IncomingSmsReceiver` returns early when `detector.automaticWarningsAllowed` is false (`sms/IncomingSmsReceiver.kt`), and **every detector leaves it false** (`model/Detector.kt:37`). This is deliberate: `docs/model-contract.md` says the model is not approved for automatic warnings. So even with permission granted and scanning on, no notification ever appears.

### New behaviour (allowed because it shows no verdict)
- When scanning is on and an SMS arrives, post a **neutral** notification:
  - title "New text received"
  - body "Check it with Veritxt before you tap any link."
  - actions **Check now** and **Dismiss**

  It must not say "scam" or "safe", so it is not a model-driven warning.
- **Check now** opens Veritxt on the Check screen with the message already filled in, runs the check automatically, and shows the normal Result screen (with the "Experimental result" tag when applicable).
- Only when `detector.automaticWarningsAllowed == true` (a future approved model) may the receiver run the model in the background and post a verdict notification ("Possible scam"). Keep that path gated exactly as it is now.
- Settings: replace the single switch with **"When a new SMS arrives": Ask me to check (default) / Off**, plus a **Send a test notification** button that posts a sample notification without needing a real SMS.

### Privacy rules for this flow
- Never put message text, the sender, or a link in the notification. Use `VISIBILITY_PRIVATE` with a public version that reads "New text to check".
- Keep the SMS text in **memory only** (an in-process holder keyed by a random id). The `PendingIntent` carries only the id.
- The text expires after 10 minutes, or once it has been checked. Never write it to disk, logs, or saved state.
- If the app process was killed and the text is gone, show: "This message is no longer available. Open your messaging app and share it to Veritxt."
- One notification per message, using a unique id. Cancel it after Check now.

### Fix "sometimes the scan / warning doesn't work on the phone"
Add a **Settings → "Why didn't I get a notification?"** helper that checks each item live and shows how to fix it:
1. SMS permission granted (`RECEIVE_SMS`).
2. Notifications allowed, and the channel not muted (`POST_NOTIFICATIONS` on Android 13+).
3. The app was not force-stopped. Force-stopped apps get no broadcasts until they are opened again.
4. Battery optimisation. Open `ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS`; do **not** request `REQUEST_IGNORE_BATTERY_OPTIMIZATIONS`. Add brand-specific "Autostart" steps for the phones common in the Philippines: Xiaomi/Redmi/POCO, OPPO, realme, vivo, Huawei, and Samsung.
5. Android 13+ sideloaded APK: explain App info → ⋮ → **Allow restricted settings** before the SMS permission can be granted.
6. RCS / "chat features" messages in Google Messages and Samsung Messages are **not SMS** and will never trigger the receiver. Say so plainly.

Also check that the receiver finishes within the broadcast time limit (it uses `goAsync` with a 7 s timeout) and works for both SIMs.

### Tests
- An instrumented test: deliver an SMS on the emulator, assert the neutral notification appears, and check it contains no message text.
- A test that "Check now" opens the Check screen with the text filled in and produces a result.
- Manual test on the emulator:
  `adb emu sms send 5550100 "BDO: Your account is on hold. Verify at bdo-verify.example.com"`
- Manual checklist for a **real Android 11 phone**: permission flow, notification, Check now, after force-stop, and after reboot.

## 6. Filipino translation and language setting
- Move **every** user-visible string out of Kotlin into `res/values/strings.xml`, with plurals where needed.
- Add Filipino in both `res/values-fil/` and `res/values-tl/`, because older Android versions report Filipino as `tl`.
  - Use natural, conversational Filipino with common Taglish where Filipinos would use it (OTP, link, app).
  - Mark the file for review by a native speaker on the team.
- Add **Settings → Language: System default / English / Filipino** using the per-app language API:
  - `locales_config.xml` with `android:localeConfig`;
  - `AppCompatDelegate.setApplicationLocales`, which needs `androidx.appcompat` and the `AppLocalesMetadataHolderService` with `autoStoreLocales` for Android 12 and below;
  - or switch `MainActivity` to `AppCompatActivity`.

  It must work on Android 8 through 16.
- Add a language choice to the first onboarding card.
- Existing tests select English text. Force the English locale in the test runner, or switch the selectors to resource ids.

## 7. Real blur behind glass (Haze)
- Add the **Haze** library (`dev.chrisbanes.haze`). Use a current stable version and confirm it resolves before writing code.
- Mark the background and the scrolling content as the blur source, and apply the blur to the floating nav bar, the glass panels, and the verdict card.
- Android 12+ (API 31+) gets real blur. Below that, Haze falls back to a translucent tint: make the fallback opaque enough for readable text.
- With **Reduce transparency** on, use no blur and solid surfaces.
- Once the blur works, the nav bar can become translucent again. Recheck WCAG AA contrast for all text over the blur, in both themes.

## 8. Android 11 testing
- Use the emulator AVD `android11_phone` (API 30, already installed) as well as the API 36 `medium_phone`.
- Capture every screen in light and dark mode on both, and save them in `docs/screenshots/veritxt/api30/` and `.../api36/`.
- Pay special attention to the no-blur fallback, notification behaviour, and the permission flow on Android 11.

---

## Do not change (hard constraints)
- Model code, model loading, and the meaning of `automaticWarningsAllowed`. No verdict may be shown in a notification unless it is `true`.
- Privacy:
  - `FLAG_SECURE`
  - no saved UI state (`LocalSaveableStateRegistry provides null`)
  - text cleared after checking and `endSession()` on stop
  - no internet permission
  - links never opened
- Honesty: keep the "Experimental result" tag, the uncalibrated-score wording, and "These are simple pattern checks, not the model's reasoning".
- All tests must pass: unit tests, lint, and the full instrumented suite (`AccessibilityTest`, `FlowsTest`, `DevelopmentFlowTest`, `PrivacyLifecycleTest`, `RedesignReviewTest`, …). Keep 48 dp touch targets and TalkBack labels.

## Deliverables
1. A short plan before coding.
2. One commit per section above.
3. Screenshots on API 30 and API 36, light and dark.
4. An update to `docs/ui-redesign-notes.md`: what changed, how to test the incoming-SMS flow, and the known limits (RCS, OEM battery settings, model approval).

Build with JDK 17 or newer (`JAVA_HOME` pointing at a full JDK, not a JRE), then run `:app:lintDebug :app:testDebugUnitTest` and the connected tests on both emulators.
