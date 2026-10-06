# Private team review workflow

Historical workflow retained for earlier datasets. Current scope is **all SMS phishing**; revised thesis title: **Pending finalization**. Use the [current labeling guide](sms-labeling-guide-20261006.md) and its linked versioned review workflow for new work. Financial-only categories below are historical and must not exclude current phishing by sector. No adviser approval is inferred.

Use the existing anonymous IDs and packets; do not generate a second mapping. This work does not request project/client authorization again. Populated files, response hashes, row IDs and source evidence stay under ignored `research/data/`. Only blank templates and aggregate documentation belong in public Git. No new model is trained by these commands.

## Coordinator and redaction reviewer

1. Mark and the coordinator complete `research/data/preparation-20260929/audit/origin-review.csv`. `candidate_sources` is a content-match hint, not proof of the download chain. Record confirmed lineage, intended primary/supplementary role, use evidence and prior training/testing exposure truthfully. Use opaque references to restricted evidence, not donor names or private URLs. `annotation_access_status=documented` needs an actual evidence reference and reviewer token; it is a separate determination from training eligibility.
2. A human redaction reviewer edits the existing `research/data/review-v1/redaction-review.csv`. Fill reviewed text, `redaction_status=verified` and reviewer ID only after checking names, contacts, account/card identifiers, OTP/PIN values, private URLs and obfuscation. Use the same placeholders across classes. Keep uncertain rows pending; mark excluded with a nonidentifying reason where appropriate. The new coordinator check queue prioritizes candidates but does not verify or automatically redact them. All original files/mapping retain their IDs; save controlled revision copies before changes.
3. Release only the intersection of documented annotation access and verified redaction:

```powershell
$env:PYTHONPATH='research'
research\.venv\Scripts\python.exe -m smishguard.team_review release research/data/review-v1 research/data/preparation-20260929/audit/origin-review.csv research/data/review-release-v1
```

This correctly fails today because there are no documented access decisions or verified redactions. No text-bearing A/B file was fabricated. The old ID-only `annotator-a-pending.csv` and `annotator-b-pending.csv` are preparation records, not annotation assignments. Use the team release entry point above; the older low-level release command assumes the caller has already handled access review.

## Annotators A and B

Each receives only their own released `annotator-a.csv` or `annotator-b.csv` and `research/LABELING_GUIDE.md`. Do not send the whole private packet folder. Hide inherited labels, source identities, model outputs, coordinator flags/grouping and the other annotator's answers. Preserve the original blank released files; each annotator works in a separate response copy under `research/data/review-responses-v1/`.

Complete every assigned row's category (`financial_phishing`, `legitimate`, `other_spam_scam`, `uncertain`), language (`en`, `fil`, `taglish`), financial scope (`true`, `false`, `uncertain`) and optional short note. Do not edit ID or reviewed message text. Ask the coordinator to re-redact and version/re-release if text is unsafe or unusable; do not silently repair it in one sheet. Do not guess legitimacy from an inherited source category or suspiciousness from a URL alone. Use unrelated practice messages to clarify the guide before production; shared decisions on evaluation records would undermine independence.

The coordinator records actual opaque A/B IDs, guide version, response hashes and human independence attestations in the private `controls/independence-review.csv`. Distinct filenames or IDs do not establish human independence. Do not invent signatures, dates or evidence references.

## Adjudicator

After both complete response copies are returned, freeze them and calculate pre-adjudication agreement:

```powershell
research\.venv\Scripts\python.exe -m smishguard.team_review adjudicate research/data/review-release-v1 research/data/review-responses-v1/annotator-a.csv research/data/review-responses-v1/annotator-b.csv research/data/adjudication-v1 --annotator-a ACTUAL_OPAQUE_A_ID --annotator-b ACTUAL_OPAQUE_B_ID
```

The command rejects missing responses, changed text (even if both annotators changed it identically), changed release sheets and different cohorts. It copies responses into `frozen-responses/`, records hashes and produces `agreement-before-adjudication.json` and `adjudication.csv`. All final fields remain blank. The adjudicator sees current A/B judgments, not historical source labels or model scores. Category, language, financial-scope disagreements and uncertainty are explicitly flagged; matching rows require confirmation too. Examine the two inherited mixed-label template components separately through the coordinator after independent responses freeze; do not force labels to agree solely to remove a conflict.

For every released record, record final category, final language, final financial scope, an adjudicator ID distinct from A/B and a short rationale. A final uncertain category/scope remains held, not legitimate by default. Keep original A/B answers unchanged.

```powershell
research\.venv\Scripts\python.exe -m smishguard.team_review validate research/data/adjudication-v1 research/data/adjudication-checked-v1
```

This verifies response hashes, cohort, unchanged original answers and complete resolution fields. It writes the legacy-compatible `adjudication-core.csv` and an aggregate resolution summary. It does not certify reviewer independence, source rights or final eligibility.

## Intake and final gate

The coordinator merges reviewed provenance/consent, verified redacted text, original A/B labels, resolved category/language/scope and group decisions into `research/data/reviewed-intake.csv` using the existing `research/intake-template.csv`. Do not copy the old ham/smishing field into either independent-label column. Preserve original responses and final decisions separately. Use `agreed` only for matching certain categories; use `adjudicated` when resolution was needed. Unresolved scope remains blank in intake; it does not become false/true by guesswork. No receipt date is inferred from `date_collected`.

```powershell
research\.venv\Scripts\python.exe -m smishguard.import_data research/data/reviewed-intake.csv research/data/reviewed-import-v1 --review-reference ACTUAL_INTAKE_REVIEW_REFERENCE --study-role primary
```

The importer checks the existing contract, produces the true `eligible_records` count and holds unresolved/out-of-scope rows. Review its exclusion ledger and recompute duplicates/template groups on final redacted text before freezing assignments. Resolve the [sample-design interpretation](sample-size-provenance.md) before invoking training. No outcome of the annotation validator alone opens the training gate.
