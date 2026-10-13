# SmishGuard research and model workflow

Latest 13 October update: [raw-SMS preparation replay and parity](../docs/bantaytext-raw-sms-validation-20261013.md)
reconstructs all 2,554 source views and verifies a test-only native adapter on 33
fictional probes. Inherited labels are an explicit limitation, not a blanket demand
for another labeled upload; phone checks are completed as reported by the user.

Additional candidate checks: [predeployment validation](../docs/bantaytext-predeployment-validation-20261013.md)
adds paired template intervals, source-complement-only operating points, targeted
FPR intervals, frozen-input stress checks and actual selected-SVM JVM/emulator
feature/score parity. `smishguard.predeployment_validation` preserves the original
candidate and requires a new private output directory. Release remains unapproved:
the supplied October 12 ZIP is already used and independent labels are still blank.

13 October baseline-first retraining: the fully executed
[SmishGuard_Model_Training_and_Evaluation.ipynb](SmishGuard_Model_Training_and_Evaluation.ipynb)
compares standard NB/LR/SVM before a frozen BantayText-informed feature,
hyperparameter, calibration and threshold matrix on random and template-grouped
partitions. See the [comparison](../docs/bantaytext-comparison-20261013.md),
[reproduction/test report](../docs/bantaytext-reproduction-20261013.md) and
[research candidate card](../docs/bantaytext-model-card-20261013.md).
The inputs and tests are retrospective; the active model is preserved.
Fitted artifacts, vocabulary, row ledgers and datasets remain private.

11 October: [fixed-setting retraining and ensemble comparison](../docs/ensemble-comparison-20261011.md)
adds a separate reproduction of the four standalone models, all eleven equal-weight
voting combinations and two OOF stacking experiments. See the
[frozen additional-experiment protocol](../docs/ensemble-comparison-protocol-20261011.md).
The October 5 dataset, partitions, baseline settings, thresholds and original
artifacts are preserved; no hyperparameter or threshold search is repeated.
`smishguard.ensemble_compare` separates audit, training, validation selection and
final evaluation. This comparison is retrospective because the existing test
partition was already exposed. Private fitted artifacts and membership remain in
`research/data/ensemble-20261011/`; the report includes reproduction commands.

6 October current work: scope is **all SMS phishing**, a team clarification without assumed adviser approval. Revised thesis title: **Pending finalization**; the existing title remains historical and title-dependent edits remain pending. See [scope record](../docs/scope-clarification-20261006.md), [review completion](../docs/review-completion-20261006.md), and [INT8 experiment](../docs/mbert-int8-experiment-20261006.md). Earlier milestone instructions below describe historical workflows; do not use financial-only import gates for current annotation or retrain the four frozen evaluation models.

1 October: [lr-calibrated-4 review](../docs/lr-calibrated-4-review.md). `smishguard.folded_candidate` converts the privately supplied folded LR parameters unchanged, checks the matching guide and publishes aggregates only. It never executes training or opens the private data ZIP. Supplied trainers that apply unconfirmed AI proposals were not enabled. Existing reviewed-data/exposure gates remain; exported calibration is fitted, not independently validated.

Complete-package audit: [findings](../docs/mark-complete-findings.md). `smishguard.complete_handoff` audits the privately extracted package and creates a private schema-v3 LR conversion/parity set without fitting a model or installing an APK asset. The supplied 2,521-record corpus remains exposed and awaiting source/redaction/label reviews. `fair_compare prepare` now also requires `--exposure-review` using `templates/comparison-exposure-review.csv`; complete actual evidence references, never invent them. See the versioned [comparison protocol](../docs/algorithm-comparison-protocol.md).

Dataset-preparation handoff: [team task sheet](../docs/dataset-team-task-sheet.md), [1,200-rule source trace](../docs/sample-size-provenance.md), and [current private-review workflow](../docs/team-review-workflow.md). Existing anonymous IDs/review packets are reused; no source permissions, independent labels or redaction attestations are inferred.

29 September: [pre-training comparison protocol](../docs/algorithm-comparison-protocol.md) and [data-review prerequisites/commands](../docs/comparison-data-review.md) prepare a common LR/NB/linear-SVM comparison. The team confirmed pending data; no new research models or winner were produced. Use `smishguard.fair_compare` for the planned comparison of all three frozen candidates, rather than the older single-selected-candidate workflow below.

25 September: [candidate review](candidate_review/README.md) adds two supplied aggregate tables and private-input-free arithmetic checks. `lr-calibrated-2` is under review, not deployed. Its retrospective results do not establish the shipped model's performance. Existing training/intake gates remain in force; the supplied demo and new trainers were reviewed without execution and not integrated.

