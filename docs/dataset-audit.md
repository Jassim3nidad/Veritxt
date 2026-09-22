# Supplied dataset audit — 21 September 2026

Inspected the local attached ZIP, all three member files, existing decisions, and the three supplied thesis documents. The Drive alternative was not used or claimed as accessed. The original ZIP in Downloads is unchanged; byte-identical preservation and private working copies are under ignored `research/data/package-audit/`. [Aggregate machine-readable audit](dataset-audit.json) records SHA-256 for the ZIP, CSV, model and guide. Raw data, original guide and private review ledgers are excluded from the APK/source deliverables.

## Verified inventory and counts

| Observation | Verified result |
|---|---|
| Records / unique IDs | 1,276 / 1,276 |
| Labels | 1,054 ham, 222 smishing; no invalid/missing label values |
| Language labels | 1,149 English, 127 Taglish; no Filipino-only label. These are supplied annotations, not independently verified language judgments. |
| English label breakdown | 950 ham / 199 smishing |
| Taglish label breakdown | 104 ham / 23 smishing; subgroup holdouts may have too few positives for reliable metrics |
| Exact message duplicates | 4 duplicate groups / 4 excess rows; 1,272 unique texts; no exact-text label conflict |
| Normalized exact templates | 1,249 groups; 27 excess rows; no normalized-exact label conflict |
| Near-template components | 940 groups; 133 multirow components; 2 mixed-label components require review |
| Date column | 1,198 values, all date-only; 78 missing; collection versus receipt meaning unverified |
| Missing fields | institution and official domain: 70 each; spoofed URL: 1,111; notes: 3. Blank URL is not proof of no URL in the text. |

Grouping uses label-blind `sg-ascii-v1` normalization (URL/email/number placeholders) plus SequenceMatcher >=0.85, connected components, including exact matches. This heuristic deliberately collapses many variable-number/link templates. It is not a human campaign annotation; mixed labels can be meaningful legitimate-versus-phishing variants, not necessarily labeling errors. Review the ID-only private ledger. Normalization is used for grouping, **not substituted into the supplied model tokenizer**.

## Source claims and shortcut risk

Source names remain unverified CSV provenance claims. The subsequently supplied signed client-request letter and reported go-ahead are recorded in [project authorization](project-authorization.md). Source-specific licenses/permitted-use records, donation consent and collection lineage have not yet been documented in the reviewed package; these are separate from project authorization.

| Claimed source | Ham | Smishing |
|---|---:|---:|
| Facebook | 0 | 1 |
| Reddit r/ScammersPH | 0 | 2 |
| Personal (received) | 1 | 9 |
| Public PH SMS spam dataset (archive.zip) | 21 | 82 |
| UCI SMS Spam Collection (public baseline) | 70 | 0 |
| Kaggle: Tagalog-SMS / Text-Messages.csv (cited in BantayText, DLSU) | 962 | 128 |

The source/label association is substantial: all UCI rows are ham; all social-post rows are smishing; the public archive is mostly smishing, while the cited Kaggle collection is mostly ham. This could make source style, annotation/redaction practices or message shape a shortcut even if the source column is excluded from inputs. The audit does not fit a source classifier or call an in-sample statistic predictive accuracy. Controlled groups, URL ablation, placeholder/shape/punctuation checks and future source-held-out analysis remain necessary.

## Primary-study eligibility and financial scope

- **70 UCI rows** are separately copied to `external-uci.csv` for supplementary review only. They are described as general nonfinancial SMS in the supplied annotation. The supplied fixed model already saw them, so they cannot be called unseen supplementary test data for that model.
- **1,206 non-UCI rows** remain unverified. One explicitly names NCAP/MMDA and a traffic-fine scam, outside the proposal's financial-institution impersonation scope.
- Removing that explicit other-sector row leaves **1,205 nominal financial-institution candidates, 1,201 unique exact texts and 869 heuristic template groups**. These are upper-bound candidate counts, not eligibility certification. Institution/attack labels alone cannot establish actual intent, sender legitimacy or financial scope; every candidate needs independent review.
- Assess archive, Kaggle and social-post records individually by origin, documented permitted use, scope and review quality. They are not automatically rejected because of hosting/source category. The ten `Personal (received)` rows need donation consent/redaction evidence. See the [source-by-source evidence list and affected activities](source-evidence.md).
- **Primary-study eligibility not yet verified.** Eligible row/group counts are unknown (`null` in the machine-readable audit), not a finding that all records are invalid. The nominal candidate counts above remain valid audit counts. Dataset-specific permitted-use evidence and label/redaction review are separate from the recorded project/client go-ahead; no repeat project approval is requested.

