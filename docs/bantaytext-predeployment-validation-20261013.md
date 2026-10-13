# Further SmishGuard predeployment validation — 13 October 2026

Latest clarification: the original task permits inherited source/rule labels when
manual review is unavailable, provided that limitation is explicit. Earlier wording
below requiring another independently human-labeled cohort as a blanket software
release gate was too strong. Historically exposed data still cannot prove prospective
performance, and the measured source-transfer weakness remains material. The user
reports physical-phone checks completed. Subsequent [raw-SMS validation](bantaytext-raw-sms-validation-20261013.md)
addresses the previously open preprocessing check; the older test results below are
preserved as historical evidence.

**Release decision: keep the active model.** Further engineering checks passed, but predictive deployment validation remains incomplete. The user-supplied ZIP is byte-identical to the previously used October 12 package; there are zero completed independent labels and zero new prospective intake records. Source transfer still fails on the Tagalog corpus.

## Data identity and independent evidence

ZIP SHA-256: `38d00a999306ff11b05a431d9488f167589bd94e701f410edb24e8202bf3b3e6`. All 8 original archive members match preserved intake hashes. The 3,340-record retrospective review has 0 finalized decisions; the package workbook also has no completed final labels. Do not treat source/rule labels as independent truth or rename previously used data as unseen validation.

The [protocol](bantaytext-predeployment-protocol-20261013.md) was saved before additional predictions. The selected original SVM, its threshold ≥0.37, coefficients, vocabulary, calibration and previous split remain unchanged. No test result was used to tune that candidate. All populated artifacts stay private under `research/runs/bantaytext-20261013/validation-v2/`.

## Fixed-candidate uncertainty

Two thousand paired whole-template bootstrap draws use the fixed grouped-test candidate and standard SVM baseline on the same 498 records. These intervals do not include fitting, model selection, inherited-label uncertainty or source bias.

| Metric | 95% descriptive interval |
|---|---|
| precision | 0.8493–0.9894 |
| recall | 0.8750–1.0000 |
| f1 | 0.8750–0.9846 |
| false_positive_rate | 0.0022–0.0203 |
| false_negative_rate | 0.0000–0.1250 |
| paired_f1_delta_vs_baseline | 0.0077–0.1763 |

The grouped-test F1 remains 0.9524. The conditional interval is broad; observed gains over a standard baseline do not prove prospective deployment superiority.

## Stricter source-held-out operating points

Each outer source and every overlapping template group are excluded before fitting. Only its source complement supplies a 5-fold grouped inner train/validation split; SVM calibration uses 3-fold grouped OOF training margins. Thresholds are chosen using inner validation only and frozen before outer prediction. Algorithm settings remain historical fixed values (NB alpha=.1, LR/SVM C=10); prior corpus exposure/setting selection prevents an unbiased prospective claim.

| Held source | Algorithm | Threshold | Precision | Recall | F1 | TN/FP/FN/TP |
|---|---|---:|---:|---:|---:|---|
| bwandowando | nb | 0.10 | 1.0000 | 0.6875 | 0.8148 | 0/0/40/88 |
| bwandowando | lr | 0.18 | 1.0000 | 0.6250 | 0.7692 | 0/0/48/80 |
| bwandowando | svm | 0.77 | 1.0000 | 0.6719 | 0.8037 | 0/0/42/86 |
| marketing | nb | 0.27 | 0.9900 | 0.6875 | 0.8115 | 857/1/45/99 |
| marketing | lr | 0.19 | 0.9590 | 0.8125 | 0.8797 | 853/5/27/117 |
| marketing | svm | 0.57 | 0.9552 | 0.8889 | 0.9209 | 852/6/16/128 |
| tagalog | nb | 0.32 | 0.2745 | 0.7925 | 0.4078 | 1260/111/11/42 |
| tagalog | lr | 0.18 | 0.1886 | 0.8113 | 0.3060 | 1186/185/10/43 |
| tagalog | svm | 0.47 | 0.2528 | 0.8491 | 0.3896 | 1238/133/8/45 |