Completion update: run `research\.venv\Scripts\python.exe scripts/verify_research.py` for the currently permitted fixture-only workflow. See [reproducibility guide](../docs/reproducibility-guide.md), [annotation response protocol](../docs/annotation-protocol.md) and [data card](../docs/data-card.md). The group split policy is now versioned with stratified group folds where support permits; preserve old manifests. Evaluation adds accuracy/specificity, fixed-prediction cluster bootstrap, anonymous errors and artifact metadata. No real research metrics have been generated.

As of 21 September 2026, a supplied dataset and full-dataset LR export have been inspected. They replace the previous missing-package assumption, **not** automatic research eligibility. Project/client authorization is recorded as reported authorized in [the authorization record](../docs/project-authorization.md); development does not wait for repeat approval. Dataset use, labels/redaction and model evaluation have separate checks. Read [dataset audit](../docs/dataset-audit.md), [labeling guide](LABELING_GUIDE.md), and [model contract](../docs/model-contract.md). No accuracy, calibration quality, ethics approval or thesis winner is established by software parity.

## Prepared data files

- `intake-template.csv`: ready-to-fill UTF-8 header-only input, no invented examples.
- `dataset-schema.csv`: header-only generated approved-output schema; use the importer to derive binary labels.
- `research/data/package-audit/original/`: locally preserved ZIP and extracted bytes, ignored by Git and source packaging.
- `research/data/package-audit/derived/`: private UCI supplementary copy, unverified non-UCI copy and ID-only review ledger. These are **not approved training inputs**.

Unknown columns, malformed CSV, duplicate IDs, unsupported labels/source types, possible residual URL/email/long identifiers, invalid timestamps and inconsistent URL facts are rejected. Unverified, pending, uncertain, other-scam and nonfinancial rows are held with reasons. Human review remains necessary; regex checks cannot establish privacy or truth. Aggregator, public-archive, social-post and external-collection origins are accepted for individual assessment. Source names alone neither approve nor reject records. Document intended permitted use and study role; preserve UCI as supplementary under the proposal. See [exact source-specific evidence needs](../docs/source-evidence.md).

## Setup and software checks

Run from repository root with JDK 17 and Python 3.12. The pinned conversion tokenizer uses Python Unicode 15.0.0.

```powershell
python -m venv research\.venv
research\.venv\Scripts\python.exe -m pip install -r research\requirements.txt
$env:PYTHONPATH='research'
research\.venv\Scripts\python.exe -m unittest discover -s research\tests -v
```

Synthetic fixtures remain under tests/androidTest only. `python -m smishguard.software_fixtures` exercises the existing unigram exporter without research claims. The supplied real model is **not** synthetic; it is unverified and experimental.

## Reproduce package audit and unchanged-weight conversion

```powershell
$package = 'C:\Users\Jassim Trinidad\Downloads\smishguard_model_package-20260920T144757Z-1-001.zip'
research\.venv\Scripts\python.exe -m smishguard.audit_package $package
research\.venv\Scripts\python.exe -m smishguard.convert_supplied research\data\package-audit\original\model_export_final.json research\data\package-audit\original\MODEL_INTEGRATION.md
.\scripts\build.ps1 -Variant development -EmulatorTests
research\.venv\Scripts\python.exe scripts\package.py --variant development
```

Conversion checks the five rounded references (absolute tolerance 0.00005), computes safe full-precision probes, preserves every coefficient/IDF/intercept, freezes Unicode tables and writes the model only into `src/development/assets/`. The baseline debug build stays model-free. No dataset or original guide is copied into APK assets. Conversion never retrains, marks calibration evaluated, enables warnings or configures reporting.

## Import genuinely reviewed primary data

Project authorization is already recorded. This import operation checks data-specific permitted use, redaction, resolved labels and the selected study role. It does not require another client go-ahead or treat the letter as data licensing. No supplied-package row is automatically relabeled or cleared.

```powershell
$reviewReference = Read-Host 'Controlled record of this dataset intake review'
research\.venv\Scripts\python.exe -m smishguard.import_data research\data\reviewed-intake.csv research\data\approved-v1 --review-reference $reviewReference --study-role primary
```

