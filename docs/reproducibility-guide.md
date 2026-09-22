# Reproducibility guide

Run from repository root on Windows, Python 3.12 with `research/requirements.txt`, JDK17, Gradle wrapper 8.13, SDK36 and Build Tools35.0.0. Local configuration and private inputs are excluded from Git. Setup is in README and `research/README.md`. Never load a pickle from an untrusted source.

## Permitted command now

```powershell
research\.venv\Scripts\python.exe scripts/verify_research.py
```

This runs only synthetic research unit/pipeline tests plus installed dependency consistency. No approved independent labels are currently available, so no real-data training/evaluation is authorized by this command. Fixture scores are not thesis results. Vulnerability database scanning is separate from `pip check` and is not implied.

## Private audit reproduction

Use fresh private output/report paths to preserve previous evidence. The package is already local; no download or URL visiting is needed.

```powershell
$env:PYTHONPATH='research'
research\.venv\Scripts\python.exe -m smishguard.audit_package research/data/package-audit/original/smishguard_model_package-20260920T144757Z-1-001.zip --private-dir research/data/audit-reproduction --report research/data/audit-reproduction/audit.json
research\.venv\Scripts\python.exe -m smishguard.freeze_dataset research/data/package-audit/original/smishguard_dataset.csv research/data/audit-reproduction/derived/review-ledger.csv --output research/data/audit-reproduction/manifest.json --summary research/data/audit-reproduction/summary.json
```

Compare parsed audit/summary values and hashes against public records. Freeze retains raw-record hashes, anonymous IDs, source hashes and existing near-template components without raw message text. It does not mark any row eligible. Current grouping checks the full source solely to prevent leakage; dataset statistics remain inherited labels.

## Android checks

```powershell
$env:JAVA_HOME='C:\Program Files\Eclipse Adoptium\jdk-17.0.16.8-hotspot'
$env:PATH="$env:LOCALAPPDATA/Android/Sdk/platform-tools;$env:PATH"
.\scripts\build.ps1 -Variant development -EmulatorTests
# After stopping API36 and starting dedicated API26 on port 5556:
research\.venv\Scripts\python.exe scripts/emulator_api26_verify.py
```

The supplied model asset is private; collaborators need authorized local access to reproduce the development build. The debug variant is model-free. Verifiers reject physical devices and clear only the dedicated emulator app's data; synthetic messages can remain in its default messaging app. They restore radio/font settings. No phone installation is part of these commands. For uncached unit/lint/build verification use Gradle `--rerun-tasks` with the JDK socket workaround from `scripts/build.ps1`.

## After researchers complete evidence

1. Follow `annotation-protocol.md`, validate/adjudicate, import the reviewed intake using `research/README.md`. Preserve the original independent responses and all held reasons.
2. Freeze the experiment matrix. `group` now uses 20 stratified group folds allocated 11/3/3/3 where there are at least 20 groups and 20 records per class, otherwise the existing group-shuffle method; fixed seed, no retries for better scores. This approximates balance, does not guarantee feasibility, and records `split_policy_version`. All four partitions must contain both labels. Old split artifacts remain historical and must not be overwritten/reinterpreted under the new version.
3. Run the documented `compare` then sealed `evaluate` sequence once. Metrics add accuracy/specificity, cluster bootstrap, anonymous errors, guarded source/language subgroups, model/data/split hashes, source commit, feature configuration and UTC evaluation time. All output stays private until publication review. A model hash identifies the artifact version.
4. For the unchanged supplied model, use a genuinely unseen approved cohort and this separate command (only after recording real independence evidence):

```powershell
research\.venv\Scripts\python.exe -m smishguard.supplied_evaluate research/data/independent-approved/approved.csv research/data/package-audit/original/model_export_final.json research/data/package-audit/original/smishguard_dataset.csv research/data/independent-approved/supplied-evaluation.json --independent-cohort-reference COHORT_EVIDENCE_REFERENCE
```

Replace the evidence-reference placeholder with an actual controlled record. The fixed model retains strict >0.5; baseline calibrated models use their separately frozen >= threshold contract. Python Unicode version must match the supplied contract. No training or comparison of real data has been run in this completion pass.

## Private packaging

After reviewed files are tracked, build and run:

```powershell
research\.venv\Scripts\python.exe scripts/check_staged.py
research\.venv\Scripts\python.exe scripts/package.py --variant development --output-dir deliverables/thesis-20260923
```

The package contains a local experimental APK, a model-free source ZIP, checksums and sharing notice. The source ZIP uses reviewed tracked paths and rejects private/generated member classes. APK CRC/model hash/asset checks and SDK signature/alignment checks are separately recorded. The model-bearing APK is not a public release. Do not upload it or research private files until redistribution review is resolved.
