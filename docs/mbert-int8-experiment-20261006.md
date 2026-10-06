# Separate mBERT INT8 deployment experiment

Revised thesis title: **Pending finalization**. Scope: **all SMS phishing**, clarified by the team without assumed adviser approval. This deployment experiment does not change the four frozen evaluation models, their thresholds or their historical results. Original fitted assets and all five original/repackaged APKs were verified against their prior manifests.

The existing fitted float32 ONNX export was converted once using ONNX Runtime 1.22.0 dynamic signed INT8 quantization, per-channel constant MatMul weights and Gather embeddings. No training, checkpoint selection, calibration fitting, threshold adjustment or quantization-configuration search was performed. The tokenizer, sequence length of 160, fitted sigmoid and exact threshold `0.8899999999999999` were retained. Dynamic quantization was chosen as the initial transformer deployment experiment following the [ONNX Runtime guidance](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html). Actual compatibility was checked with the project's pinned runtime rather than inferred from that guidance.

| Measure | Float32 reference | Separate INT8 experiment |
|---|---:|---:|
| ONNX model bytes | 711,555,338 | 178,926,534 |
| APK bytes, versus clean float32 package | 800,410,184 | 267,781,492 |
| Historical test accuracy, 448 records | 92.63% | 92.63% |
| Historical phishing precision | 100.00% | 100.00% |
| Historical phishing recall | 41.07% | 41.07% |
| Historical phishing F1 | 58.23% | 58.23% |
| Historical confusion TN / FP / FN / TP | 392 / 0 / 33 / 23 | 392 / 0 / 33 / 23 |
| Host model-load time | 1,272.6 ms | 476.3 ms |
| Host warm inference p50 | 159.6 ms | 87.8 ms |
| Host warm inference p95 | 183.4 ms | 119.4 ms |

The model is **74.85% smaller**; the APK is **66.54% smaller** than the clean float32 package. The preserved earlier 1.51 GB APK includes historical ZIP-layout overhead and is not the quantization size baseline. MB here is decimal.

Accuracy is a separate descriptive check on the already opened historical test with inherited, unconfirmed labels. It is not fresh, independent accuracy and was not written into the original four-model report. The float32 replay reproduced its saved accuracy/F1. There were zero decision changes on those 448 records and zero on 20 synthetic probes. Across all 468 cases the maximum absolute logit difference was 1.4163, maximum score difference 0.4070 and mean absolute score difference 0.01370. Those score shifts matter despite unchanged decisions: future near-threshold decisions may differ. No claim of accuracy equivalence or improved calibration is established.

Host timings used CPUExecutionProvider, two intra-op threads, one inter-op thread, 20 warmups and 100 timed inferences per model over the same 20 synthetic probes. Tokenization was outside the timed session call. The float32 and INT8 sessions ran sequentially. Android emulator startup/build activity also occurred on the host, so these are descriptive engineering timings under uncontrolled competing load, not an isolated causal speed benchmark or physical-phone result.

## Android verification and private artifact

The experimental build type is `mbertQuantized`, with application ID `ph.smishguard.mbert.int8`. It reuses the existing detector/tokenizer and minimalist UI. Runtime and build guards allow INT8 only in this separate variant and bind its reference model hash and unchanged inference policy. The original `mbert` build still requires float32. Reporting and automatic warnings remain disabled; the signed APK has no INTERNET permission and contains only the four intended model assets.

API 36 x86_64 emulator verification passed. Twenty synthetic tokenization/logit/score/decision cases matched the INT8 host reference: zero logit differences, maximum score error `1.11e-16`, zero decision changes. Twenty warmups and 200 repeated scans over four synthetic messages produced 200 scored results and no abstentions; p50 was 159.9 ms and p95 252.5 ms. Cold detector load was 3,031.1 ms. These emulator timings include the app's inference path and cannot be compared directly with host timings or an earlier float32 emulator session to claim a speedup.

Build, lint and JVM checks passed: 21 JVM tests reported, three skipped, zero failures/errors; five lint warnings and no errors. Emulator checks also covered offline scans, lifecycle/privacy, SMS decoding/injection, notification policy, reporting rejection, 2× font layout and private-storage fixture checks. An initial parity test failed because the test APK was built before the synthetic parity asset was produced; rebuilding the test APK resolved it, and the full verifier passed. Both evidence versions are retained privately.

Minimum SDK remains API 26, but this INT8 variant was runtime-tested only on the API 36 emulator. ARM physical devices, vendor behavior, real-phone installation/loading and physical speed/memory remain pending groupmate evidence. No physical-phone result or fix is claimed.

Private APK: `deliverables/mbert-int8-20261006/SmishGuard-expanded-20261005-mbert-c3abc4bb-int8-v1-experimental-debug.apk`.

APK SHA-256: `4c353ef0c7bf01f0a85149defd03dddd59f55c3a426283e1cefaa5c7adf75a09`.

INT8 model SHA-256: `db61cf99b394987640722e4f430bfa071ef16d852fb9a805e8300f19df911826`.

Float32 reference SHA-256: `a319976073b401ac1e90c2b229bed8facb5be8c9f6367cf2df6f0781d8b57417`.

## Reproduction

Use a new private experiment and deliverables directory; never replace originals. Conversion and benchmark require the existing isolated `research/mbert-requirements.txt` environment. Finish the benchmark before building instrumented tests, because it creates their synthetic parity asset.

```powershell
$env:PYTHONPATH='research'
$py='research/data/mbert-20261002/venv/Scripts/python.exe'
$experiment='research/data/mbert-int8-20261006/experiment-v1'
# These destinations already exist locally; choose a new version to reproduce.
& $py -m smishguard.mbert_quantize convert android/app/src/mbert/assets $experiment
& $py -m smishguard.mbert_quantize benchmark android/app/src/mbert/assets $experiment --historical research/data/expanded-20261005/experiment-v1
# Omit --historical to run only synthetic compatibility/timing probes, with no accuracy.
# Copy the four experiment app-assets into the ignored src/mbertQuantized/assets.
# Retain any prior experimental assets before installing a new experimental version.
$parity=(Resolve-Path $experiment).Path
.\scripts\build.ps1 -Variant mbertQuantized -MbertParityDir $parity -EmulatorTests
research/.venv/Scripts/python.exe scripts/package_mbert.py --variant mbertQuantized --output-dir deliverables/mbert-int8-20261006
```

Only sanitized aggregate evidence is public: [verification record](completion-engineering-verification-20261006.json). Models, tokenizer vocabularies, APKs, raw datasets, historical predictions and populated annotation files remain private and ignored by Git.
