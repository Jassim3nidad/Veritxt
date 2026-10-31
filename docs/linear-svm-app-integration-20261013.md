# Linear SVM app integration — 13 October 2026

The user requested the groupmates' latest UI/features, trained Linear SVM integration, feature checks, an APK and UI screenshots. GitHub `main` and local `main` were both `0242b489bd551f067ee571012576e88fde9c8e3a`; `git pull --ff-only` confirmed the checkout was current. A NUL-filled Codex checkpoint reference was copied to private output before removal to restore Git fetching. No branch or source work was lost.

The separate `selectedSvm` build (`ph.smishguard.svm.selected`, Android 8+) packages the frozen notebook-selected `svm-C-10.0` candidate. It uses the already verified Unicode-15 tokenization, English stopwords, word unigrams/bigrams, TF-IDF/L2, fitted sigmoid and inclusive threshold ≥0.37. Raw input follows the exact clean/mask/clean training view; the original input length is checked before masking. Empty, unknown, numeric-only and URL-only inputs abstain. Model scores are experimental, not verified probabilities.

The scorer and raw adapter now live in app sources and are shared with the original parity tests. A dedicated loader requires both assets; the generic model loader still rejects schema 6 without the raw-input adapter. Build guards pin the exact exported model SHA-256 `15cc0105b0e51e5342682ea36896c4436e515c39d165faf040476046b6b8059c` and adapter SHA-256 `11c3ee93fb7523e72b5658bec9f4bc5ee7389d9e5add25d5ca3fceceeedb5b8c`. Learned parameters and original development weights were preserved. Private assets and APKs remain excluded from Git.

The team's incoming-SMS warning feature remains enabled for this experimental build, conditional on privacy acceptance, scanning consent and Android permissions. This app policy does not rewrite the model's research approval metadata. Reporting stays unavailable, as implemented in the groupmates' app. No remote reporting service was added.

Accuracy evidence remains limited by inherited labels, historical exposure and source transfer. Earlier Tagalog-source holdout F1 was 0.3896 with 133 false positives. Integration checks establish software compatibility; they do not establish future SMS accuracy. Previous user-reported phone checks are preserved as reported and are not attributed to this new APK.

Reproduction:

```powershell
$parity=(Resolve-Path research/runs/bantaytext-20261013/raw-sms-v2/parity).Path
scripts/build.ps1 -Variant selectedSvm -ModelParityDir $parity
$env:JAVA_TOOL_OPTIONS='-Djdk.net.unixdomain.tmpdir=C:/sg-nonexistent-socket-dir'
.\gradlew.bat :app:assembleSelectedSvmAndroidTest "-PmodelParityDir=$parity" -PinstrumentedBuild=selectedSvm --console=plain
research/.venv/Scripts/python.exe scripts/emulator_verify.py --variant selectedSvm --output output/svm-integration-20261013/emulator-results.json --demo-screenshots deliverables/Veritxt-LinearSVM-20261013/ui
```

Verification passed:

| Check | Result |
|---|---|
| App/test APK assembly and Android lint | Passed; no lint errors |
| JVM tests with private parity fixtures | 32 passed, 4 conditional skips, no failures/errors |
| Specialized API36 emulator suite | 29 passed |
| Additional recovery, privacy and bilingual UI tests | 9 passed |
| Final branded UI refresh on delivery APK | 2 passed; screenshots refreshed |
| Frozen SVM parity | 515 masked/synthetic cases; maximum JVM score error 4.44e-16 |
| Raw-SMS app path parity | 33 fictional probes; maximum JVM score error 1.11e-16 |
| Actual SVM modem SMS → private alert → result | Passed without a stub detector |
| Share/paste, session clearing, multipart reception | Passed |
| Denied/granted/blocked notifications, large text | Passed |
| Private app storage | 2 files inspected, zero raw-fixture markers |
| APK asset identity and content | Exact frozen model/adapter; no dataset or case assets |
| Android APK signature | Verified |

The original development-model hash remains `9026c925679f9667b5bd09e34f31dd884cdb72607650d97f9a0708c86fa6bab2`. No new physical-phone measurement was made. Prior user-reported phone results remain historical; these checks use the designated API36 emulator.

The first attempt caught an emulator notification shade holding clipboard focus; the verifier now collapses it before UI tests. The second attempt passed the functional checks but exposed a stale screenshot assertion for model-version text hidden by the groupmates' localized status label. The test now verifies the real detector identity separately, and the home screen displays a translated Linear SVM status. The final branding also omits the internal `selectedSvm` build name. Failed logs are preserved under private output; no model parameter was changed to satisfy a test.

Delivery: `deliverables/Veritxt-LinearSVM-20261013/Veritxt-0.3.0-LinearSVM.apk`, its `SHA256SUMS.txt`, and `ui/`. The APK is development-signed. `comparison-home.png` and `comparison-result-*.png` use the real bundled model with fictional inputs. `tour-*.png` demonstrates the complete UI; the tour's result examples use synthetic fixed verdicts and are not model evidence. Detailed logs/audits remain under `output/svm-integration-20261013/`.

Final delivery APK: 22,213,049 bytes, SHA-256 `59d5f7cf68bb2c99d7819b648d435d81c3c912123b4d293ce506edfcb200db2a`. The delivery copy matches the assembled APK byte-for-byte; signature, checksum and frozen asset checks passed after the final branding change.
