# Baseline-first training reproduction and test report

The executable research deliverable is [SmishGuard_Model_Training_and_Evaluation.ipynb](../research/SmishGuard_Model_Training_and_Evaluation.ipynb). It embeds the actual dataset-cleaning, splitting, TF-IDF, fitting, calibration, prediction, threshold and metric code. Public notebook outputs contain aggregate statistics and plots; trained vocabulary, datasets and populated audit ledgers remain ignored.

## Inputs and environment

Use Python 3.12 and [bantaytext-requirements.txt](../research/bantaytext-requirements.txt). The executed environment used Python 3.12.5, numpy 2.2.6, scipy 1.15.3, sklearn 1.6.1, pandas 2.3.3 and matplotlib 3.10.7. Notebook execution uses nbformat 5.10.4, nbclient 0.10.2 and ipykernel 6.30.1. The private run stores the exact expanded matrix, input/cleaned/split hashes, versions, OOF membership and frozen selected candidates. Seed 42 applies to splitting, classifiers and grouped training calibration folds.

Required input is an authorized, masked `dataset.json`: a list of records containing `id`, `text`, integer `label` (ham=0, smishing=1), `source`, `category`, `language`, plus `needs_review` and `template_group` when available. These are the established source-joined fitting views, not arbitrary raw messages. They preserve inherited labels; this task supplies no independent human label confirmation. Source-specific original labels, masking and holds are documented in the existing private intake ledger and [aggregate input audit](bantaytext-input-audit-20261013.json).

For Colab, install the dependencies using the notebook's installation cell, upload the authorized `dataset.json`, and run top-to-bottom. Optional `source-metadata.csv` contains only `id,source_category`; it enables OTP/government/advertising/notification evaluation without uploading raw SMS. The notebook falls back to these uploaded filenames. Use a fresh `RUN` directory for every execution. No credentials, Drive mount or private Windows path is required. JVM checks require the local Android repository and Java/SDK; they cannot run in an ordinary Colab session.

The default local input is `research/data/newdata-20261013/experiment-v2/dataset.json`, SHA-256 `c3abc4bb23742226deab491821c1828559d895242da55267c77ae6f7dfa07b21`. That corpus contains no newly eligible records and is historically exposed. Raw source snapshots and original package remain private; a public checkout does not include the dataset or usable model parameters.

## Commands

Run from repository root in PowerShell. These commands assume the authorized local corpus is present:

```powershell
$env:PYTHONPATH='research'
$env:PYTHONIOENCODING='utf-8'
research\.venv\Scripts\python.exe -m pip install -r research\bantaytext-requirements.txt
research\.venv\Scripts\python.exe scripts\audit_bantaytext_inputs.py
research\.venv\Scripts\python.exe scripts\create_bantaytext_notebook.py
# A NEW directory is mandatory. Existing results must remain intact.
research\.venv\Scripts\python.exe scripts\execute_bantaytext_notebook.py --run runs/bantaytext-20261013/NEW-NOTEBOOK-RUN
```

The same workflow can run without Jupyter:

```powershell
research\.venv\Scripts\python.exe -m smishguard.bantaytext_workflow research/data/newdata-20261013/experiment-v2/dataset.json research/runs/bantaytext-20261013/NEW-CLI-RUN
```

For the successful delivered notebook run:

```powershell
$run='research/runs/bantaytext-20261013/notebook-run-v3'
research\.venv\Scripts\python.exe scripts\prepare_bantaytext_active_parity.py "$run/parity"
$env:JAVA_TOOL_OPTIONS='-Djdk.net.unixdomain.tmpdir=C:/sg-nonexistent-socket-dir'
$parityPath=(Resolve-Path "$run/parity").Path
.\gradlew.bat :app:testDevelopmentUnitTest :app:assembleDevelopment :app:lintDevelopment "-PmodelParityDir=$parityPath" --console=plain
research\.venv\Scripts\python.exe -m unittest discover -s research/tests -q
research\.venv\Scripts\python.exe -m unittest discover -s scripts -p 'test_*.py' -q
research\.venv\Scripts\python.exe scripts\report_bantaytext_workflow.py $run
git diff --check
```

The report command verifies every frozen candidate hash, recomputes all test metrics from saved scores, checks protected app/model hashes, validates executed notebook outputs and reads actual JVM XML results. It does not fit or select a model.

## Execution and validation