Output directory must be new. The new template adds `permitted_use_status` (`pending`, `documented`, `not_permitted`), `permitted_use_reference` (opaque reference to the actual evidence), and `study_role` (`primary`, `supplementary`, `undecided`). Existing intake files must add these truthfully; do not infer them from the client letter. Donation records additionally need verified donation consent; other origins use their documented permitted-use basis. A `documented` declaration must cover the selected research activity, not necessarily redistribution. The legacy output column `approval_reference` and CLI alias store the intake review reference, not ethics clearance.

For separately reviewed supplementary financial-binary records, use `--study-role supplementary` and a separate output directory. Primary training refuses those rows. General nonfinancial UCI messages remain in their private supplementary collection for a separately specified evaluation task; never invent financial labels to force them through the primary schema. Review `import-report.json`: eligibility/exclusions and agreement use original independent labels. Do not replace missing dates with collection dates. Training requires >=1,200 eligible records and both classes in all four partitions; report unique texts and independent template groups alongside row counts. The current supplied package is not certified to meet that minimum. A below-minimum alternative needs the separately finalized small-sample protocol, not a lowered CLI guard.

## Baselines, frozen selection, untouched final partition

```powershell
$dataset = 'research\data\approved-v1\approved.csv'
$experiment = 'research\runs\baseline-group-v1'
research\.venv\Scripts\python.exe -m smishguard.compare $dataset $experiment --split group --data-history previously_used
$selectedName = (Get-Content (Join-Path $experiment 'selection.json') -Raw | ConvertFrom-Json).selected_run
$selectedRun = Join-Path $experiment $selectedName
research\.venv\Scripts\python.exe -m smishguard.evaluate $dataset $selectedRun --selection (Join-Path $experiment 'selection.json')
```

LR, Multinomial NB and linear SVM are fitted **from scratch**, using identical deterministic splits. Only training text fits vocabulary, IDF and classifier. A separate calibration partition fits a sigmoid; validation chooses the threshold (maximum F1 over 0.05..0.95, ties higher), then compares candidates by validation trapezoidal PR-AUC (ties LR, NB, SVM). The selection hashes the frozen artifact/manifest/config/export. Final evaluation rejects changed data/selected files and refuses to overwrite its final report. It transforms final text only after selection. Do not defeat this boundary by copying runs, deleting reports or selecting after looking at final results.

The supplied export was fitted on all supplied rows. Never score it on those same rows and call that held-out performance. `--data-history previously_used` explicitly labels any new partition as retrospective; it cannot undo earlier use of the data. `prospectively_reserved` is only for genuinely reserved new data under the team's documented protocol, not a way to rename these supplied rows. Preserve a future independent collection for confirmation.

| Split | Interpretation |
|---|---|
| `group` | Label-blind normalized exact/near-copy components and manual groups kept disjoint across train/validation/calibration/test. Grouping uses the full corpus solely to prevent overlap, not to learn features. |
| `random` | Deliberately permissive stratified comparison; duplicates/templates may cross partitions. Never present as leakage-controlled. |
| `time` | Chronological-only comparison; templates may still overlap. Requires genuine receipt timestamps with timezone. |
| `time-group` | Chronological boundaries with every component spanning partitions purged entirely; excluded IDs are recorded. Both classes must survive in each partition. |

All six pairwise group-overlap counts are recorded. Group splits target 55/15/15/15%; unequal group sizes change counts. Same-time rows stay together. Nonviable partitions fail; do not search seeds for favorable scores. The supplied `date_collected` has unresolved meaning and is date-only, so chronology is **not available** for it.

For the deliberately permissive comparison use a fresh directory:

```powershell
research\.venv\Scripts\python.exe -m smishguard.compare $dataset research\runs\baseline-random-v1 --split random --data-history previously_used
# Evaluate its frozen candidate only as a declared comparison, with --allow-permissive-comparison.
```

Freeze the experiment matrix before opening any final partition. Use the same seed/data/split for each condition. `compare --condition text-only|text-url|placeholders|shape|punctuation` preserves URL ablation and shortcut checks; `--analyzer char` adds character n-grams. `text-url` requires measured coarse facts, never guessed zeros or full retained URLs. `source`, notes, institution claims, attack type, IDs, timestamps and annotation fields are never model inputs. Main word baselines currently use versioned ASCII-normalized unigrams; character baselines use 3–5 grams. These are declared research baselines, not a claim to reproduce the missing original bigram training/CV code.

Final reports include precision, recall, F1, trapezoidal PR-AUC, average precision, ROC-AUC, FPR/FNR, confusion counts, Brier/log loss/ECE/reliability bins and explicitly hypothetical base-rate sensitivity. English/Taglish/Filipino support is reported separately; subgroup metrics require >=20 records and >=5 of each class, otherwise only support and an insufficient-data explanation are emitted. This reporting floor is not statistical power assurance. Phone latency/memory remain unmeasured.