The selected algorithm family has Tagalog-held-out F1 **0.3896**, despite recalibrating its operating point entirely outside that source. This confirms a material source-generalization concern. BwandoWando has only positive labels, so FPR/ROC/AP there are not estimable. Source-specific confusion counts and partition supports are in [JSON](bantaytext-predeployment-validation-20261013.json).

## Targeted errors and calibration

| Original source category | Ham support | FP | Observed FPR | Wilson 95% interval |
|---|---:|---:|---:|---|
| otp | 55 | 0 | 0.0000 | 0.0000–0.0653 |
| gov | 21 | 0 | 0.0000 | 0.0000–0.1546 |
| ads | 176 | 3 | 0.0170 | 0.0058–0.0489 |
| notifs | 173 | 1 | 0.0058 | 0.0010–0.0320 |

Zero OTP errors in 55 records does not establish zero population FPR: its Wilson upper bound is about 6.53%. Wilson bounds do not cover grouping/selection/label uncertainty. No independently validated bank/e-wallet category is available. Broad notifications are not a bank-specific safety test.

Grouped-test ECE is 0.02183, Brier 0.01567 and log loss 0.06074 under inherited retrospective labels. The score transform was fitted; numerical calibration quality on real incoming financial SMS remains unverified. The native test scorer never marks its score as a validated probability.

## Frozen-input robustness

| Transformation | Changed decisions /498 | Max absolute score change |
|---|---:|---:|
| uppercase | 0 | 0.00000 |
| whitespace | 0 | 0.00000 |
| punctuation | 0 | 0.00000 |
| remove_url_marker | 2 | 0.33593 |
| add_taglish | 5 | 0.16107 |
| bank_obfuscation | 0 | 0.07139 |

All scores stayed finite. Casing, whitespace and inter-token punctuation happened to preserve this cohort’s features. Inserting Taglish wording or removing link markers can alter content/features; changed decisions are stress diagnostics, not newly adjudicated errors. The current model cannot be fixed using these exposed test observations and then evaluated on that same test as an independent improvement.

## Actual SVM native compatibility and offline emulator

The selected SVM was exported into a test-only Unicode-15/English-stopword/bigram scorer. It preserves minimum two-codepoint tokens, removes stopwords before bigrams, retains unknown-token adjacency, ordered feature indices, IDF/raw counts/L2, coefficients, exactly one sigmoid and class/threshold mapping. These checks now apply to the actual selected SVM, rather than only the earlier portable LR comparator.

Python/JVM and API36 offline emulator parity passed on **515 cases: 498 actual private masked test views plus 17 synthetic probes**. Maximum score difference is 4.44e-16; maximum feature difference is 1.11e-16. Seven required empty/random/keyboard/placeholder/malformed inputs abstained; overlong input failed. Metadata, invalid numeric, class orientation and approval-field tampering were rejected.

The contract expects already masked training views. A reviewed raw-SMS masking/integration contract remains necessary before release. The scorer lives only in test sources and is absent from the production APK. The production loader explicitly rejects its schema; no active inference path was switched. The development APK still contains byte-identical active weights and no selected-SVM model or private case asset. Test artifacts/APKs remain private.

Emulator-only measurements: JSON model 1,333,723 bytes / 18,473 features; load 449.9 ms; mean score-path time 0.324 ms/message. The score timing includes tokenization/features/dot product/sigmoid, excludes model load, JSON probe parsing and input-abstention checks. Whole instrumentation-process PSS went from 162,103 to 181,745 KiB; this includes test data/runtime and is not isolated model memory or phone benchmarking.

Four offline Android instrumentation checks passed, covering the selected SVM, unchanged active model and synthetic sklearn exports. Airplane mode was enabled, Wi-Fi disabled and INTERNET permission denied. Original connectivity settings were restored. The emulator is verified using ro.kernel.qemu=1; no physical device was used.

