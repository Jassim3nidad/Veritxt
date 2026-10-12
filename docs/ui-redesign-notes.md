# UI redesign (Liquid Glass) — change notes

Branch: `ui-liquid-glass`. Prompt: [ui-redesign-prompt.md](ui-redesign-prompt.md). Screenshots: `docs/screenshots/redesign/` (light and dark, Android 16 emulator).

## What changed for users
- **Look:** translucent glass panels over a soft, slowly drifting teal-green background; floating pill navigation bar; Material icons instead of text symbols; light and dark themes.
- **Home:** one large "Check a message" card, a "Paste from clipboard" shortcut, status pills (model, incoming SMS), and one scam tip. Repeated disclaimers cut to one line.
- **Onboarding:** three swipeable cards (what it does, privacy, limits) with page dots.
- **Check:** glass text field, Paste and Clear buttons side by side.
- **Result:** coloured verdict card that springs in — red "Likely scam", amber "Not flagged, but be careful" (model didn't flag it but 2+ warning signs), green "Not flagged", grey for no model / errors. Animated score bar. New "Warning signs found" list (brand mentioned, link to a non-official domain, urgency, OTP/PIN request, prize bait), clearly labelled as pattern checks, not the model's reasoning. A "What to do" step that names the brand when found.
- **Report:** brand chosen with tap chips, back link to the result, clear "not available" notice.
- **Settings:** grouped Protection / Preferences / Privacy lists; new **Reduce transparency** switch (solid surfaces for easier reading).

## Kept the same (by design)
`FLAG_SECURE`, no saved UI state, text cleared after checking, no internet permission, links never opened, "Experimental result" tag and uncalibrated-score wording, disabled automatic warnings and reporting, detection and SMS receiver logic.

## Code
- New `ui/Glass.kt` (GlassBackground, GlassSurface, GlassButton, GlassNavBar, StatusPill, ScoreBar) and `ui/Hints.kt` (rule-based warning signs).
- `CheckViewModel` computes hints at check time (only the summary is kept; the message text is still cleared).
- `PreferencesRepository` stores `reduce_transparency`.
- Added `material-icons-extended`.
- Tests: new `HintsTest` (5 unit tests) and `RedesignReviewTest` (test-only screenshots with a fixed stub detector). All 18 instrumented tests, unit tests, and lint pass.

## Trade-offs and not done yet
- **Blur:** Compose can't blur content *behind* a panel without an extra library (e.g. Haze), so the background is blurred and panels are translucent, and the nav bar is opaque so labels stay readable.
- **Filipino translation / language setting:** not done. Text is still hard-coded in Kotlin; moving it to `strings.xml` + `values-fil/` is the next step.
- **Android 8–11 fallback:** coded (more opaque panels, no blur) but not screenshotted — no API 26 emulator image is installed.
- The real verdicts need the trained model, which is not in this repo; screenshots use a test-only stub.
