# Prospective intake and frozen evaluation plan

This stage prepares a new collection. **No prospective records or labels have been received and no prospective model performance has been measured.** The retrospective 3,340-record cohort, older datasets, review packets and fictional demonstrations are not fresh data.

`research/data/validation-20261006/prospective-freeze.json` records the exact UTC freeze instant and file hashes for the current four fitted asset bundles, training freezes, tokenizer, inference code and preprocessing. Thresholds remain LR 0.82, NB 0.63, SVM 0.59 and mBERT approximately 0.89 (the exact serialized value is authoritative), with greater-or-equal comparison. Calibration remains exactly once. The separately rebuilt mBERT package may change its APK hash only while its fitted assets remain byte-identical and parity passes. No retraining, recalibration, threshold search, checkpoint selection or model substitution is part of this evaluation.

Collection protocol, fixed before intake:

- Start after the UTC freeze instant. Record actual receipt time and collection time separately, with a private receipt-evidence reference and source-use basis. Collect consecutively within the participating team's defined recruitment channel; document that channel and any coverage limitations before recruitment. Do not choose messages based on predicted class, score, difficulty or expected model performance.
- Close at the first 200 coordinator-approved distinct template groups or 30 calendar days after the freeze, whichever comes first. Preserve all screened intake rows and their reasons, including excluded cases. Do not extend collection after seeing model scores. Record nonparticipation and uncollected messages where feasible; convenience recruitment is not a population sample.
- Use the blank intake template. Do not collect unnecessary sender identities or raw private screenshots in the working sheet. Keep any authorized receipt evidence separately under controlled access. Source permission, consent/use basis and human privacy checks are required for each admitted record; template fields do not certify them.
- Screen exact original-view hashes, normalized exact matches and SequenceMatcher similarity >=0.85 against the local historical index, and check duplicates within the new intake. The index scans all available historical CSV/TSV/JSON/XLSX tables, nested data archives and source snapshots under research storage. Its inventory distinguishes message-bearing files from metadata. Refresh into a new index directory if additional prior corpora become available; retain both inventories. Unavailable or deleted data remain a limitation. The broad historical views deliberately include held/excluded messages and previous review text to detect exposure, without admitting them to training.
- Any historical match is held from the prospective cohort. A coordinator reviews no-match cases for semantic template overlap, verifies receipt/source evidence, and assigns connected template groups. Keep one chronological first eligible member per group for the primary prospective cohort; keep later related records in the screened ledger. No-match alone does not prove independence, and normalization can flag unrelated messages. Record conservative holds and reasons rather than silently admitting matches.
- Create new blinded A/B packets for the admitted new cohort, using the same empty-field schema and labeling guide. Complete independent review, pre-adjudication agreement and adjudication before predictions. Freeze membership, text, groups, labels, intake ledger, cutoff and exclusion reasons by file hash. Do not expose scores to labelers or the adjudicator.
- Evaluate the four frozen pipelines once on identical admitted IDs. Save paired predictions privately. Report phishing precision/recall/F1, macro-F1, accuracy, confusion counts/FPR, Brier/log loss and group-bootstrap intervals, plus paired differences. Keep source/language support visible. If either class has fewer than 20 examples or fewer than 10 groups, label the result descriptive with insufficient confirmatory support; do not tune, rebalance or extend this test to obtain a desired result.
- Separate classifier metrics from app abstention. Report coverage, scored-only performance and a sensitivity analysis counting abstentions as failures; never credit an abstention as a genuine-message success. Physical-phone engineering checks use fictional messages and cannot substitute for prospective accuracy.

The intake checker never runs predictions. Its outputs are **holds** or **candidates pending human semantic/evidence review**, not automatic approval. Preserve mismatches and all versions. Any later model change requires a new model version and a separate future evaluation cohort.

```powershell
$env:PYTHONPATH='research'
research/.venv/Scripts/python.exe -m smishguard.validation_stage verify-freeze `
  research/data/validation-20261006/prospective-freeze.json
research/.venv/Scripts/python.exe -m smishguard.validation_stage history `
  research/data research/data/validation-20261006/history
research/.venv/Scripts/python.exe -m smishguard.validation_stage intake `
  research/data/validation-20261006/prospective/intake.csv `
  research/data/validation-20261006/history `
  research/data/validation-20261006/prospective-freeze.json `
  research/data/validation-20261006/prospective/screen-v1
```

Each output directory is new and existing evidence is never overwritten. The historical snapshot must precede the candidate batch: do not add that batch to the history before screening it. For subsequent batches, add earlier closed intake batches to history and explicitly retain the inventory cutoff. Candidate text and ID-level overlap results remain private.

Current scope: **all SMS phishing**, clarified by the team without assumed adviser approval. Revised thesis title: **Pending finalization**. [Admission and evaluation commands](review-completion-20261006.md) now connect screened intake, semantic review, independent labels and comparison tables. The separate INT8 experiment is excluded from this four-model freeze. Near-copy screening conservatively uses both SequenceMatcher directions; index coverage includes known header aliases and archived headerless UCI records.
