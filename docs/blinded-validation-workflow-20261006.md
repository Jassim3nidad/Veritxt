# Independent annotation and adjudication

Two private packets cover the same 3,340 eligible records from the expanded experiment. They have independently shuffled orders and unrelated random review IDs. Each packet contains only a review ID, the shared case-preserving redacted text, and blank response fields. Existing labels, categories, sources, confidence, review flags, partitions and model outputs are absent. The coordinator alone holds the ID crosswalk. These are retrospective review packets, not new prospective observations.

Private working directory: `research/data/validation-20261006/review/`. Give annotator A only `annotator-a.xlsx` (or its CSV) and the labeling guide; give B only B's packet and the guide. Never share the coordinator directory, the other annotator's responses, or model-result reports. No packet is evidence of completed annotation. A coordinator must check the redacted views before controlled release; the blank `coordinator/privacy-release.csv` records that work. Any text correction requires a new matched packet version for both reviewers, preserving these originals.

1. Assign two different reviewers who have not seen the inherited labels or model predictions. Record their codes and signed independence attestations in `coordinator/attestations.csv`. If prior exposure exists, disclose it and use different reviewers where possible; software cannot certify blinding.
2. Reviewers work independently using the guide, fill every decision/rationale/privacy response, and enter their reviewer code and actual UTC completion time. Leave unresolved cases `uncertain`; never infer a decision from a blank. Keep message text and review IDs unchanged. Review in manageable sessions and record deviations privately.
3. Return the `Review` sheet as UTF-8 CSV, with its original column names and all rows. Preserve original returns and their file hashes. Do not let reviewers reconcile disagreements before pre-adjudication agreement is calculated.
4. Run the agreement command below into a new output directory. It checks assigned IDs and text, reports response coverage, constructs the 4-by-4 decision table, and computes Cohen's kappa. A second binary calculation includes only pairs where both reviewers chose `phishing` or `genuine`; its omitted-pair count must accompany it. Report the four-category estimate as primary so uncertainty/exclusion does not disappear. Partial-pair estimates are provisional and may be biased by missing responses.
5. A third adjudicator uses the generated private `adjudication.csv`, which shows both independent decisions and rationales but no inherited labels or model predictions. Confirm agreements explicitly and resolve disagreements, uncertainty, scope and privacy issues with a written reason. Leave any unresolved final decision blank or `uncertain`. Do not replace independent responses. The validator rejects edited input evidence or final decisions preceding two responses.
6. Freeze signed responses, agreement output and adjudication with hashes before any model re-evaluation. A future independently reviewed-label analysis must be separately versioned. It must retain the original inherited-label results and disclose that it reuses historically exposed messages.

Agreement is `Po = matching completed pairs / completed pairs`, `Pe = sum_k(pA,k × pB,k)`, and `kappa = (Po − Pe)/(1 − Pe)`. Missing pairs are excluded from the denominator and reported. Zero paired responses and `Pe = 1` yield an undefined (`null`) kappa, not zero or perfect agreement. Include marginals/confusion counts and coverage alongside kappa; do not infer annotation quality from a categorical kappa label alone. Current completed decisions: **0**; agreement and adjudication are **pending**.

```powershell
$env:PYTHONPATH='research'
research/.venv/Scripts/python.exe -m smishguard.validation_stage agreement `
  research/data/validation-20261006/review/returns/a.csv `
  research/data/validation-20261006/review/returns/b.csv `
  research/data/validation-20261006/review/coordinator/agreement-v1
research/.venv/Scripts/python.exe -m smishguard.validation_stage adjudicate `
  research/data/validation-20261006/review/coordinator/agreement-v1/adjudication.csv `
  research/data/validation-20261006/review/coordinator/agreement-v1/final-summary.json
```

The supplied 18 excluded job/loan conflicts require separate scope adjudication. They are not silently added to this cohort. The 212 held records remain held; this workflow neither grants source permission nor establishes consent. Private packets and returns must not enter public Git or group-wide public links.