## Export and Python-to-Android parity for a newly trained candidate

The `deployment` word-unigram training command automatically exports frozen `model.json` through the shared validated exporter. Other conditions/analyzers remain research-only. Do not overwrite the supplied development model with an incompatible export.

```powershell
research\.venv\Scripts\python.exe -m smishguard.export_parity $selectedRun
$parityDir = (Resolve-Path (Join-Path $selectedRun 'parity')).Path
$env:JAVA_TOOL_OPTIONS='-Djdk.net.unixdomain.tmpdir=C:/sg-nonexistent-socket-dir'
.\gradlew.bat :app:testDebugUnitTest "-PmodelParityDir=$parityDir" --console=plain
.\scripts\build.ps1 -Variant development
```

Export parity uses safe synthetic probe texts against real fitted parameters. Neither a passed test nor a fitted sigmoid establishes calibration quality, threshold approval, model licensing or permission to issue warnings. This milestone's development model policy always disables automatic warnings and reporting.

## Pending research

No original CV scripts, fold manifests, seeds, CI/bootstrap method, model-comparison records or calibration evidence were supplied. The guide's accuracy/F1/CI and realistic-traffic assertions cannot be reproduced or adopted as results. Source-held-out and prospective confirmation require additional protocol/data. XLM-RoBERTa/RoBERTa-Tagalog comparison scaffolding remains present but unexecuted without vetted licensed checkpoints/dependencies and eligible data; calamanCy/mobile transformer export remain pending. No model winner is claimed.

## Source tracing and private blinded review packets

The official-host investigation and exact/whitespace-only matches are recorded in [source-evidence.md](../docs/source-evidence.md); source versions and member hashes are pinned in `source_matching.py`. No source URL is taken from an SMS. Published license labels are separate from acquisition-chain confirmation, privacy review and target-task labels.

Private packets for all 1,276 supplied rows already exist locally at `research/data/review-v1/`. The coordinator mapping includes source/original labels and must never reach annotators or Git. `redaction-review.csv` contains anonymous IDs and original text for a restricted human reviewer; reviewed text and reviewer fields start blank. The two shuffled pending annotator sheets contain IDs only and are not ready for labeling. No labels, dates or redaction sign-offs were generated.

```powershell
$env:PYTHONPATH='research'
# On a fresh checkout/private package, use a NEW output directory:
research\.venv\Scripts\python.exe -m smishguard.review_packets prepare research\data\package-audit\original\smishguard_dataset.csv research\data\review-v1
# Downloads only three explicitly pinned official Kaggle datasets; fails on changed member hashes:
research\.venv\Scripts\python.exe -m smishguard.source_matching research\data\review-v1 --download
# AFTER a human completes redaction-review.csv; only verified rows are released:
research\.venv\Scripts\python.exe -m smishguard.review_packets release research\data\review-v1 research\data\review-v1-released
```

Give annotator A only `annotator-a.csv`, annotator B only `annotator-b.csv`, and each the labeling guide. Do not share coordinator mappings, old labels, model outputs, source notes or the other's answers. Each independently records category, language and financial scope. Keep uncertainty; use the existing intake/adjudication workflow to combine both responses without replacing their original labels. Formula-like cells in the redaction display are escaped, and release rejects unsafe prefixes/residual URL/email/long-identifier patterns. Human review is still essential.

Safe header-only files under `research/templates/` can be shared publicly. All populated packets/source downloads stay ignored. See [repository sharing](../docs/repository-sharing.md): the public checkout omits the supplied model asset and generated APKs, while the existing local offline build remains unchanged.

No new real-data comparison has run: the exact dependency is a completed permitted-use/study-role review and independently labeled, redaction-verified primary intake with the required post-filter sample support. UCI remains supplementary; unknown dates do not block group-based evaluation. Once reviewed inputs exist, use the comparison/selection/final-evaluation commands above. Do not substitute the auto-derived package labels just to make the command run.

## Supplied procedure evidence

model_evidence/ contains sanitized scripts, aggregate tables, hyperparameters and reviewed documentation. Do not run its dataset-dependent scripts in this handoff. CSV arithmetic and static checks are distinct from reproducing experiments. See model_evidence/MODEL_EVALUATION.md for conflicting summary values, pre-vectorized inner CV, overlapping selection/test splits and missing threshold-procedure artifacts.
