# Minimalist Compose redesign - 26 September 2026

This visual direction supersedes the earlier neo-brutalist redesign. The native Compose app now uses warm-white and neutral dark surfaces, near-black actions, subtle dividers, restrained gray selection, and consistent 24 dp spacing. Information sections are unboxed. Outlined secondary actions use a 1 dp border; primary actions retain visible keyboard focus and standard pressed feedback. Touch targets remain at least 48 dp.

## Screens and behavior

- Onboarding and Home retain the processing, consent and experimental-use disclosures with a simpler typographic hierarchy.
- Test a message has a prominent multi-line input and one Check message action. Paste, share, clear and input limits are unchanged.
- Results have their own concise presentation within the existing checking route, with the classification as the main heading, Model score for valid outputs, and an accessible experimental-status note. Check another message clears the result and returns to an empty input. Details and reporting options remain accessible.
- Missing or invalid models display Model unavailable without a percentage; Unable to assess and failure behavior remain intact. Only display wording changed, not the numerical score or decision policy.
- Settings, SMS consent, notification permissions, city selection, local reset, explanation and disabled reporting flows remain available. There is still no scan History screen or retained message history.
- Dark mode, system navigation insets and keyboard insets are retained. Content scrolls for smaller screens and larger fonts.

Retraining, calibration, threshold changes and model replacement are postponed. Detector, assessability, reporting, automatic-warning policy and privacy lifecycle implementations were not changed. No networking was added. Private training data, private model ZIPs and the pre-existing untracked output directory were not accessed or staged.

## Reproduction and evidence

Use scripts/build.ps1 with Variant debug or development and ConnectedTests for the ordinary emulator suite. The development variant still verifies the existing shipped model digest before packaging. Debug deliberately has no bundled model; development contains the unchanged shipped asset and is debug-signed. Generated APKs, screenshots and verification metadata are under the ignored deliverables/minimalist-20260926 directory.

VisualReviewTest captures all main screens, six result states, permission consent, the explanation and disabled reporting, using invented input only. Result fixtures are UI coverage, not research measurements. Existing model and privacy assertions remain; presentation assertions now reflect the new copy and return-to-input action.

The required 12ui installer was attempted but failed on this Windows host with spawn EINVAL. The supplied references were applied directly to Compose; no reference branding, imagery or decorative patterns were copied.

## Verification results

- Debug and development APK assembly, Android lint and unit tests passed. Each unit suite reports 10 passes and one explicit private parity-data skip.
- Development API 36 connected suite: 21 passed, five specialized tests skipped, no failures/errors. The skips require separate modem/notification orchestration or private parity fixtures.
- Six post-refinement UI tests passed: screenshot states, compact-result checks and accessibility. A separate 320 dp-wide/200% font accessibility run passed, including the result heading, no fabricated percentage, and reachable return-to-input action. Display settings were restored afterward.
- Light and dark screenshot checks passed. Visual review removed the remaining default secondary-control tint and corrected dialog captures to target their own windows.
- Both APK signatures verify and both manifests omit Android INTERNET permission. Debug has no model asset. Development retains the shipped model SHA-256 enforced by the existing build guard. APKs and audit metadata remain local.

The first unit run caught an expected-copy typo at 100% in a changed test assertion; it was corrected without changing score calculations. No physical-device validation or new research evaluation was performed. Specialized skipped checks remain outstanding rather than being counted as passes.

Final plain-debug API 36 connected suite: 16 passed, 10 explicit skips, zero failures/errors. Additional skips are development-model-only checks because debug deliberately ships without a model.
