# Private APK handoff — audit fixes, 9 October 2026

Built and packaged 9 October; final verification resumed 11 October 2026. Source commit: `470169efba0a10e1169827c369ee7ed64e647061`, branch `codex/thesis-completion-package`. Later evidence/harness/documentation commits do not change these APK bytes. The original APKs and audit reports are preserved.

Private output: `deliverables/audit-fixes-20261009-v030/` under the repository. This directory contains four APKs, the original build-time `APK-MANIFEST.json`, final `APK-MANIFEST-verified-20261011.json` (absolute paths, full per-asset fingerprints and completed API checks), `VERIFICATION-20261011.json`, `SHA256SUMS.txt`, `README-private-testers.md`, and the blank `PHONE-RESULTS.md`. No APK, weights, private fixtures, individual predictions or completed phone form belongs in public Git.

Version code **3**; version names below. All four IDs coexist and retain the existing development signing certificate. Signature verification and comparison with the preserved code-2 APK signer passed. Minimum manifest API is 26 (Android 8.0); target API is 36. Emulator runtime/API coverage is stated separately below, not inferred from the manifest. Only x86_64 emulators are exercised; bundled ABIs are not physical-device acceptance.

| Algorithm | Application ID | Version name | Exact model ID | Rule (unrounded score) | APK bytes |
|---|---|---|---|---|---|
| Logistic Regression | `ph.smishguard.lr` | `0.3.0-lr-experimental` | `expanded-20261005-lr-c3abc4bb` | >= 0.82 | 13,051,007 |
| Multinomial Naive Bayes | `ph.smishguard.nb` | `0.3.0-nb-experimental` | `expanded-20261005-nb-c3abc4bb` | >= 0.63 | 13,051,286 |
| Linear SVM | `ph.smishguard.svm` | `0.3.0-svm-experimental` | `expanded-20261005-svm-c3abc4bb` | >= 0.59 | 13,041,513 |
| float32 mBERT | `ph.smishguard.mbert` | `0.3.0-mbert-exploratory` | `expanded-20261005-mbert-c3abc4bb` | >= 0.8899999999999999 | 800,501,259 |

## APK filenames and SHA-256

- `SmishGuard-0.3.0-lr-expanded-20261005-lr-c3abc4bb-experimental.apk`
  SHA-256: `6e2134ae5f7731753671159c90fd8eb8304d8653b87fc6ab73f43a44735c1ae8`
- `SmishGuard-0.3.0-nb-expanded-20261005-nb-c3abc4bb-experimental.apk`
  SHA-256: `f7fb7cfd11eea2712b6177367df80fea14a1eff2b2b325593c21c7a7a73a4ece`
- `SmishGuard-0.3.0-svm-expanded-20261005-svm-c3abc4bb-experimental.apk`
  SHA-256: `c177ad552b209eb98ffb79a333da8d864ff48bae7f54ea8d134977882c8b09d5`
- `SmishGuard-0.3.0-mbert-expanded-20261005-mbert-c3abc4bb-experimental.apk`
  SHA-256: `728b163e5a728d67a1121e13f8ebacb8a44dabc1dc86edd6108d795e98c69bb1`

## Asset, permission and signature evidence

### lr

Bundled ABIs: arm64-v8a, armeabi-v7a, x86, x86_64. Asset SHA-256:

- `model.json`: `34aba6fba8399e9bac0369ab59637511155d36849edd3829269edc70450d4623`
- `review.properties`: `ddec5562eff939263f49ef6375e8eeb9075e2dd404068e594a2af0253988e2f5`
### nb

Bundled ABIs: arm64-v8a, armeabi-v7a, x86, x86_64. Asset SHA-256:

- `model.json`: `9a06358416cde665d80ed42f8a25cec34ed94cc6f6769fca38d0f56421968b49`
- `review.properties`: `44861770781c06b9ac4cd1783ecc18ebf80926d54ebe73ea4eda7e273eeec6ef`
### svm

Bundled ABIs: arm64-v8a, armeabi-v7a, x86, x86_64. Asset SHA-256:

- `model.json`: `d54aa2e06d126e70dc9aeeaf9bce17f8aa202c459b8b63890c50a302d2fc6d19`
- `review.properties`: `83bcc81221e5b6c47f6945a778c18613cdd6ec67e2747f59c6922738cd2bc2f7`
### mbert

Bundled ABIs: arm64-v8a, armeabi-v7a, x86, x86_64. Asset SHA-256:

- `LICENSE.txt`: `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`
- `model.json`: `044fa5b0a2fbbf3318ab45343b99ef1a3d5b0ebf580078732903669c107c0c14`
- `model.onnx`: `a319976073b401ac1e90c2b229bed8facb5be8c9f6367cf2df6f0781d8b57417`
- `vocab.txt`: `fe0fda7c425b48c516fc8f160d594c8022a0808447475c1a7c6d6479763f310c`

All assets match their frozen manifest entries and the APK contents. mBERT remains float32 with the same tokenizer and exact >=0.8899999999999999 policy. No retraining or test-set tuning was performed. Calibration still executes once.

Each APK requests RECEIVE_SMS and POST_NOTIFICATIONS plus its own signature-level DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION. **INTERNET, READ_SMS and SEND_SMS remain absent.** The existing receiver plumbing does not enable automatic model warnings. Reporting remains disabled; no endpoint or queue is added.

