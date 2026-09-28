# Dataset preparation tasks for the team

**Current training-ready count: zero established.** All 1,276 preserved records still lack completed redaction reviews and independent A/B judgments. This does not mean all records are unusable. The client/project go-ahead remains recorded; it is not being requested again. The working historical LR APK and minimalist UI are unchanged. No models were trained here.

| Owner | Private working file/location | Completion criterion |
|---|---|---|
| Mark, with coordinator | `research/data/preparation-20260929/audit/origin-review.csv`; `controls/training-history.csv` in the same preparation folder | Identify actual download/page/version and file hashes, acquisition/merge/transformation code, per-record source lineage and intended-use evidence. Resolve ambiguous content matches; do not infer acquisition or permissions from a match. Provide the exact records used for each historical/candidate model, preprocessing, versions, seeds, split/group manifests and data used for tuning/calibration/testing. State unknowns explicitly. Account for the supplementary 1,050 rows and previously exposed 34 probes. |
| Human redaction/access reviewers | Existing `research/data/review-v1/redaction-review.csv`; new `audit/coordinator-check-queue.csv` and `audit/origin-review.csv` | Review every retained message, not only regex hits. Supply safe redacted text, verified/excluded/pending status, actual reviewer reference, and documented annotator-access evidence. Review names, OTPs/PINs, account/contact details, links and obfuscation. There are 285 potential-identifier candidates under the expanded checks, not 285 confirmed privacy violations. |
| Annotator A and annotator B, independently | After permitted release: `research/data/review-release-v1/annotator-a.csv` and `annotator-b.csv`; return separate copies to `research/data/review-responses-v1/` | Complete category, language and financial scope for every assigned row; use uncertain where needed. Do not change IDs/text. Do not see old labels, model predictions, source ledger, coordinator flags or each other's answers. Preserve originals and record independence evidence in `controls/independence-review.csv`. |
| Adjudicator distinct from A/B | Generated only after complete responses: `research/data/adjudication-v1/adjudication.csv` | Resolve category/language/scope disagreements and uncertainty with final values, reviewer ID and rationale; retain original A/B answers. Unresolved final cases stay out of training. Coordinator separately reviews 22 records in two inherited mixed-label template groups after independent judgments freeze; do not force consistent labels solely for modeling convenience. |
| Coordinator and methodology owner/adviser | `controls/methodology-decision.csv`, `controls/unseen-reservation.csv`, `controls/split-assignments.json`; then `research/data/reviewed-intake.csv` | Record the controlling methodology version/evidence, legitimate-negative scope, total/class/group support and applicable fallback. Merge only supported review facts into intake, validate it, and record actual eligible counts. Reserve genuinely new test records and a common group-isolated assignment before training/selection. |

Detailed commands and field rules: [private review workflow](team-review-workflow.md). The existing ID-only A/B pending sheets must not be annotated. The release command currently rejects the incomplete real packet; no unreviewed text was distributed. Mark's coordinator-only mapping is `research/data/review-v1/coordinator/mapping.json`; send each annotator only their own released sheet and the labeling guide, never the whole private directory.

## What exclusion can and cannot accomplish

These are set-union counts from actual records, not subtraction estimates. Remaining rows are **candidates**, still requiring the same review gates. No exclusion is applied to the preserved original corpus.

| Optional disposition for the primary experiment | Rows withheld/excluded | Remaining candidates | Established eligible now |
|---|---:|---:|---:|
| Keep UCI supplementary | 70 | 1,206 | 0 |
| Also exclude the explicit nonfinancial traffic-fine case | 71 | 1,205 | 0 |
| Also hold all 10 personal and 3 social-source rows pending their evidence | 83 | 1,193 | 0 |
| Also hold the two inherited mixed-label template groups pending resolution | 105 | 1,171 | 0 |
| Exclude every row still missing required human reviews | 1,276 | 0 | 0 |

One nonfinancial case is already in the personal/social set, so 71 + 13 is not the exclusion union. Pending permissions or consent, unrepaired identifiers, unresolved labels/scope and source-ambiguous records may be held/excluded with recorded reasons; do not replace them with assumed legitimate labels. Duplicate rows must share groups and be handled under a documented deduplication policy; dropping duplicates does not create independent evidence. The 1,050 supplementary ham rows cannot be used to make the primary total meet a target merely because they are available.

## Reserve new unseen messages

Use a separate controlled collection channel under the methodology's actual collection/consent arrangements; do not extract users' app scans or change the app. Record existing collection/ethics evidence where the manuscript requires it, without treating client authorization as a substitute. Capture donation/use evidence and source lineage privately; record true receipt date/timezone only when known. Keep collection time separate. Aim for legitimate financial hard negatives as well as financial-phishing positives and the intended languages; no final quotas are invented here.

A custodian keeps the new cohort away from model development and score inspection. Obtain blinded independent labels, check exact/normalized/template and source overlap against all development, supplementary and exposed-probe records, and keep whole related groups together. Overlap must be resolved before a record is called unseen. Record reservation time, prior-use evidence and every opening of the cohort; do not backdate any field. The 34 handoff probes have already been exposed and cannot serve as a new sealed test set.

Freeze a private manifest assigning every eligible ID exactly once to train/validation/calibration/test. All three algorithms must use the same manifest. The prepared trainer requires `--assignments` for `--history prospectively_reserved`, validates complete IDs/class support and rejects crossing template groups. The evidence reference must point to the real reservation ledger; a filename alone does not prove unseen status. Fit vocabulary within training folds, tune using development partitions only, and open the final test once after all candidates/thresholds are frozen.

## Sample-size decision

The 1,200 figure comes from supplied Chapter 1 and a related proposal feasibility table. Formal approval/applicability of the version and the code's financial-only interpretation are not established. It is **not a universal statistical requirement**. The proposal includes other legitimate messages in its total and describes a smaller-sample fallback. See [the source trace](sample-size-provenance.md). The guard remains unchanged until the controlling scope/design is recorded; labels, rights and leakage controls are required under either design.
