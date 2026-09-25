# Model-not-installed investigation — 25 September 2026

## Diagnosis before changes

The initial working tree was clean on `codex/thesis-completion-package`, at
`c3cfc3b`. Recent work reviewed candidate evidence and fixed initialization/test
synchronization; it did not adopt the candidate. Fetching origin showed no divergence.

The screenshot does not identify an APK. No exact installed file was supplied, so
the user's screenshot/phone APK cannot be proven. File paths, package/version
metadata, inferred variants and full hashes of likely deliverables are recorded in
[existing APK evidence](model-install-existing-apks.json).

The connected API 36 emulator contained package `ph.smishguard`, version 0.1.0,
code 1, with no `assets/model.json`. Its pulled APK hash was
`86c92f1fe6105bcea5dfe804fef6859f1010d9dc9946989f31ba67ca51c11a1d`.
This establishes an older model-free debug installation on the emulator, not the
identity of the screenshot APK. The old deliverable `deliverables/SmishGuard-0.1.0-debug.apk`
also lacks that asset, with hash
`586536d9f63fe4c6609112bc282495fd267c7ae33a0ba776ac5c011e161664f3`.
These are different APK bytes despite the same package/version.

`SmishGuardApp` opens `model.json` from Android assets. FileNotFoundException
creates `MissingDetector()`, whose detection returns `Unavailable`; `MainActivity`
maps that specifically to “Model not installed.” Other loading/validation exceptions
return `InvalidModel`, displayed separately. Thus this screen indicates a missing
asset, not a schema-validation failure in the current code. The inspected development
deliverables all contain the expected asset with SHA-256
`9026c925679f9667b5bd09e34f31dd884cdb72607650d97f9a0708c86fa6bab2`.
No packaging defect was found in those APKs. A wrong/older variant is supported by
the emulator evidence; the user's installed APK remains unidentified.

## Fix

The development Gradle build previously succeeded when the ignored private model
was absent. A required, always-executed guard now checks presence and the exact
existing experimental-model digest before development prebuild/asset merging.
Missing or substituted assets fail with an actionable error. Debug remains model-free.
The isolated regression script exercises the real assembly/merge task dependencies
without moving, replacing or reading the working private model.

If missing on another checkout, place the team's existing converted 0.2.0-dev
asset at `android/app/src/development/assets/model.json`, matching the digest above.
Do not use the calibrated candidate. Neither PRIVATE ZIP was opened or used.
No model parameters, runtime inference, reporting or warning policy changed.

## Verification actually run

- `python scripts/test_development_model_guard.py`: 3 checks passed: missing asset
  blocks development assembly, wrong asset blocks merging, model-free debug prebuild works.
- `scripts/build.ps1 -Variant development`: assembly, lint and unit-test task succeeded.
  Assembly and JVM tests were subsequently rerun with `--rerun-tasks`: 6 JVM tests
  passed; 1 legacy schema-1 ExportParityTest skipped because its separate export
  directory is absent. This skip is not a parity pass.
- Development instrumentation APK assembled; existing `scripts/emulator_verify.py
  --variant development` passed 19 API 36 tests, including UI/lifecycle, model initialization,
  offline supplied-model parity at 1e-10, malformed model rejection, disabled reporting,
  SMS/notification safeguards and large-font accessibility. Original historical results
  were preserved; this run is in [emulator results](model-install-emulator-results.json).
- Separate ordinary app launch, outside instrumentation: installed the named deliverable,
  scanned a synthetic input, saw an experimental score/result, verified input cleared
  and disabled-policy text. Pulled installed bytes matched the deliverable hash.
  Process-filtered AndroidRuntime logs contained no fatal exception; no raw logs or
  scan text are published. [Smoke evidence](model-install-production-smoke.json).
- ZIP CRC, APK Signature Scheme v2, package/version, exact packaged/local model
  equality and safe metadata verified. No INTERNET permission, dataset, parity fixture
  or test runner/application in the delivered APK. [APK evidence](model-install-apk-verification.json).

Only an emulator was connected. No physical-phone installation or scan was tested.
No research accuracy claim follows from these software checks.

## Private team deliverable and installation

`deliverables/SmishGuard-0.2.0-dev-model-included-20260925-ce4c9752edb1.apk`

SHA-256: `ce4c9752edb161f7293e38a7f1ebd9f775089e845550fba868bfbfac7843411f`

Package `ph.smishguard.dev`, version `0.2.0-dev`, code 2, development variant.
The fresh build is byte-identical to the existing current build output: the safeguard
changes build validation, not packaged runtime code or model bytes. The distinct
filename separates it from older deliverables; old files were preserved.

Send only this APK to authorized groupmates through the private team channel.
Open it on Android and install/update it, then choose Open from the installer to
avoid launching the older `ph.smishguard` app. Confirm the home screen says
“Experimental model · unverified performance” before checking a synthetic message.
If Android requests permission for that file source, temporarily allow installation
from that source. Development and old debug packages can coexist. For an emulator
or explicitly selected test device, `adb -s <target> install -r <apk-path>` installs it;
launch `ph.smishguard.dev/ph.smishguard.MainActivity` explicitly.

APK, model and local audit copies remain ignored; only source/tests and sanitized
records are intended for this branch. No main merge or force push is authorized.
