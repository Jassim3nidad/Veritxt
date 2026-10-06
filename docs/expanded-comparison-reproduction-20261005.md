# Reproduce the expanded development experiment

Run from the repository root. All original messages, worksheets, fingerprints of
individual records, membership manifests, fitted models, private test fixtures and
APKs stay under ignored `research/data/` or `deliverables/`. No public data download
or upload is part of training. Retain the original ZIP and extracted files unchanged.

The inspected ZIP is `smishguard_dataset_2026-10-04.zip`; its five files contain CSV
outputs, review workbook, README and builder, but no raw source bundle. ZIP paths,
sizes and link entries were checked before extraction into
`research/data/expanded-20261005/original/`. Use a new directory for a reproduction;
never remove a freeze or test-opening marker to retune an existing experiment.

The builder was read before use. Its complete build is **not executed**. The audit
accepts only the inspected SHA-256, then evaluates its pure rule definitions before
the source-loading section. Hard-coded `/home/claude` paths are never run. A future
full raw-build reproduction needs all original raw files and an explicitly
configurable input/output adapter; CSV validation is not that reproduction.

Use the existing hash-pinned ZERO v1, Chua v15 and BwandoWando v49 snapshots under
`research/data/source-evidence-pinned/`. Preserve attribution in
[source evidence](source-evidence.md) and the aggregate preparation record. This
run uses BwandoWando only for local noncommercial development; it supplies no new
source clearance for GitHub/team records and publishes no derived fitted artifacts.

```powershell
$env:PYTHONPATH='research'
$run='research/data/expanded-20261005/experiment-v1'
$package='research/data/expanded-20261005/original/smishguard_dataset_2026-10-04'
$python='research/.venv/Scripts/python.exe'
$bertPython='research/data/mbert-20261002/venv/Scripts/python.exe'
& $python -m smishguard.expanded_prepare $package research/data/source-evidence-pinned $run
& $python -m smishguard.expanded_exposure $run
& $python -m smishguard.expanded_audit_extra $run
& $python -m smishguard.expanded_train baselines $run
& $bertPython -m smishguard.expanded_train mbert $run --base research/data/mbert-20261002/base
& $bertPython -m smishguard.expanded_evaluate $run
```

The first preparation refuses an existing output directory. For another run, change
the directory. Model version includes experiment date, algorithm and dataset hash;
separately version any changed training configuration. Existing baseline freezes
are verified and resumed; mBERT resumes its optimizer/scaler/RNG state from
`mbert/resume.pt`. The selected checkpoint remains separate. A completed mBERT
freeze is never retrained. Test evaluation requires all four completed freezes,
verifies model hashes and refuses a second opening. `--export-only` recovers export
from the same recorded evaluation and does not rewrite research metrics.

Dependencies: [baseline pins](../research/requirements.txt) and
[mBERT lock](../research/mbert-dependency-lock.txt), Python 3.12.5. Both environments
pass `pip check`. The base model revision, weights/vocabulary hashes, training
settings, device and duration are recorded. Local model loads and training disable
Hugging Face networking and telemetry. mBERT is full multilingual BERT, not a smaller
substitute; the faithful first export uses float32 ONNX Runtime 1.22.0.

The actual training implementation is retained in commit `56d0ddb`; its hash is
also recorded in the mBERT configuration. After all fitted pipelines were frozen,
the Windows process-memory diagnostic was corrected to use 64-bit handle types.
The initial zero readings are reported as unavailable, never as zero memory use.
This diagnostic fix changes no model, score, split or training setting. Use the
original implementation when resuming that specific checkpoint because its code
hash is pinned; future fresh runs use the corrected probe.

Before staging any model, copy previous Android assets and app/test APK outputs
to a separate ignored backup and check their hashes. Stage each baseline's
`model.json` and `review.properties` only into its matching `src/lr`, `src/nb` or
`src/svm` assets. Stage only the four files from `mbert/app-assets` for mBERT.
The old deliverables remain at `deliverables/comparison-20261001/`.

```powershell
$env:JAVA_TOOL_OPTIONS='-Djdk.net.unixdomain.tmpdir=C:/sg-nonexistent-socket-dir'
$env:PATH="$env:LOCALAPPDATA/Android/Sdk/platform-tools;$env:PATH"
# Repeat with Nb/nb and Svm/svm.
./gradlew.bat :app:assembleLr :app:lintLr :app:testLrUnitTest :app:assembleLrAndroidTest `
  -PinstrumentedBuild=lr "-PmodelParityDir=$((Resolve-Path "$run/lr/parity").Path)" --console=plain
& $python scripts/emulator_verify.py --variant lr `
  --output research/data/expanded-20261005/emulator-lr.json `
  --demo-screenshots deliverables/expanded-20261005/screenshots/lr
& $python scripts/package_comparison.py lr --output-dir deliverables/expanded-20261005
./gradlew.bat :app:assembleMbert :app:lintMbert :app:testMbertUnitTest :app:assembleMbertAndroidTest `
  -PinstrumentedBuild=mbert "-PmbertParityDir=$((Resolve-Path "$run/mbert").Path)" --console=plain
& $python scripts/emulator_verify.py --variant mbert `
  --output research/data/expanded-20261005/emulator-mbert.json `
  --demo-screenshots deliverables/expanded-20261005/screenshots/mbert
& $python scripts/package_mbert.py --output-dir deliverables/expanded-20261005
& $python scripts/benchmark_four_models.py --apk-dir deliverables/expanded-20261005 `
  --output research/data/expanded-20261005/common-device-benchmark.json
& $python scripts/verify_research.py
& $python scripts/test_comparison_model_guards.py
& $python scripts/check_staged.py
```

These commands are a reproduction procedure, not evidence of success. The dated
results and verification reports record actual completion. The comparison emulator
has four virtual CPUs, 4096 MiB configured RAM and a 12 GiB data partition; all four
variants coexist. Cold loading and warm timing are separate. Measurements are
emulator results, not physical-phone performance. Screenshots use the same fictional
messages and retain unfavorable predictions. Model scores remain experimental.
