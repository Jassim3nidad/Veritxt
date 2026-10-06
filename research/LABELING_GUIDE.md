# Labeling and intake guide

Historical workflow retained for earlier datasets. Current scope is **all SMS phishing**; revised thesis title: **Pending finalization**. Use the [current labeling guide](../docs/sms-labeling-guide-20261006.md) and its linked versioned review workflow for new work. Financial-only categories below are historical and must not exclude current phishing by sector. No adviser approval is inferred.

Use `intake-template.csv` (headers only). Keep the supplied package unchanged. Work in the ignored `research/data/` directory, never in app assets. This guide does not authorize collection or certify any source.

## Four categories

| Independent label | Decision rule |
|---|---|
| `financial_phishing` | Message plausibly impersonates a Philippine bank, e-wallet, government financial office, lender or remittance service to obtain credentials, OTPs, personal documents or money. A link is neither necessary nor sufficient. Label records an annotator judgment, not verified sender identity. |
| `legitimate` | Evidence and context support a legitimate message. Genuine OTP/transaction notices, official marketing and anti-scam advisories can qualify. Suspicious vocabulary, urgency, or a URL alone does not determine the label. Mark financial scope separately. |
| `other_spam_scam` | Spam/scam outside the target financial-institution impersonation task (e.g. unrelated delivery, traffic-fine, job or prize scams). Keep separate, not negative examples silently relabeled as ham. |
| `uncertain` | Insufficient context/evidence, ambiguous financial scope, unclear intent or disagreement not yet resolved. Do not guess. Hold out until adjudication; unresolved cases never enter training. |

## Independent workflow

1. Project/client authorization is already recorded separately. The coordinator reviews each source and intended permitted use. `source_type` may be `participant_donation`, `team_donation`, `institutional_publication`, `aggregator`, `public_archive`, `social_post` or `external_collection`. A platform name neither qualifies nor disqualifies a record. Set `permitted_use_status` to `pending`, `documented` or `not_permitted`; documented use requires an opaque `permitted_use_reference` to evidence. Assign `study_role` as `primary`, `supplementary` or `undecided` under the protocol. Keep UCI supplementary as planned. The client letter is not blanket data licensing or formal ethics clearance.
2. Redact names, personal phone/account/card IDs, OTPs, private URLs and email addresses uniformly across categories. Use `zznamezz`, `zzaccountzz`, `zznumberzz`, `zzemailzz`, `zzurlzz`. Preserve necessary institution names and substantive wording. Review obfuscated identifiers manually. The import regex is only a conservative blocker, not a PII detector or automatic approval.
3. Give two annotators separate shuffled copies containing only anonymous `id`, reviewed `text_redacted` and space for their category. Hide source, original labels, model outputs, notes and each other's answers. Coordinator populates `annotator_1_id`, `annotator_1`, `annotator_2_id`, `annotator_2` afterward. IDs are opaque pseudonyms, not names/emails.
4. Preserve both original labels. Use `adjudication_status=pending` with an empty final category until review. `agreed` requires matching non-uncertain labels and `adjudicated_category` equal to them. For disagreement/uncertainty, use `adjudicated` only after recording an `adjudicator_id`, final category and a brief nonidentifying `adjudication_note`. Final `uncertain` remains excluded.
5. Set `financial_scope=true` only after checking the task definition, `false` when outside it, or leave blank while unresolved. Genuine general conversation is not automatically a primary-study financial negative.
6. Enter `received_at` only for genuinely known receipt timestamps with timezone. Never copy `date_collected`, a publication date, file modification time, or an invented time into it. Leave unknown values blank. Unknown dates block chronological evaluation, not group-based tooling.
7. Optional `template_group` is an opaque label-blind reviewed campaign/template ID. Automatic normalization and near-copy grouping also apply; manual groups join connected components rather than overriding duplicate controls. Review mixed-label groups without changing labels just to improve scores.
8. Optional URL facts must be genuinely measured under the approved protocol before URL removal: all four fields or all blank. Actual linkless zeros are valid; unknown is not zero. No DNS/HTTP requests are made by the pipeline.

## Contract and outputs

`source_ref` points to a controlled provenance/evidence ledger held separately; do not paste donor names, phone numbers or private links into it. `consent_verified` and `redaction_verified` are literal `true` or `false`, entered by a reviewer. Use `--review-reference` for the intake decision record; the legacy `approval_reference` output column/CLI alias is retained, not a project/ethics approval gate. Donation origins require `consent_verified=true`; other sources rely on documented permitted use without inventing participant consent. Every imported row needs documented permitted use for its selected role, `redaction_verified=true`, resolved labels and financial scope. Pending use/role or review holds are eligibility not yet verified, not a declaration that records are invalid. `label` is derived as 1 for financial phishing and 0 for legitimate financial messages; never manually fabricate it.

`import-report.json` reports original pre-adjudication four-category confusion counts, observed agreement and Cohen's kappa on paired labels, including uncertain/out-of-scope cases. Missing pairs and undefined kappa are explicit. Agreement does not establish ground truth. The held ledger contains only IDs/reasons, not text. `approved.csv` has the generated `dataset-schema.csv` columns. Identifiers, dates, source and annotation metadata never become model features.

The supplied 1,276 records do not yet meet this contract. Do not fabricate missing independent labels, redaction reviews, consent or evidence to make import pass. Reserve new, genuinely unseen records for prospective confirmation; these existing records were already used to fit the supplied model.
