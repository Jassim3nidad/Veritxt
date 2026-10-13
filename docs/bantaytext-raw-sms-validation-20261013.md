# Raw-SMS preprocessing validation — 13 October 2026

**Raw-input engineering check passed.** The user-reported physical-phone checks are recorded as completed. The supplied dataset is used with inherited-label limitations; another human-labeled upload is not a blanket prerequisite imposed by this task.

The candidate still has a measured source-transfer concern: on the stricter Tagalog-source holdout it produced 133 false positives and F1 0.3896. Successful phone/compatibility checks establish that software runs correctly; they do not erase that predictive result. Active model parameters and behavior remain unchanged.

## Exact training-view replay

Reconstructed the original case-preserving source inputs for all **2554 cleaned records** using pinned source-member hashes and the existing private source-row joins. `clean(mask(clean(raw)))` reproduced every trained/evaluated text exactly. Python scores have maximum absolute difference **0** from the frozen fitting views. No vectorizer, coefficients, IDF, calibrator or threshold was refitted.

| Source | Replayed records |
|---|---:|
| tagalog | 1424 |
| marketing | 1002 |
| bwandowando | 128 |

Cleaning removes the documented dataset placeholders, collapses frozen Python Unicode-15 whitespace and strips edge spaces/commas. Masking applies ASCII-case-insensitive http(s)/www URLs, ASCII email patterns and ASCII digit runs in that order, then cleans again. Lowercasing remains in the frozen tokenizer, preserving the original case-sensitive source view until feature extraction. No URL is opened. Bare domains/obfuscated URLs keep the original preparation behavior; this is not a new URL detector or complete privacy certification.

## Python/JVM/Android parity

All **33 fictional raw-SMS probes** passed exact normalized-text, token, feature-index/value, score and threshold parity on JVM and an offline API36 emulator. Maximum score difference: JVM 1.11e-16, Android 1.11e-16. Eight required empty/placeholder-only/random/keyboard/numeric/URL-only/malformed cases abstained; raw overlength input failed before masking could reduce its length.

Probes cover legitimate-style bank/e-wallet/OTP text, Taglish, HTTPS and www links, email/OTP masking order, source placeholders, Unicode whitespace, Arabic versus ASCII digits, underscores, Turkish/Greek/supplementary Unicode, unknown-token adjacency, bare and obfuscated links. These are compatibility fixtures, not independent accuracy labels. Original raw SMS stays in authorized private source storage and was not exported into the Android probes or public report.

The first Android raw-input run caught an ICU case-folding difference: a Unicode long-s in a URL prefix was incorrectly treated as ASCII s. Explicit ASCII character pairs and ASCII whitespace exclusions replaced reliance on Android regex flags. The corrected adapter passes the original probe and added Unicode URL-boundary probes; the failed attempt is preserved privately under raw-sms-v1. Learned parameters did not change.

The native raw adapter and selected scorer remain in test sources. Production APK checks confirm they are absent, the selected schema remains rejected by the production loader, and the active asset is byte-identical. This provides a reviewed preprocessing specification for eventual integration without silently switching the application model.

Checks passed: 121 research tests; JVM 32 passed, 4 conditional skips, zero failures; Android development app/test APK assembly and lint. The offline instrumentation run passed selected-SVM/raw-SMS/active-model checks with airplane mode on, Wi-Fi off and INTERNET denied. All 11 protected model/app hashes are unchanged.

## Phone-check and labeling clarification

Physical-phone checks: **completed as directly reported by the user**. Exact tested APK/model and measurement details were not specified in this chat, so no device timings or new-SVM physical results are invented. Older blank/pending forms describe historical records and are not grounds to ask for completion again. Agent-executed checks in this report are JVM/emulator checks.

Labels: source/rule labels were already supplied and used. Independent human review is unavailable; its limitation remains explicit, as allowed by the original task. No reviewer identity, adjudication or ground-truth verification is fabricated. The October 12 ZIP is historically used, so it cannot support a claim of genuinely unseen traffic performance merely by reshuffling it.

Broad deployment recommendation remains limited by the observed false positives/source-transfer result. Further independently verified or unseen data would strengthen the predictive evidence, but it is not an invented permission gate for continuing local engineering or research demonstrations.

## Reproduction

```powershell
$env:PYTHONPATH='research'
$env:PYTHONIOENCODING='utf-8'
research/.venv/Scripts/python.exe -m smishguard.raw_sms_validation research/runs/bantaytext-20261013/notebook-run-v3 research/runs/bantaytext-20261013/validation-v2 research/runs/bantaytext-20261013/NEW-RAW-RUN
$parityPath=(Resolve-Path research/runs/bantaytext-20261013/NEW-RAW-RUN/parity).Path
$env:JAVA_TOOL_OPTIONS='-Djdk.net.unixdomain.tmpdir=C:/sg-nonexistent-socket-dir'
.\gradlew.bat :app:testDevelopmentUnitTest :app:assembleDevelopment :app:assembleDevelopmentAndroidTest :app:lintDevelopment "-PmodelParityDir=$parityPath" -PinstrumentedBuild=development --console=plain
# Use a verified designated test emulator:
research/.venv/Scripts/python.exe scripts/verify_selected_svm_emulator.py --adb '<SDK adb path>' --raw-sms --output research/runs/bantaytext-20261013/NEW-RAW-RUN/emulator-results.json
research/.venv/Scripts/python.exe scripts/report_raw_sms_validation.py research/runs/bantaytext-20261013/NEW-RAW-RUN
```

Files: `research/smishguard/raw_sms_validation.py`, `research/tests/test_raw_sms_validation.py`, test-only `RawSmsParity.kt`/`RawSmsParityTest.kt`, extended `SelectedSvmAndroidTest.kt`, emulator/report scripts and updated phone/model documentation. Successful private output: `research/runs/bantaytext-20261013/raw-sms-v2/`. No dataset, learned model parameter, raw message, commit, push or deployment was published.
