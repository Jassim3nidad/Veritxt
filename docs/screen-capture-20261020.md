# Showcase screen capture — 20 October 2026

The user requested screenshots, screen recording and screen sharing for showcasing both APKs. `MainActivity` previously set Android's `FLAG_SECURE`, which causes capture/sharing tools to block or black out the app. That call and its unused import have been removed from the shared Activity. Compose dialogs inherit the unrestricted window policy. No permission, settings toggle or test-only override is required to capture the app.

Both `selectedSvm` and `nbGeneralization` are rebuilt with their saved Light/Dark/Follow system controls. Model assets remain byte-identical to the earlier APKs; no retraining or score/threshold change is part of this update. Application IDs and the local Android debug signing identity are retained, so these APKs update the corresponding installed versions.

The existing message-clearing behavior still applies when leaving or backgrounding the app. The app remains excluded from recents and does not store scan history. Screen capture tools can now capture what the user displays. The [privacy documentation](privacy.md) and [current system architecture](VERITXT-SYSTEM-ARCHITECTURE.md) describe the changed capture policy; older dated audits record the policy in their original builds.

## Verification

`ScreenCaptureTest` uses Android's `UiAutomation.takeScreenshot()` to capture the actual composed display. It does not clear any window flags and does not draw the app view into a bitmap. It checks visible content on the privacy page, home, message entry, actual-model result and explanation dialog. The host verifier records the result screen with Android's `screenrecord`, checks the transfer hash, and decodes frames with Android's media retriever to verify that the recording contains visible app content.

`PrivacyLifecycleTest` now checks that capture is allowed while retaining assertions that the message clears after navigation, backgrounding and recreation. Old visual-only test helpers no longer toggle or restore `FLAG_SECURE`, so later tests cannot accidentally re-enable the removed restriction.

Private build/test logs: `research/runs/screen-capture-20261020/`. Delivery, native PNGs, fictional-message MP4 recordings, checksums and verification records: `deliverables/Veritxt-Showcase-20261020/`. No physical phone or third-party screen-sharing service is used for the emulator verification; the app-side secure-window blocker is removed.

## Completed results

- Both app/test APK assemblies passed; Android lint reported zero errors.
- JVM checks passed: SVM 43 executed / 6 conditional skips; NB 39 executed / 10 conditional skips; zero failures. Each variant's private model parity fixtures were supplied.
- Ten final API 36 emulator tests passed (five per APK): both lifecycle-clearing tests, OS screenshots, video-frame decoding and theme switching/recreation.
- Ten actual OS screenshots passed visible-content checks. Both recordings were decoded at two timestamps and contained visible app content: SVM 6,944 ms, NB 6,207 ms. Native PNGs and MP4 frames were visually inspected.
- APK v2 signatures verified using the existing local debug certificate. The delivered copies match the tested APK hashes; asset inventories contain only the original frozen model assets.

| Delivered APK | SHA-256 |
|---|---|
| `Veritxt-LinearSVM-60-20-20-Showcase-20261020.apk` | `60f2dfd2a545fc12fba99a5eb74c4caa4d7b98f05999514313c04ddabe8c7bbf` |
| `Veritxt-Retrained-NB-80-20-Showcase-20261020.apk` | `e1656a6e246e97b6d7c48ac66a914bbefbd199bfacdf2b0c9fe91e196ec48b06` |

The first capture check was adjusted to wait for a presented compositor frame rather than only Compose semantics. The recording verifier was corrected to keep MP4 bytes on-device during transfer and scroll the actual UI while recording, since a static screen can yield a one-frame/sub-second MP4 despite a longer recording command. These were test-harness corrections; no model or app behavior was changed to satisfy them. Earlier logs remain in the private run directory.
