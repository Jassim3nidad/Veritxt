# Data and model review needed before the comparison can run

29 September 2026: the team confirmed use of the documented pending-data status. No new research training, hyperparameter search, calibration fitting or final-test comparison was run. Software fixture tests are not research evidence.

The 1,276 supplied records are not an eligible primary corpus simply because their total exceeds 1,200. See [data card](data-card.md), [source evidence](source-evidence.md) and [annotation protocol](annotation-protocol.md). The following work remains:

The 1,200 figure is a sourced methodology feasibility target with an unresolved implementation interpretation, not a universal statistical requirement or verified approval of the current sample design. See [the source trace](sample-size-provenance.md) and [current preparation/task sheet](dataset-team-task-sheet.md).

1. Complete source-specific permitted-use records, origin/version and study-role decisions. Review the 70 UCI-labeled records as supplementary only. Establish donation consent/use for the 10 personal rows and controlled origin/reuse evidence for the three social-source rows; otherwise exclude them. The explicit nonfinancial record is outside the primary task. Do not infer labels, rights or consent from source names.
2. Complete independent annotator A/B packets, verified redaction and financial-scope review. Resolve disagreements through the documented adjudicator; preserve original labels and pre-adjudication agreement. Uncertain, unreviewed and out-of-scope records never become legitimate negatives by default. Keep populated packets and consent evidence private.
3. Import through the existing intake validator, producing approved.csv and import-report.json. Review exclusions and confirm at least 1,200 eligible primary records, both classes and enough independent template groups for every outer/inner partition. If support fails, collect more eligible examples or approve a separate small-sample protocol before training; do not silently lower the threshold.
4. Review duplicate/template groups, cross-source overlap and label conflicts. Confirm the freeze and prior-use ledger. The old full-data LR has already seen supplied corpus rows; reshuffling them does not create genuinely unseen data. Reserve an independently labeled future test cohort, verify it does not overlap development groups, and record who had access before model selection. Dates of collection are not automatically receipt dates.
5. Name data custodians, controlled access, retention/deletion policy and review references. Review learned vocabulary for identifiers and sensitive content before creating each model-bearing APK. Independent calibration evidence and physical-phone testing remain separate tasks; no automatic-warning or reporting approval is implied.

Once these inputs exist, the prepared commands below use private outputs. Do not run them on the pending corpus:

```powershell
$env:PYTHONPATH='research'
research\.venv\Scripts\python.exe -m smishguard.fair_compare prepare research/data/REVIEWED/approved.csv research/runs/comparison-v1 --history previously_used --exclusion-report research/data/REVIEWED/import-report.json --exposure-review research/data/REVIEWED/comparison-exposure-review.csv
# Review the freeze, all three candidates, and the recorded prior-use scope first.
research\.venv\Scripts\python.exe -m smishguard.fair_compare evaluate research/data/REVIEWED/approved.csv research/runs/comparison-v1
```

Use `prospectively_reserved` only when a documented reservation actually predates training/selection. It now requires `--assignments` with a reviewed complete partition manifest and reservation evidence reference; see the blank `research/templates/split-assignments.json`. Import the eligible development and reserved cohorts under one schema, assign the reserved IDs to test, and ensure no template component crosses partitions. A random reshuffle is not accepted as prospective evidence. Software checks assignment integrity, not the truth of the human prior-use declaration. The evaluator seals all candidates and refuses repeat evaluation, including after an interrupted opening. Never delete the marker to retune. Dataset/vocabulary/pickles/splits remain private. Review only the aggregate comparison for public sharing.

The new fair-comparison command supersedes the older default-hyperparameter, single-selected-model command for this thesis comparison. It has fixture-level checks, but a full end-to-end approved-data run remains pending. A reference parity export can be prepared afterward with `python -m smishguard.export_parity research/runs/comparison-v1/lr` (and nb/svm). Validate app abstention coverage separately before equating full-coverage classifier metrics with deployed app performance.

## Installing a future reviewed model

For each of lr/nb/svm, privately place its own portable `model.json` under `android/app/src/<algorithm>/assets/` with `review.properties` containing algorithm, modelVersion, manualReview=accepted-experimental and sha256. These values document an actual manual review, not an approval obtained by filling in a file. The asset must identify the same algorithm, be nonsynthetic and have a fitted sigmoid with calibration_evaluated=false. The build verifies identity/hash; runtime also validates schema and numeric arrays. Preserve training provenance and review evidence in the private run folder.

Build with `scripts/build.ps1 -Variant lr` (or nb/svm), run parity and emulator checks against that exact artifact, inspect APK membership and permissions, then distribute privately. Missing models, wrong algorithms or changed bytes fail the build. NB/SVM have faithful implementations; their current blocker is eligible data and reviewed artifacts, not Android support. The historical schema-v2 LR is a pinned exception with its exact pre-existing digest and must never be presented as the new shared-data baseline.
