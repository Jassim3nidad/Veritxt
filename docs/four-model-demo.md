# Reproduce and demonstrate the preliminary models

Run from the repository root in PowerShell. Private inputs and fitted outputs are deliberately absent from public Git. Existing frozen runs refuse a second training/evaluation opening. To reproduce independently, use a new private output directory and retain the old run. Do not change the saved 1,068-record membership or partition assignments to improve results.

## Recorded baseline commands

```powershell
$env:PYTHONPATH='research'
$baseline='research/data/comparison-20261001/experiment-v1'
research/.venv/Scripts/python.exe -m smishguard.preliminary_compare prepare `
  'research/data/comparison-20261001/extracted/smishguard_PRIVATE_data/data/smishguard_dataset.csv' `
  research/data/source-evidence-pinned $baseline
research/.venv/Scripts/python.exe -m smishguard.preliminary_compare train $baseline
research/.venv/Scripts/python.exe -m smishguard.preliminary_compare evaluate $baseline
```

The historical run uses Python 3.12.5, scikit-learn 1.6.1, NumPy 2.2.6 and SciPy 1.15.3. Its protocol/code/data/split hashes and all trial choices are retained in the aggregate manifest. For each of `lr`, `nb`, `svm`, copy that run's `model.json` and `review.properties` to its ignored `android/app/src/<algorithm>/assets/` only after its automated content screen passes. Preserve historical asset backups. The supplied LR4 files do not belong in these directories.

```powershell
$env:JAVA_TOOL_OPTIONS='-Djdk.net.unixdomain.tmpdir=C:/sg-nonexistent-socket-dir'
$env:PATH="$env:LOCALAPPDATA/Android/Sdk/platform-tools;$env:PATH"
# Substitute Nb/nb and Svm/svm for the other two builds.
./gradlew.bat :app:assembleLr :app:lintLr :app:testLrUnitTest :app:assembleLrAndroidTest `
  -PinstrumentedBuild=lr "-PmodelParityDir=$((Resolve-Path "$baseline/lr/parity").Path)" --console=plain
research/.venv/Scripts/python.exe scripts/emulator_verify.py --variant lr `
  --output research/data/comparison-20261001/emulator-lr.json `
  --demo-screenshots deliverables/comparison-20261001/screenshots/lr
research/.venv/Scripts/python.exe scripts/package_comparison.py lr --output-dir deliverables/comparison-20261001
```

The packaging tool refuses to replace an existing APK with different bytes. Existing deliverables are the artifact versions actually tested; rebuilding after later shared-source changes does not replace their recorded checksums.

## mBERT local execution

Use an isolated environment and the [resolved dependency lock](../research/mbert-dependency-lock.txt). Install CUDA PyTorch from its official index; this does not require cloud compute. The Windows CPython 3.12 wheel hash is recorded in the lock. `pip check` passed. Public model downloads precede training; training and evaluation set Hugging Face offline/telemetry-disable flags and use local files only.

```powershell
py -3.12 -m venv research/data/mbert-20261002/venv
$python='research/data/mbert-20261002/venv/Scripts/python.exe'
& $python -m pip install torch==2.7.1 --index-url https://download.pytorch.org/whl/cu126
& $python -m pip install -r research/mbert-dependency-lock.txt
& $python -m pip check
& $python -c "from huggingface_hub import snapshot_download; snapshot_download('google-bert/bert-base-multilingual-cased',revision='3f076fdb1ab68d5b2880cb87a0886f315b8146f8',allow_patterns=['model.safetensors','config.json','tokenizer.json','tokenizer_config.json','vocab.txt','README.md'],local_dir='research/data/mbert-20261002/base')"
$env:PYTHONPATH='research'
$mbert='research/data/mbert-20261002/experiment-v2'
& $python -m smishguard.mbert_experiment prepare $baseline research/data/source-evidence-pinned $mbert
& $python -m smishguard.mbert_experiment train research/data/mbert-20261002/base $mbert
& $python -m smishguard.mbert_evaluate $mbert
```

Check the downloaded safetensors SHA-256 `876f584f15ebf14887dec17539c114bb99a032e96b9e72507a51c41e205337fc` and vocabulary `fe0fda7c425b48c516fc8f160d594c8022a0808447475c1a7c6d6479763f310c` before training. The original `experiment-v1` preparation was superseded by `experiment-v2` before training to correct explicit UTF-8 reading; v1 was never trained. No baseline result changed.

If export fails after evaluation, `& $python -m smishguard.mbert_evaluate $mbert --export-only` reuses the exact frozen checkpoint and does not rewrite metrics or open a new research evaluation. Do not remove evaluation markers to retune. Keep failed numerical diagnostics and document any runtime correction.

After actual export/tokenizer/parity and content checks pass, install only `app-assets/model.json`, `model.onnx`, `vocab.txt` and the [Google BERT Apache-2.0 license](https://github.com/google-research/bert/blob/master/LICENSE) into ignored `android/app/src/mbert/assets/`.

```powershell
./gradlew.bat :app:assembleMbert :app:lintMbert :app:testMbertUnitTest :app:assembleMbertAndroidTest `
  -PinstrumentedBuild=mbert "-PmbertParityDir=$((Resolve-Path $mbert).Path)" --console=plain
research/.venv/Scripts/python.exe scripts/emulator_verify.py --variant mbert `
  --output research/data/mbert-20261002/emulator-results.json `
  --demo-screenshots deliverables/comparison-20261001/screenshots/mbert
research/.venv/Scripts/python.exe scripts/package_mbert.py --output-dir deliverables/comparison-20261001
```

These are execution instructions, not claims that an unfinished step passed. Consult the comparison report and aggregate verification for actual outcomes. Private data, predictions, models, tokenizer assets, APKs and real-message parity fixtures remain local.

The original AVD lacked storage for mBERT. The verified fourth APK used a separate `SmishGuard_Comparison_API36` Pixel 6 / API-36 x86_64 AVD with 4 virtual CPUs, 4096 MiB RAM and a 12 GiB data partition. The original AVD was preserved. With the larger emulator booted, the same-session four-model measurement was:

```powershell
research/.venv/Scripts/python.exe scripts/benchmark_four_models.py `
  --output research/data/mbert-20261002/common-device-benchmark-20261004.json
```

This installs hash-verified preserved APKs and their already-built private test APKs, uses one app process at a time, records identical 20-warmup/200-scan conditions, and restores airplane/Wi-Fi state. Use a new output filename for another measurement; the command refuses to overwrite its previous record.

## Short demonstration

Install the four distinct application IDs if their APK verification is complete. Keep the LR4 rollback APK separate. Enable airplane mode, turn Wi-Fi off, open each app, and show the algorithm/model version. Paste the same fictional message into each app:

1. `Your account is suspended. Verify your password at https://account.example now.`
2. `Bayad na po. Salamat sa tulong, kita tayo bukas.`
3. Empty input, then `qwerty`, then `123456` to demonstrate abstention.

Record each actual result without promising identical decisions. Repeat a scan, then share a fictional message from another app into SmishGuard. Scores are experimental model outputs; different algorithms/calibrators need not assign comparable percentages. Reporting and automatic warnings stay disabled. Explain that screenshots and emulator timing demonstrate software behavior; they do not validate phishing labels or phone performance.

The validation-selected thresholds differ: LR 0.74, NB 0.30, SVM approximately 0.41 and mBERT 0.09. Thus mBERT may label a score below 50% positive. Its captured benign Taglish example is an illustrative false positive and remains in the demonstration evidence. Do not retune the model or relabel that example to improve the presentation.
