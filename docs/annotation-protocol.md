# Independent annotation preparation

Use `research/LABELING_GUIDE.md` for the four categories and edge cases. A URL, urgency, claimed institution or inherited source label alone is not sufficient evidence. Genuine OTP/advisory language can be legitimate; financial impersonation without a URL can be phishing; unrelated scams remain `other_spam_scam`; insufficient context is `uncertain`.

## Private files the team must complete

| File | Who / action |
|---|---|
| `research/data/review-v1/redaction-review.csv` | Human reviewer fills reviewed text, verified/excluded status, opaque reviewer ID and necessary nonidentifying note. Pending rows remain withheld. |
| `research/data/review-v1/coordinator/mapping.json` | Coordinator-only original mapping; preserve unchanged; never distribute to annotators. |
| `research/data/review-v1/coordinator/source-matches.json` | Coordinator verifies acquisition/terms against controlled originals; matches alone are insufficient. |
| `research/data/review-release-v1/annotator-a.csv` and `annotator-b.csv` | Generated only after redaction release; each independent annotator completes category, language (`en/fil/taglish`), financial_scope (`true/false/uncertain`) and optional note. |
| `research/data/review-release-v1/adjudication.csv` | Copy `research/templates/adjudication.csv`; adjudicator records one final category, opaque ID and reason per released record after originals freeze. |
| `research/data/annotation-progress.csv` | Copy progress template; coordinator records actual counts/evidence, no invented completion dates. |
| `research/data/reviewed-intake.csv` | Copy `research/intake-template.csv`; coordinator truthfully merges evidence, original independent labels, final scope/adjudication and study role. |

The existing `annotator-a-pending.csv` and `annotator-b-pending.csv` contain IDs only; they must not be annotated. No released real-message sheets or agreement results are fabricated by this task.

Before release remove personal names, numbers, account/card identifiers, OTPs, email, private URLs and embedded identifiers, including obfuscation. Use the guide's uniform placeholders, preserve substantive wording and review spreadsheet escaping. Regex checks are only blockers; they cannot certify redaction. Separately verify permission for annotator access; redaction release is not permission clearance. Keep personal/social records held until evidence is complete.

Distribute each annotator only their own released file and the guide. Hide original labels, source identities, coordinator mapping, model outputs and the other annotator's decisions. Existing packet tests verify the exported schema and withheld-text boundary, not human independence. Store response hashes and a private independence attestation before adjudication. Use an unrelated training exercise for labeler training, not shared decisions on evaluation rows.

```powershell
$env:PYTHONPATH='research'
research\.venv\Scripts\python.exe -m smishguard.review_packets release research/data/review-v1 research/data/review-release-v1
research\.venv\Scripts\python.exe -m smishguard.annotation_results research/data/review-release-v1/annotator-a.csv research/data/review-release-v1/annotator-b.csv --adjudication research/data/review-release-v1/adjudication.csv --output research/data/review-release-v1/agreement.json
```

The validator rejects blank/invalid responses, unequal ID cohorts, duplicate IDs, changed text and incomplete adjudication without logging message values. With two sheets it reports Cohen's kappa; with three or more distinct sheets, equal-rater Fleiss' kappa. Raw agreement is mean pairwise agreement; disagreement count means non-unanimous records. Degenerate chance agreement yields null kappa. Missing responses are rejected, not silently dropped. Agreement includes uncertain/out-of-scope labels before adjudication. Final label counts do not establish eligibility; the intake validator still applies.
