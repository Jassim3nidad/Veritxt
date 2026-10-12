# Branch integration — 13 October 2026

Merged the two outstanding branches into `main`: `codex/thesis-completion-package` at `ebefc30` and `origin/ui-liquid-glass` at `11fcf6c`. The previous remote main was `c0623c8`. Both histories are retained; feature branches are not deleted.

## Conflict decisions

- Keep the Veritxt Liquid Glass interface, privacy gate, English/Filipino resources, notification prompts and city removal.
- Preserve research/model variants, abstention, exact decision-policy and truncation details, transient checked-message display, cancellation/deadline handling and serialized inference. Incoming automatic checks use the same inference permit.
- Preserve the UI branch decision to enable experimental warnings for the original supplied model. Candidate, folded LR, comparison and mBERT variants keep their manual-only policy. This merge does not establish research validation or calibration.
- Keep variant-specific launcher names under the Veritxt brand. Reporting remains disabled. The standalone backend still requires a city and is not compatible with the current Android preview; document that mismatch explicitly.
- Reconcile privacy setup, report signatures and result expectations in instrumentation. Avoid duplicate reporting controls while the result explanation dialog is open.

## Verification

- Android debug APK, lint, JVM tests and instrumentation APK compilation passed.
- JVM: 32 tests, zero failures/errors, five private-parity tests skipped without their optional private inputs.
- API 36 emulator: the selected CompactResult, PrivacyAndCheckPrompt, PrivacyLifecycle, Recovery, ModelInitialization, Flows and Accessibility suites passed. The shipped-model screenshot case is intentionally skipped in the model-free debug variant.
- Research: 103 software tests passed; dependency check passed. Backend: 46 tests passed.
- Staged sharing review and whitespace/conflict checks passed. Emulator SMS examples use a fictional short sender rather than mobile-number-shaped literals.

Initial Android builds overlapped and hit the Kotlin incremental cache; stopped them and rebuilt in one process with fresh generated outputs. The initial emulator run exposed missing-model copy and duplicate-report-control mismatches, which were fixed. Android System UI also displayed an ANR dialog, causing focus failures; restarted the emulator and reran the selected suites successfully. Initial and final logs remain in ignored `output/merge-*.log` files.

This integration verifies the debug build and selected software/emulator flows. It does not rebuild every private model APK, retrain models, repeat research evaluations or establish physical-phone evidence.
