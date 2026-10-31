# VeriTxt — old Ham/Smishing model restored

Install `C:\Users\Jassim Trinidad\OneDrive\Desktop\smishguard\deliverables\old-binary-svm-20261020\VeriTxt-OldModel-Ham-Smishing-debug.apk` and open **VeriTxt · Ham/Smishing**. This is a signed debug APK, package `ph.smishguard.svm.oldbinary`, built with the existing local debug key. It installs alongside earlier variants. No physical-phone test is claimed.

The model asset is byte-identical to `assets/model.json` inside the user's `Veritxt-0.3.0-Updated.zip` APK: SHA-256 `15cc0105b0e51e5342682ea36896c4436e515c39d165faf040476046b6b8059c`. It has 18,473 features, classes Ham/Smishing, and the unchanged validation-selected threshold 0.36999999999999994. Training percentage is not established by the old APK metadata. No retraining, parameter, feature, sigmoid or decision-threshold changes were made. The existing case-preserving raw-SMS adapter is retained unchanged (SHA-256 `11c3ee93fb7523e72b5658bec9f4bc5ee7389d9e5add25d5ca3fceceeedb5b8c`).

The new `oldSvm` build uses the existing SelectedSvmDetector/scorer. It adds explicit Ham or Smishing display labels based directly on the binary decision; no Gambling class or invented model output is presented. The mathematical scorer is unchanged. Previous variants keep their existing behavior.

Following the user's latest direction, this build uses the base `evidence-index-v1` risk profile with the cashback override disabled. No bank-name rule or message-specific condition was added. Model category and the existing heuristic risk index remain separate; a risk score is not a calibrated fraud probability. This is a restoration of the old model, not evidence of improved accuracy or a promise that every scam is detected. No accuracy was inferred from parity tests.

Verification: 515 frozen Python/JVM/Android model fixtures and 33 raw-SMS preparation fixtures passed. Android maximum score errors: 4.44e-16 (model) and 1.11e-16 (raw). Production app-path, binary category mapping, unchanged base risk routing, both category screens, manual/shared/pasted flows, privacy clearing, risk screens, themes and actual emulator incoming-SMS warning checks passed. Total Android tests: 20 on API 36. Unit tests: 46 passed, 11 conditional skips, zero failures/errors. Lint: zero errors, 11 warnings. Normal non-test app launch succeeded.

Earlier artifacts/models/reports: 510 original files passed SHA-256 preservation checks. The packaged application contains only the original binary model and its raw-SMS adapter; no parity fixtures, datasets or pickle files were included. APK SHA-256: `9994b695389c5ef65ba35729278ee9e4a2a272042a4e3447e16a36a47f0f30fb`.

Reproduce with `scripts/build_old_binary_svm.ps1`, then `scripts/verify_old_binary_svm.py --output <fresh-output>` and `scripts/package_old_binary_svm.py --verification <fresh-output> --destination <fresh-deliverable>`. The parity files are copied into the new run directory so historical evidence is not overwritten.