All signatures verify with certificate SHA-256 `7b15b0a216a5e78a2db8e4e9c489c0515ded705c683e7b3e0262c5e3c811c8c4`. These are private development-signed experimental packages, not production distribution. The mBERT archive is 800,501,259 bytes with 94,834 unreferenced ZIP bytes, within the 1 MiB guard; the previous inflated package is preserved.

## Verification and limitations

Exact aggregate results are in [audit-fixes-20261009-evidence.json](audit-fixes-20261009-evidence.json). Implementation, controlled failure reproduction and cancellation guarantees are described in [app audit fixes](app-audit-fixes-20261009.md).

All four Android builds and lint passed (zero errors, five existing dependency/target-version warnings each). JVM: LR/NB/SVM each 23 passed, 4 skipped; mBERT 24 passed, 3 skipped; zero failures/errors. Skips are named in the evidence, covering variant-inapplicable mBERT checks or unconfigured historical candidate/folded/private baseline parity. The current baseline export parity and mBERT tokenizer parity were configured. They reuse saved artifact references, not a reopened research evaluation.

Final emulator runs, completed 11 October (pass / skip / fail):

| Variant | API36 full | API36 recovery/narrow UI/resources | API26 offline/UI/recovery | API26 additional resources |
|---|---|---|---|---|
| LR | 26 / 0 / 0 | 11 / 0 / 0 | 25 / 0 / 0 | Not applicable |
| NB | 26 / 0 / 0 | 11 / 0 / 0 | 25 / 0 / 0 | Not applicable |
| SVM | 26 / 0 / 0 | 11 / 0 / 0 | 25 / 0 / 0 | Not applicable |
| mBERT | 25 / 1 / 0 | 11 / 1 / 0 | 24 / 1 / 0 | 1 / 0 / 0 |

Totals: **247 emulator passes, 3 skips, 0 final failures; 93 JVM passes, 15 skips, 0 failures/errors; 8 safe-handoff checks and 1 APK-layout regression passed.** These are test invocations, including repeats across variants/APIs. The three emulator skips are the classical-only `shippedModelSyntheticScanScreenshot` in mBERT configurations; actual mBERT boundary and native parity tests passed separately. Earlier failed attempts remain separately documented.

Both emulators use x86_64, four virtual CPUs and 4096 MiB RAM. All four package IDs coexist on both. API26 checks ran with airplane mode on and Wi-Fi disabled through standard Settings. Shared flow checks cover keyboard/scroll, lifecycle clearing, share, failure/retry and accessibility semantics. Additional API36 checks use 320 dp width and 200% font; the fictional long-result screenshot was visually inspected for readable wrapping and unobscured navigation. Human TalkBack and landscape/physical acceptance remain pending.

On each API, saved classical parity checks cover 461 cases per variant (456 scored, 5 abstentions); maximum score error is below 2e-15. mBERT compares 468 saved cases, with maximum logit error 1.33514404296875e-5, maximum score error 4.385687211116984e-6 and zero classification changes. Its aggregate `scored=200` is a separate warm latency scan count, not the parity cohort denominator. Tokenizer IDs/masks/types remain compatible with frozen references. Native resource tests on both APIs replace deliberately incomplete cache bytes with the exact frozen model hash, remove stale pending copies and verify idempotent close/use-after-close rejection. Privacy inspection found zero raw fixture markers in two inspected preference files per variant; immutable verified model-cache bytes are excluded from message-storage checks.

The first LR API36 attempt on 9 October passed seven groups but failed instrumentation startup for the large-font group (recorded background-start ANR). The final run on 11 October rechecks the artifact and retains the failed run separately. No physical failure is inferred from that emulator/harness event.

Two mBERT test corrections are retained in the failure record: a boundary fixture incorrectly assumed lowercase `hello` was a single cased WordPiece (corrected to verified `Hello`), and JUnit rejected the native-resource test's inferred non-void return (corrected to explicit Unit). Production code and APK bytes were unchanged by these test corrections. Test/harness source is `240af8cdad474ec11cf6c0d3ecd6d24bfd052c01`; APK source remains `470169efba0a10e1169827c369ee7ed64e647061`.

Physical-device testing remains **pending**: no authorized real device was attached or tested. No Xiaomi secure-FRP bypass was attempted. TalkBack reading order and user comprehension remain human tasks even when automated semantics pass. Independent annotation/adjudication and new-cohort prospective research also remain pending.

## Private tester instructions

Use the concise README beside the APKs. Verify SHA-256, install with Android's installer or `adb -s <authorized-device> install -r <APK>`, and check the expected Home model identity. Code 3 upgrades compatible code 2; record a signature/installer restriction rather than bypassing device protection. Preserve preferences unless an intentional uninstall is chosen.

Use fictional SMS only; test financial and nonfinancial phishing prompts, ordinary messages, blank/random inputs, offline paste/share, policy details, mBERT truncation, repeated submit, loading/retry, clear/navigation/background and restart. At 200% font with keyboard and narrow/landscape layouts, check all actions plus TalkBack result/notice announcements. A slow notice appears at seven seconds; the UI stops waiting after sixty. Cancellation does not terminate a synchronous native call; a new request is blocked until it returns, and a stuck call needs Android Force stop/reopen. No message is retained for retry.

Return one completed PHONE-RESULTS.md per actual device/variant through the private team folder. Record date, APK hash, API/ABI, install/update outcome, cold/warm times, Pass/Fail/Not tested and sanitized reproducible observations. Blank worksheets, emulator results and fictional predictions are not physical or human research evidence.
