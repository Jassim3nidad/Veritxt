# Compact result verification — 25 September 2026

Started from a clean `codex/thesis-completion-package` at `f642487`. Fetch confirmed
no divergence. Existing work and all older deliverables were preserved.

## Actual checks

| Check | Outcome |
|---|---|
| Development assemble and lint | Passed via `scripts/build.ps1 -Variant development`; lint rerun after test updates |
| JVM tests | 10 passed: CoreTest 6, AssessabilityTest 4; ExportParityTest 1 explicitly skipped because no separate legacy export directory is configured |
| Development instrumentation assembly | Passed |
| `python scripts/emulator_verify.py --variant development --output docs/compact-result-emulator.json` | 25 passed, zero failed/skipped in final run on API 36 emulator |
| Full-suite breakdown | Flow/lifecycle/decoding/initialization/development/compact/assessability 18; notification denial 1; offline parity/invalid models 3; modem SMS 1; notification/channel safeguards 1; large-font accessibility 1 |
| CompactResultTest at font scale 2.0 | 4 passed; setting restored afterward |
| Shipped-model synthetic screenshot test | 1 passed, test-owned view rendered with FLAG_SECURE preserved |
| Ordinary launch of named deliverable, outside instrumentation | Passed: short synthetic greeting produced 28.2% and No phishing detected, message cleared, no process fatal exceptions; installed APK bytes equal deliverable |
| APK | ZIP CRC, v2 signature, package/version, original model hash/metadata and test/dataset exclusions passed; no INTERNET permission |
| Policies | Strict >0.5 threshold and model bytes unchanged; automatic warnings and reporting disabled |

The initial 18-test flow group had one failed expectation: the test assumed a common
short English reply existed in the private vocabulary, but it had zero features.
Corrected the fixture expectation to honest abstention and explicitly covered both
that reply and an unknown short Tagalog reply. The short known greeting remains
assessable. Full suite then passed. Initial failure evidence remains local under
ignored deliverables; this is not a model adjustment or evaluation-set tuning.

The original fifteen-probe supplied-model math/feature parity still runs at 1e-10,
including unknown/blank cases through the internal raw scoring path. Separate new
tests exercise the production abstention path and score equality for accepted inputs.
UI tests cover both decision wordings, percentage formatting, blank/unknown results,
missing/invalid model handling, stale-result clearing, headings/live regions, 48 dp
help control, scrollable explanation and disabled reporting. Test fixtures are invented
software probes and are not labeled research data or evidence of classifier accuracy.

The screenshot shows an actual 90.1% score from the unchanged model on a synthetic
phishing-shaped input. The message box is empty because the existing privacy policy
clears text after a check. No private message or vocabulary appears in the screenshot.
Layout was visually inspected at normal scale; 2x font behavior was exercised separately.

## Private development APK

`deliverables/SmishGuard-0.2.0-dev-compact-results-20260925-e9447250767e.apk`

SHA-256: `e9447250767e0c82b249514d4e303cc8ba7be84bb1c047b9e38e74552087de9f`

Package `ph.smishguard.dev`, version `0.2.0-dev`, version code 2.
Model SHA-256: `9026c925679f9667b5bd09e34f31dd884cdb72607650d97f9a0708c86fa6bab2`.

Install/update this APK and choose Open from Android's installer. This launches the
development package instead of the older model-free `ph.smishguard` app. Use the
Check tab for Test a message. Share only through the authorized private team channel.
The APK/model remain ignored and are not part of the source commit.

Evidence: `compact-result-apk.json`, `compact-result-emulator.json`,
`compact-result-accessibility.json`, `compact-result-production-smoke.json`,
`compact-result-score-diagnosis.json`, `compact-result-training-readiness.json`.
Retraining investigation and remaining gates: `compact-result-retraining.md`.

Only an API 36 emulator was tested; phone behavior and API 26 reruns are unverified
in this change. No retraining or candidate adoption occurred. The design-tool installer
failed with spawn EINVAL on this host; the native Compose implementation followed the
user's supplied reference and was checked against its field/button/card arrangement.
