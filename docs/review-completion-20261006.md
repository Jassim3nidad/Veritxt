# Review completion and frozen evaluation

Revised thesis title: **Pending finalization**. Scope: **all SMS phishing**, a team clarification without assumed adviser approval. Original title and historical results remain preserved. No completed reviewer returns, fresh messages or physical-phone results were available in this implementation pass.

Use the existing private packets, not duplicate manually constructed sheets. Returns must retain every assigned ID and exact displayed text; blank decisions remain missing. The agreement command now snapshots both original returns, mapping, source identity, privacy release and attestations with hashes. It rejects changed packets, reused reviewer identities, invalid timestamps and altered adjudication evidence. Partial agreement is descriptive only; versioned label application requires complete responses and explicit final decisions, signed distinct reviewer attestations and a third adjudicator. `uncertain`, `out_of_scope` and unresolved privacy are retained in the exclusion ledger.

Before agreement, complete `coordinator/attestations.csv` using `yes` for a truthful independence declaration and an actual UTC signature time. Complete `coordinator/privacy-release.csv` using `verified` only after actual human review. Other statuses remain holds. The guide changed to all SMS phishing: record which version each reviewer used; conflicting definitions require new matched packets/review, not silent reinterpretation. Preserve old files. No software declaration proves human independence or source permission.

```powershell
$env:PYTHONPATH='research'
$py='research/.venv/Scripts/python.exe'
$review='research/data/validation-20261006/review'
$agreement="$review/coordinator/agreement-v1"
& $py -m smishguard.validation_stage agreement "$review/returns/a.csv" "$review/returns/b.csv" $agreement --review $review
# After a real third adjudicator completes the generated CSV:
& $py -m smishguard.validation_stage adjudicate "$agreement/adjudication.csv" "$agreement/final-summary.json"
& $py -m smishguard.review_completion apply research/data/expanded-20261005/experiment-v1/case-view.json "$agreement/adjudication.csv" research/data/validation-20261006/reviewed-v1
```

The output contains the parent bytes, new labels, historical labels where present, original A/B decisions/rationales, hashed evidence and an exclusion ledger. It refuses an existing destination. This historical cohort stays retrospective; applying reviewed labels cannot make it fresh. Changed return evidence requires a new agreement version.

For genuinely new data, run the existing `history` and `intake` commands from the prospective plan. Screening now recognizes case/whitespace header variations, `body`/`v2` aliases and archived headerless `SMSSpamCollection` data. Near-copy comparison uses the maximum of both SequenceMatcher directions because its ratio can depend on argument order. Index all available history before intake, including old held/excluded views; never index the current batch into its own history. A no-match still needs human semantic/evidence review. Empty normalized text is held.

Complete a private CSV using the header-only [semantic review template](../research/templates/semantic-review.csv). Every screened ID needs an explicit `admit` or `hold`, actual reviewer/time/reason, language/source and template group. Admission requires `semantic_overlap=no`, `evidence_verified=yes`, a clear automatic screen and the frozen collection window (200 groups or 30 days). Holds cannot be overridden merely by writing `admit`. Resolve an input issue in a new screened version, retaining the earlier ledger. Keep the chronologically first eligible member per group; collect no predictions during labeling.

```powershell
$stage='research/data/validation-20261006'
$freeze="$stage/prospective-freeze.json"
& $py -m smishguard.review_completion admit "$stage/prospective/intake.csv" "$stage/prospective/screen-v2" "$stage/prospective/semantic-review.csv" $freeze "$stage/prospective/admitted-v1"
& $py -m smishguard.validation_stage prepare --source "$stage/prospective/admitted-v1/dataset.json" --review "$stage/prospective/review-v1"
# Repeat genuine independent returns/agreement/adjudication with --review pointing to this new packet.
& $py -m smishguard.review_completion apply "$stage/prospective/admitted-v1/dataset.json" "$stage/prospective/agreement-v1/adjudication.csv" "$stage/prospective/reviewed-v1"
# Uses the existing isolated mBERT dependencies and all four original assets:
# A separate evaluation-runtime-lock.json is prepared alongside the original freeze.
# It hashes the new evaluator and dependencies without changing the model freeze/time.
& research/data/mbert-20261002/venv/Scripts/python.exe -m smishguard.review_completion evaluate "$stage/prospective/reviewed-v1" $freeze "$stage/prospective/evaluation-v1"
```

Evaluation saves paired predictions privately plus JSON, CSV and Markdown comparison tables. It uses the existing exported linear scorers and float32 ONNX mBERT, with unchanged calibration and thresholds. A cohort-level exclusive marker prevents reopening the same version via another output directory; failures retain the marker and require investigation, not deletion to tune/retry. Metrics include phishing precision/recall/F1, macro-F1, accuracy, confusion/FPR, Brier/log loss, source/language support, scored-only coverage and abstentions-as-failures accuracy. Adequate support adds group-bootstrap intervals and paired F1 differences; low support is explicitly descriptive. Do not publish message-level evidence.

All populated inputs, indexes, experiment files and APKs stay in ignored private storage. Synthetic end-to-end tests exercise screening → admission → packets → returns → agreement → adjudication → dataset version → four-column comparison and reject changes to frozen evidence. Fixture reviewers and messages are fictional and are never research results.

For a new private setup, create the additional runtime lock before any predictions with `research/data/mbert-20261002/venv/Scripts/python.exe -m smishguard.review_completion lock-runtime <original-freeze.json> <same-directory>/evaluation-runtime-lock.json`. It already exists in this handoff. The lock records scorer/source hashes and installed inference-library versions; a mismatch blocks evaluation. Do not overwrite it or regenerate it to conceal a change after testing. Consolidate the entire collection into the screened intake ledger before admission so the group cap and collection cutoff apply to the whole cohort.