Do not claim the 1,200 minimum from the unfiltered 1,276 total. Even the 1,201 unique-text nominal pool is provisional and its effective template diversity is 869; report all counts after review rather than equating rows with independent campaigns. The 2,500 target and minimum/sample-size protocol remain research decisions.

## Privacy and dates

Heuristics found message-text candidates in 3 rows for emails, 147 for long numeric/phone-like sequences, 120 for explicit HTTP/www URLs and 1 for a name-style salutation. These categories overlap and include possible institutional contacts, amounts or nonpersonal identifiers. They are **not confirmed PII counts or proof of adequate redaction**. No examples, addresses or suspected personal values are printed in the audit. URLs were not opened. Names, obfuscated identifiers and private paths still require human review.

Two learned vocabulary terms contain at least seven consecutive digits. Model vocabulary can retain training tokens even though no complete dataset is bundled. Their privacy status requires review before broader distribution; the supplied weights/vocabulary were not silently changed. Runtime pasted/shared message text remains transient and is not added to assets or data files.

`date_collected` is not renamed to `received_at`. Its meaning is undocumented, and its values lack time and timezone. No receipt dates are inferred or invented; chronological evaluation is unavailable until actual timestamp provenance is supplied.

## Claims and study limitations

The guide says the export was fitted on all 1,276 rows. The ZIP contains no training/evaluation scripts, fold manifests, seed records, CI method, model-comparison output or calibration evidence. Its accuracy, F1, confidence interval and Random Forest comparison cannot be reproduced from this package. The ham/smishing ratio does not establish realistic traffic prevalence; the sources are curated and strongly associated with labels. The proposal itself calls for explicitly hypothetical base-rate sensitivity, not this prevalence claim.

Any new split/retraining of these already used data is **retrospective exploratory evaluation**, even with clean within-run train/calibration/validation/test separation. Prospective confirmation needs genuinely unseen records. The supplied export was used only for technical conversion/reference/parity checks, not same-data accuracy estimation. Transformer comparisons remain pending.

## Team evidence needed next

1. Dataset-specific permitted-use evidence linked to anonymous source references, itemized in [source-evidence.md](source-evidence.md), plus the intended primary/supplementary role. Project/client authorization is already recorded and is not requested again. The letter does not settle formal ethics-clearance status or model redistribution rights.
2. Independent blinded annotations, agreement/adjudication records, financial-scope decisions and human redaction review; resolve the two mixed-label template components and review learned numeric tokens.
3. A data dictionary explaining `date_collected`; actual receipt timestamps/timezones only where genuinely known.
4. Original preprocessing/training/CV code, library versions, seeds, fold/group IDs and the method behind the reported confidence interval/model comparison/calibration, if available.
5. More independent primary financial messages, especially legitimate hard negatives and Taglish positives; reserve an unseen prospective cohort. Approve the experiment/threshold policy before opening final-test results.

Physical-device SMS delivery, installer permission behavior and manufacturer background restrictions remain **Pending physical-device testing.** They do not block this tooling or manual emulator development.

## Source investigation update

Official-host candidate versions/licenses and content overlap are now recorded in [source-evidence.md](source-evidence.md) and [source-match-summary.json](source-match-summary.json). All 1,090 Kaggle-labeled rows match the union of two inspected collections; all 103 archive-labeled rows match a third. This supersedes the earlier absence of externally checked source evidence, without automatically assigning row licenses, labels or research eligibility. The supplied ZIP itself remains unchanged. Private anonymous review packets cover all 1,276 rows.