- Before changing training: 108 existing research tests passed; the previous 17-model comparison was recomputed from its finalized predictions using `report_new_dataset_comparison.py`, with the output saved under ignored `output/`. This was evaluation reproduction, not an independent fresh fit or a prospective performance claim.
- The active supplied model's original 1,276-row baseline was calculated explicitly as **resubstitution** on its claimed entire training corpus. It has 12 FP/0 FN and F1 0.9737; it cannot be compared with independently held-out candidate metrics or used to choose a replacement. Exact original training/artifact reproduction remains unresolved.
- The first new notebook attempt failed on record-copying before fitting; that attempt remains private. The cleaning code was fixed, and five new meaningful tests passed. A complete 28-cell run then succeeded. A final run adds original-category targeted evaluation and executes all 30 cells top-to-bottom; fitted configurations are unchanged.
- 113 research tests passed, including the five new conflict, baseline-order, grouped-split, train-only vocabulary/OOF and metric guards. Script unittest discovery passed its one unittest; this is not a claim that every standalone script is a unittest suite.
- Development assemble, lint and JVM checks passed. With the real private exports configured, 34 JVM tests ran with zero failures/errors and four conditional skips for unrelated private candidate/folded/variant parity. The new active/parity tests and existing real-export parity test executed without skips.
- Sixteen safe active-model probes matched Python scores within 1e-10 (observed maximum error 5.55e-17), including seven required input abstentions. The fitted portable comparator's ten probes also passed Python/JVM score and decision parity. Scores are finite and explicitly not validated probabilities; empty/oversized comparator inputs fail.
- Eleven protected app/model hashes are unchanged. No permissions, consent, incoming receiver behavior, reporting safeguards, privacy flow or active model was modified. No server, network permission, cloud inference, automatic deletion/blocking/forwarding or telemetry was introduced.
- No emulator or physical-device testing was performed in this task: `adb devices` returned no connected targets. Phone latency/memory and deployment generalization remain unmeasured. Historical emulator results elsewhere in the repository are not new results for this retraining.

Local logs are under ignored `output/bantaytext-*.log`. Failed attempts and all full fitted pipelines, calibration folds, thresholds, ledgers, membership, synthetic probe fixtures and predictions remain under ignored `research/runs/bantaytext-20261013/`. The public notebook and aggregate reports contain no original SMS examples or learned feature vocabulary. Nothing was committed, pushed or published.

## Modified files and deliverable status

- Training/cleaning/evaluation: `research/smishguard/bantaytext_workflow.py`; frozen experiment summary and notebook dependencies: `research/bantaytext-experiment-20261013.json`, `research/bantaytext-requirements.txt`.
- Executed research artifact: `research/SmishGuard_Model_Training_and_Evaluation.ipynb`; generation/execution tools: `scripts/create_bantaytext_notebook.py`, `scripts/execute_bantaytext_notebook.py`.
- Source/active-model audit, safe private probe preparation and verified reporting: `scripts/audit_bantaytext_inputs.py`, `scripts/prepare_bantaytext_active_parity.py`, `scripts/report_bantaytext_workflow.py`.
- Meaningful Python guards: `research/tests/test_bantaytext_workflow.py`; actual-model JVM parity/input tests: `android/app/src/test/java/ph/smishguard/BantayTextParityTest.kt`.
- Aggregate dataset audit, random/grouped results and error analysis: `docs/bantaytext-input-audit-20261013.json`, `docs/bantaytext-comparison-20261013.{md,json,csv}`. This file is the commands/test report; `docs/bantaytext-model-card-20261013.md` is the research card.
- Existing navigation/contract/card updated: `research/README.md`, `docs/model-contract.md`, `docs/model-card.md`. Pre-existing unrelated untracked research files were preserved.
- Existing-model baseline, conventional baselines, BantayText candidates, NB/LR/SVM comparisons, independent metric arithmetic, grouped leakage checks, FP/FN analysis, notebook execution, Python/JVM parity and Android build/lint checks: completed and documented.
- Selected research pipeline and exact preprocessing parameters: saved privately. Release-model integration: deliberately not performed because independent validation and native compatibility for the selected SVM are unresolved; the active model remains usable.
- Chronological testing, independently confirmed financial/OTP ground truth, unbiased prospective validation and phone resource testing: unavailable and explicitly unclaimed.

## Remaining release work

Complete source/label/privacy review and collect a genuinely unseen, independently labeled financial-SMS cohort; freeze its protocol before prediction. Establish calibration/threshold quality and subgroup support. Review a native feature contract for the research candidate, preserve exact vocabulary/tokenization/stopword filtering/bigram ordering/IDF/L2/calibration/class mapping, then run real export parity and phone resource checks before replacing the active model. A new random split cannot satisfy these requirements.
