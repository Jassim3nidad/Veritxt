# Neo-brutalist Compose redesign - 25 September 2026

Implemented in the existing native Compose application. Retraining is postponed. No private training data or model ZIPs were accessed. The shipped development model, detector, score formatting, threshold, reporting policy, and automatic-warning policy are unchanged.

## Visual system

Cream canvas, violet selection/focus, lime primary actions, mint information surfaces, warm yellow unavailable states and coral phishing results. Cards and primary buttons use 2 dp dark outlines, 4 dp offset shadows and modest corner radii. Bold headings, consistent 16 dp section spacing, 20 dp page gutters, and at least 48 dp action targets preserve readability. Dark mode uses a dark canvas with readable light information cards. Keyboard, system navigation insets and vertically scrolling content are retained.

Home places the manual action before status details. Test a message retains one SMS field and one primary check action, followed immediately by the result. Result navigation keeps Check selected. All existing result copy and disclosure behavior remain. Settings and permission choices explicitly say automatic protection and reporting remain off. No History screen was added: message retention remains disabled. Onboarding, share, clear, reporting-unavailable, consent and Android settings flows remain available.

The supplied references informed the outlines, flat accent blocks, small shadows and bold hierarchy. Shopping content, branding, decorative clutter and compressed text were excluded. The required 12ui installer was attempted but failed on this Windows host with spawn EINVAL; implementation and visual review used the supplied references directly.

## Verification

See local deliverables/neo-brutalist-20260925 for the development APK, verification hashes and emulator screenshots. These generated/private artifacts are excluded from Git. Screenshot result values are explicit instrumentation fixtures, not research results. Screenshots contain no real messages. Screenshot protection is relaxed only inside the existing test instrumentation and restored afterward.

The development build guard verifies the unchanged shipped asset SHA-256. APK signature and packaged-model checks were performed; Android INTERNET permission is absent. The artifact is development-signed, not a production release.

Build and lint passed. JUnit XML reports 10 unit tests passed and 1 private-data parity test skipped; the API 36 connected suite reports 21 passed, 5 specialized tests skipped, and zero failures/errors. Specialized skips require modem/notification orchestration or private parity fixtures and were not represented as passing tests. Existing privacy, assessability, lifecycle, share/paste and model initialization tests remain intact.

After visual refinements, six targeted UI tests passed (compact results, accessibility and screenshot states). A separate accessibility run passed at 320 dp width and 200% font size; emulator dimensions, density and font settings were restored. Dark-mode screenshot coverage passed. Visual review corrected shadow geometry, a Settings text encoding artifact and screenshot transition synchronization. Screenshot capture now draws the settled test-owned view to avoid stale compositor frames.