The existing complete development emulator suite also passed: UI/lifecycle/SMS decoding, denied/granted/blocked notification behavior, offline supplied exports, synthetic modem SMS, large-text accessibility and private-storage scanning. Receiver tests used fictional markers only; selected-model inference used already masked private test views directly inside the isolated test APK. No real SMS was sent through the receiver.

Verification: 117 research tests passed; JVM 31 passed/4 conditional skips/0 failures; Android assemble, test-APK assemble and lint passed. All 11 protected app/model hashes remain unchanged. Initial harness attempts failed on Windows manifest path separators and absent shared comparator fixtures. The broader emulator run also exposed a stale UI-test assertion that warnings were disabled, contrary to the prior team-enabled original-model policy; CompactResultTest now checks the actual build policy. These corrections affect validation tooling/tests only. No production behavior changed. Failed attempts/logs remain private; no partial fit was selected.

## Required next evidence

Supply a genuinely new, authorized cohort collected after a documented candidate freeze. Complete human privacy/source-use checks, blinded independent A/B labels and adjudication before predictions; reject historical exact/near-template overlap and freeze membership. The previous 3,340-row blinded packets can improve retrospective label quality but cannot turn those messages into prospective evidence. A new candidate-specific freeze is saved privately as `prospective-candidate-freeze.json`; the old four-model freeze is preserved.

Confirm calibration/threshold quality and legitimate financial-message subgroup support on that new cohort, review raw-SMS preprocessing parity, then perform physical-phone resource and behavior checks. Until those steps pass, keep the active model and experimental score wording. Nothing was deployed, committed, pushed or published.

## Changed files

Additional scripts: `research/smishguard/predeployment_validation.py`, `scripts/report_predeployment_validation.py`, `scripts/verify_selected_svm_emulator.py`; Python guards: `research/tests/test_predeployment_validation.py`. Test-only Kotlin scorer/parity: `android/app/src/softwareTest/java/ph/smishguard/SelectedSvmParity.kt`, JVM `SelectedSvmParityTest.kt` and instrumented `SelectedSvmAndroidTest.kt`. `CompactResultTest.kt` corrects the stale policy expectation. The protocol, this report/JSON, research README and candidate/contract documentation were updated. Existing notebook, fitted candidates, previous evaluation outputs, production sources and installed assets were preserved.

## Reproduction

```powershell
$env:PYTHONPATH='research'
$env:PYTHONIOENCODING='utf-8'
research/.venv/Scripts/python.exe -m smishguard.predeployment_validation research/runs/bantaytext-20261013/notebook-run-v3 '<authorized October 12 ZIP path>' research/runs/bantaytext-20261013/NEW-VALIDATION-RUN
$parityPath=(Resolve-Path research/runs/bantaytext-20261013/NEW-VALIDATION-RUN/parity).Path
$env:JAVA_TOOL_OPTIONS='-Djdk.net.unixdomain.tmpdir=C:/sg-nonexistent-socket-dir'
.\gradlew.bat :app:testDevelopmentUnitTest :app:assembleDevelopment :app:assembleDevelopmentAndroidTest :app:lintDevelopment "-PmodelParityDir=$parityPath" -PinstrumentedBuild=development --console=plain
# Start a designated API36 test emulator; no physical-device use.
research/.venv/Scripts/python.exe scripts/verify_selected_svm_emulator.py --adb '<SDK platform-tools adb path>' --output research/runs/bantaytext-20261013/NEW-VALIDATION-RUN/emulator-results.json
# Optional complete development regression suite, with SDK adb on PATH:
research/.venv/Scripts/python.exe scripts/emulator_verify.py --variant development --output research/runs/bantaytext-20261013/NEW-VALIDATION-RUN/privacy-emulator-results.json
research/.venv/Scripts/python.exe -m unittest discover -s research/tests -q
research/.venv/Scripts/python.exe scripts/report_predeployment_validation.py research/runs/bantaytext-20261013/NEW-VALIDATION-RUN
```
