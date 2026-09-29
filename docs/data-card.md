# Supplied dataset data card

29 September complete package is a separate 2,521-row corpus (2,270 ham / 251 smishing), with 742 exact stripped-text matches to the earlier supplied corpus. Its source/category columns do not establish research eligibility. Do not replace the earlier audit below or reuse its anonymous review IDs for unmatched records. The new corpus remains exposed and unreviewed; the notebook's nominal test partition does not establish unseen status. [Full audit and limitations](mark-complete-findings.md).

29 September preparation: [reproduced audit and separate handoff inventory](dataset-preparation-audit.md) and [current team tasks](dataset-team-task-sheet.md). The 1,200 guard is a sourced feasibility target whose approved applicability and financial-only interpretation remain unresolved, not a universal statistical requirement; see [source trace](sample-size-provenance.md).

Snapshot: `dataset-audit.json` plus `dataset-freeze-summary.json`. A private anonymous per-record/group manifest is stored under ignored `research/data/thesis-audit-20260923/manifest-v2.json`; its hash is public. Original private bytes were preserved. Hashes are identifiers, not anonymization guarantees, so the row-level manifest also stays private.

The supplied corpus has 1,276 records: 1,054 inherited ham and 222 inherited smishing labels; 1,149 supplied English and 127 Taglish values. These are not independently verified target-task or language labels. The audit reports exact/normalized duplicate groups, missingness, heuristic near-copy groups, conflicting-label groups and source counts. The supplement adds character-length quantiles and overlapping URL/phone-like/financial-keyword indicators with explicit regex definitions. Indicators are not verified PII or financial scope.

Roles and eligibility:

| Category | Current disposition |
|---|---|
| Eligible model-development rows | Not yet established; no rows were newly cleared by the audit |
| 70 UCI-labeled rows | Supplementary role only, with source/label/use review still required; never fill the primary minimum |
| One explicit nonfinancial-sector record | Excluded from primary financial task; retain only in a separately defined permitted task |
| Other nominal financial candidates | Await source-specific permitted use, financial-scope review, redaction and independent labels |
| 10 personal rows | Excluded from model development until donation consent/use and review complete |
| 3 social-source rows | Excluded from model development until controlled origin/reuse evidence and review complete |
| Pending/uncertain/out-of-scope labels | Held or excluded by intake; never auto-converted to ham |

Known candidate source overlap is documented in `source-evidence.md`; exact matches do not prove acquisition history or applicable terms. Keep original versions, transformations and attribution in a controlled ledger. Do not infer ethics clearance, donor consent or model redistribution rights from client authorization.

`date_collected` is not a verified receipt timestamp and cannot support chronological evaluation. Preserve unknowns. Sampling is curated, not population-representative; legitimate financial hard negatives and independent Filipino/Taglish positives remain research needs. The 2,500 target/1,200 eligible minimum is unresolved; row count and independent template count must both be reported.

Storage/access: private raw collection, packet mapping and annotator files remain outside Git/ZIP/APK. Assign actual access custodians, retention/deletion schedule and controlled evidence references before collection/release; no dates or permissions are invented here. The app never contributes scan text to this corpus. Public redistribution is withheld pending source and privacy review.
