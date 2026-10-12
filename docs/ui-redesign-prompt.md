# Prompt: SmishGuard UI and user-journey redesign (Liquid Glass style)

You are redesigning the UI and user experience of **SmishGuard**, a native Kotlin / Jetpack Compose Android app (minSdk 26, targetSdk 36) that checks SMS messages for smishing in Filipino, English, and Taglish. All checks run on the phone with an offline logistic-regression model. Users are ordinary Filipino phone owners, including older and less technical people.

Work in this repository. All UI currently lives in `android/app/src/main/java/ph/smishguard/MainActivity.kt` (one 259-line file, 5 screens: HOME, CHECK, RESULT, REPORT, SETTINGS, driven by `Screen` and `CheckState` in `CheckViewModel.kt`).

## Goal
Make the app feel calm, trustworthy, and modern, using an Apple-style **Liquid Glass** visual language, and make the main journey — *"I got a weird text → is it a scam? → what do I do?"* — take under 10 seconds and 2 taps.

## Visual direction: Liquid Glass, adapted for Android
- Translucent "glass" layers floating over a soft, slowly shifting background (blurred colour blobs in SmishGuard's teal-green family). Content sits on frosted panels with a thin light edge highlight and generous corner radius (24–32 dp), not on flat grey cards.
- Floating, pill-shaped bottom navigation bar made of glass, inset from the screen edges; the active tab has a brighter glass "lens".
- Primary actions are large glass pills with a tinted fill; secondary actions are clear glass.
- Smooth, physical motion: panels spring in, the verdict card morphs from the Check button, tab changes cross-fade. Use Compose animation APIs (`animate*AsState`, `AnimatedContent`, `SharedTransitionLayout`). Respect the system "remove animations" setting.
- Implementation:
  - Android 12+ (API 31+): real blur via `Modifier.blur` / `RenderEffect` on the background layer behind panels.
  - API 26–30: no blur available — fall back to a semi-opaque tinted surface (about 85% opacity) with the same shape and edge highlight. The app must look intentional on both.
  - Build reusable components (`GlassSurface`, `GlassButton`, `GlassNavBar`, `VerdictCard`) in a new `ui/` package instead of styling inline.
- Full light and dark themes. Keep SmishGuard teal-green as the brand colour; use red / amber / green only for verdicts.
- Use real Material Symbols icons; remove the text-character icons (⌂ ✉ ⚙).

## Readability rules (glass must not hurt legibility)
- Text on glass must meet WCAG AA contrast (4.5:1 body, 3:1 large text) in both themes, over the busiest part of the background. Add a darker/lighter scrim behind text if needed.
- Support font scaling up to 200% without clipping; minimum 48 dp touch targets.
- Provide a "Reduce transparency" option in Settings (and follow system high-contrast) that swaps glass for solid surfaces.
- Keep every existing TalkBack label, heading semantics, and content description working.

## User journeys to design
1. **First launch (onboarding):** 2–3 short swipeable glass cards — what SmishGuard does, privacy ("stays on your phone"), "warns, never blocks". One "Get started" button. Language choice: English / Filipino. No permission requests here.
2. **Check a message (main journey):** Home shows one big "Check a message" glass button plus a "Paste from clipboard" shortcut. Sharing an SMS into the app goes straight to Check with the text filled in. One tap on "Check" → result.
3. **Result:** a large glass verdict card that morphs in, coloured by outcome:
   - Likely scam (red), Unsure (amber), Not flagged (green), plus clear states for "Model not installed" and "Couldn't check".
   - A simple score bar, not a raw decimal.
   - "Why it looks suspicious" hints from simple rules: brand mentioned, link domain not on the official list (use `SafeDomain`), urgency words, OTP/PIN requests. Label these as **hints, not the model's explanation**.
   - One clear next step ("Don't tap the link. Open the BDO app yourself."), then "Check another" and "Report".
4. **Report:** brand chosen with tap chips, exact metadata preview, clear "not available yet" state (reporting is disabled in this build).
5. **Settings:** grouped glass list — Protection (scan incoming SMS, notifications), Preferences (city, language, reduce transparency), Privacy (clear local data). Explain each permission in one line, in plain words, right before asking.
6. **Turning on auto-scan:** consent sheet → system permission → confirmation; handle "denied" and "notifications off" with friendly recovery, not dead ends.

## Copy
- Short, warm, plain language; sentence case; no exclamation marks. Provide English and Filipino strings via `strings.xml` / `values-fil/` (move all hard-coded text out of Kotlin).
- Cut the repeated disclaimers to **one line per screen**, but keep their meaning.

## Do not change (hard constraints)
- Privacy behaviour: `FLAG_SECURE`, no saveable state (`LocalSaveableStateRegistry provides null`), text cleared after checking, `endSession()` on stop, no internet permission, links never opened.
- Honesty: while the model is experimental, every result must show an "Experimental result" tag and must not claim certainty. Automatic warnings and reporting stay disabled. Never present the score as a probability unless the model is calibrated.
- Detection, model loading, and `IncomingSmsReceiver` logic. This is a UI/UX change only.
- Existing tests must still pass: `AccessibilityTest`, `FlowsTest`, `DevelopmentFlowTest`, `VisualReviewTest`, `PrivacyLifecycleTest`, and unit tests. Update test selectors only where text intentionally changed.

## Deliverables
1. Before coding, a short plan: component list, screen-by-screen layout, and the journey changes.
2. The implementation, split into small commits (theme and glass components → navigation → each screen → strings and Filipino translation).
3. Updated screenshots in `docs/screenshots/` (light and dark, API 26 fallback and API 34 blur).
4. A short note listing what changed for users and any trade-offs (e.g. no blur on older phones).

Build with `./scripts/build.ps1 -Variant development` and run `:app:lintDebug :app:testDebugUnitTest` before finishing.
