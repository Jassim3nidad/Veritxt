# mBERT packaging audit — 6 October 2026

The expanded APK shrank from **1,511,956,972 bytes to 800,410,184 bytes** (47.06% smaller). The removed **711,546,788 bytes** were an unreferenced gap left in the incremental ZIP layout. There was no duplicate active model file to delete. A clean packaging state removed the gap while preserving **all 160 referenced file contents byte-for-byte**, including model, tokenizer, metadata, Android bytecode, resources and native libraries. No fitting, quantization, threshold/calibration change or UI change occurred.

## What occupied the APK

| Component | Referenced stored bytes |
|---|---:|
| Four active assets | 712,169,045 |
| Native libraries across four Android ABIs | 75,280,448 |
| DEX bytecode | 12,257,646 |
| Other referenced files | 532,297 |
| Total referenced payload | 800,239,436 |

The asset bundle is 712,625,479 bytes before APK compression. Its main ONNX file is 711,555,338 bytes and remains stored uncompressed for the existing runtime. Native ABI support and app code account for most of the remaining legitimate payload. None was removed merely to reduce size.

In the original ZIP, a 711,546,788-byte gap began at offset 87,701,722, between active local-file records. Total unreferenced space was 711,550,884 bytes. After rebuilding, total unreferenced space was 4,096 bytes; the large gap disappeared. The remaining space and ZIP headers/directory/signing overhead are small. This identifies the excess as stale incremental packaging space, rather than a second active ONNX entry or bundled training dataset.

## Gradle and asset-source inspection

The `mbert` variant uses the normal shared sources plus `src/mbert`. The variant's asset guard admits exactly `LICENSE.txt`, `model.json`, `model.onnx` and `vocab.txt`; it rejects a shared main model. `androidResources.noCompress` retains ONNX uncompressed. mBERT alone adds ONNX Runtime Android 1.22.0. Private parity fixtures belong to `androidTest` through the explicit parity-directory property, not the application asset set. Inspection of the packaged archive confirmed only the four intended assets, with no private CSV, fitted training checkpoint or test-case file.

The old `outputs/apk/mbert` directory and `intermediates/incremental/packageMbert` state were moved to private, path-checked backup locations. Gradle then produced a fresh application package using the same inputs. The preserved original deliverable was never overwritten. `scripts/package_mbert.py` now rejects more than 1 MiB of unreferenced ZIP space to catch this recurrence before handing off another bloated APK.

## Verified outputs

| Property | Result |
|---|---|
| Model ID | `expanded-20261005-mbert-c3abc4bb` (unchanged) |
| ONNX SHA-256 | `a319976073b401ac1e90c2b229bed8facb5be8c9f6367cf2df6f0781d8b57417` |
| All four fitted asset hashes | Identical to the original expanded APK |
| All referenced APK file contents | 160/160 identical |
| New APK SHA-256 | `605f8ab4eb35eb3c3e52caacf31f89cde61caa1984bcf65009d004f7da7b25df` |
| Build / lint | Passed; zero errors/fatal issues, five warnings |
| JVM tests | 21 reported, three skipped, zero failures/errors |
| Emulator tests | 24 passed |
| Actual parity | 468 cases; zero class changes |
| Maximum logit / score error | 1.3351e-5 / 4.3857e-6 against the frozen Python reference |
| Offline repeated scans | 200 scored, zero abstentions on the four fictional probes |
| Permissions / signature | No INTERNET permission; signature verified |
| Physical phone | Pending actual team evidence |

All 84 research tests and the APK-layout regression test passed. The layout test confirms that unreferenced space is detected without treating it as an active asset. No new research test evaluation was opened; tests use synthetic fixtures.

New local APK: `deliverables/validation-20261006/SmishGuard-expanded-20261005-mbert-c3abc4bb-experimental-debug.apk`. The package filename retains the unchanged model ID; the dated directory and APK hash identify this packaging revision. Its manifest is beside it. The original 1.51 GB artifact remains under `deliverables/expanded-20261005/`, and all previous baseline artifacts remain unchanged.

The new verification run records timing as engineering evidence, but it is a separate session. It does not replace the original four-model common-session benchmark or establish a speed improvement. Research scores remain frozen.

Reproduction: preserve the existing APK and variant packaging state before rebuilding; run `:app:assembleMbert :app:lintMbert :app:testMbertUnitTest :app:assembleMbertAndroidTest` with the existing private parity directory, then `scripts/emulator_verify.py --variant mbert` and `scripts/package_mbert.py --output-dir <new private deliverables directory>`. Use `scripts/audit_apk_layout.py` to retain before/after layout evidence. Keep all APKs, assets, snapshots and parity fixtures outside public Git.

[Aggregate verification](validation-stage-verification-20261006.json) · [Remote phone guide](remote-phone-test-20261006.md) · [Original frozen report](four-model-comparison-20261005.md).
