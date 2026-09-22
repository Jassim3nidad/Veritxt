# Lint review — 21 September 2026

Development lint completes with **0 errors and 5 warnings**, down from the previous milestone's 10. No warnings were suppressed.

| Previous warning | Action |
|---|---|
| `UseKtx` URI parsing | Use AndroidX `toUri()` for the settings intent. |
| Activity dependency | Updated 1.12.2 to 1.13.0. |
| DataStore dependency | Updated 1.2.0 to 1.2.1. |
| Coroutines dependency | Updated 1.10.2 to 1.11.0. |
| JVM-test JSON dependency | Updated 20250517 to 20260814. |
| OldTargetApi | Retain target/compile 36 for this verified build; SDK 37 migration needs a separate build/toolchain and behavior check. |
| Compose BOM, main and androidTest (2) | Retain 2025.12.01; a newer bundle requires SDK 37 / AGP 9.1+. |
| Lifecycle viewmodel/runtime Compose (2) | Retain 2.10.0; inspected 2.11.0 AAR metadata requires compile SDK 37 and AGP 9.1. |

The inspected Activity 1.13.0 AAR requires compile SDK 36 / AGP 8.9.1, compatible with this project's SDK 36 / AGP 8.13.2. DataStore 1.2.1 requires SDK 34 / AGP 8.1.1. Build, unit tests and lint verify the selected dependency combination; this is not a claim that every dependency is the newest.

The SMS switch now has explicit 48 dp minimum bounds after its semantic height test exposed a 32 dp target. Focused accessibility instrumentation checks semantic headings, labeled switches, 48 dp input/switch targets, reachable controls and 2.0 font scale. See the verification checklist for actual API results. Automated semantics are not a TalkBack usability audit. TalkBack navigation, switch access, every screen/orientation/font/device configuration and API 37 remain untested.
