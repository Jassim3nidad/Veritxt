# Prompt: make the result score easy to understand

You are improving the **Result screen** of Veritxt, an Android app (Kotlin + Jetpack Compose) that checks SMS messages for scams in Filipino, English, and Taglish. Start from the latest `main` (`git pull`). The Result screen is `ResultScreen` in `android/app/src/main/java/ph/smishguard/MainActivity.kt`; all text is in `res/values/strings.xml` with Filipino in `res/values-b+fil/` and `res/values-tl/` (keep those two identical).

## The problem
Ordinary users find the current score confusing. The result card shows:
- a score bar,
- "Uncalibrated model score: 0.8700. This is not a likelihood of fraud.",
- "Above provisional threshold (0.5).",
- "Reporting is disabled in this build."

Words like *uncalibrated*, *threshold*, and a 4-decimal number mean nothing to most people, and "this is not a likelihood" contradicts the bar they are looking at.

## Goal
A user should understand the result in **3 seconds**: what Veritxt thinks, how strongly, and what to do. Technical details stay available for the research team, but out of the way.

## What to build
1. **Plain-language level instead of a number.** Map the model output to one of three levels and show it as a short label with a simple visual (for example 3 segments or a gauge that fills to Low / Medium / High):
   - **High warning signs** — the model flagged it (above the threshold).
   - **Some warning signs** — not flagged, but 2+ pattern warning signs (the existing amber case).
   - **Few warning signs** — not flagged and fewer than 2 pattern signs.
   Do not say "safe", "% chance", "probability", or "accuracy". The model is uncalibrated, so a percentage would be misleading.
2. **One sentence of meaning** under the label, e.g. "Veritxt found strong signs this text is a scam." / "Some parts of this text look like scams." / "Veritxt didn't find strong scam signs, but stay careful."
3. **Keep the honesty, but make it human.** Replace the three technical lines with one line: "Experimental — Veritxt can be wrong. Always double-check with the official app or hotline." Keep the existing "Experimental result" pill.
4. **"How is this decided?" expandable section** (collapsed by default) for the research team and thesis panel. Inside: the raw model score (2 decimals is enough), the 0.5 provisional threshold, that the score is uncalibrated and not a probability, and that reporting is disabled. This keeps the technical facts available without confusing users.
5. **Keep everything else** on the Result screen: warning signs list, "What to do", buttons.
6. **Filipino**: add every new string in English and Filipino (natural, conversational; native-speaker review needed).
7. **Accessibility**: the level must not rely on colour alone (label + icon + segments), TalkBack reads the level and sentence, contrast passes WCAG AA in light and dark, works at 200% font size.

## Also fix (seen on a real Infinix Note 10 Pro, Android 11, XOS, dark mode)
- **"Check message" button contrast:** pale green fill with pale text is hard to read. Use the primary colour with `onPrimary` text in both themes and check WCAG AA.
- **"Clear message" wraps to two lines** next to "Paste". Shorten to "Clear", or stack the buttons when they don't fit.
- **Background is very green in dark mode:** tone down the colour blobs so text panels stay readable.
- **Infinix / Tecno / itel (Transsion XOS)** are missing from the Autostart helper. Add: "Phone Master → Auto-start management → allow Veritxt; also Settings → Battery → App battery saver → Veritxt → No restrictions." XOS kills background apps aggressively, so this matters for automatic warnings.

## Do not change
- Model code, `SuppliedDetector`, the 0.5 threshold, or when automatic warnings fire.
- Privacy behaviour (`FLAG_SECURE`, text cleared after checking, no internet).
- The "Experimental result" pill and the "These are simple pattern checks, not the model's reasoning" note.
- Never present the score as a probability or percentage while the model is uncalibrated.

## Tests
- Update tests that look for the old strings (`DevelopmentFlowTest` checks "Uncalibrated model score:" and "Reporting is disabled in this build."; they should now find these inside the expanded "How is this decided?" section, or check the new level text).
- Keep the check that no "probability" text appears for the experimental model.
- Add a test that each level (high / some / few) shows the right label and sentence.
- Run unit tests, lint, and the instrumented suite on Android 11 (API 30) and Android 16 (API 36); capture before/after screenshots of the Result screen in light, dark, and Filipino into `docs/screenshots/veritxt/score/`.

## Deliverables
1. A short plan with a mockup of the new result card before coding.
2. The change in small commits.
3. Before/after screenshots and a note in `docs/ui-redesign-notes.md`.
