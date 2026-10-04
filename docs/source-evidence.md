# Dataset source evidence — inspected 21 September 2026

3 October development update: the user authorized a preliminary inherited-label comparison. Direct text from pinned CC0/CC BY source copies supports the bounded 1,068-record subset described in [the four-model report](four-model-comparison.md). This later decision does not fill the original pending human reviews, establish permissions for held personal/social records, or make the internal test prospective. The dated source evidence below remains unchanged.

29 September complete-package update: the new CSV has `id`, `text`, `label`, `source_category`, and `source`. Its source strings attribute 1,446 records to Tagalog-SMS, 972 to PH Spam + Marketing SMS, 90 to Philippine Spam/Scam SMS, and 13 to Facebook/Reddit/personal receipt. These are supplied attributions, not verified licenses, donation consent, row-level source matches, redaction attestations or independent annotations. No completed review records are supplied. The notebook, run metadata and per-seed results add procedure evidence; the notebook contains zero saved outputs and zero execution counts. Existing review packets and authorization statuses were preserved. See [complete-package findings](mark-complete-findings.md).

Project/client authorization remains **reported authorized to proceed**; it is not requested again. Dataset **eligibility not yet verified** is separate from source identification, permitted-use documentation, annotation/redaction and model evaluation.

## Supplied-file inspection

Read all three ZIP members, the original pasted request, the supplied Chapter 1 / Chapter 2 / client brief DOCX texts and hyperlinks, the signed-letter image and previous setup screenshots. The CSV `source` and `notes` fields contain **no source URLs**. Its 1,090 Kaggle rows say their labels were generated from source categories plus claimed domain verification; that is not independent annotation. The package provides neither exact original versions nor acquisition/merge code. The model metadata and guide provide no dataset license or training/split records. The supplied thesis chapters cite BantayText DOI `10.1109/FMLDS67896.2025.00121`.

Related local proposal/RRL variants were also inspected for clues, not adopted as new instructions. One proposal excludes Kaggle primary data and drops BantayText; later supplied chapters cite its DOI. The current user instruction governs: assess aggregators individually, keep UCI supplementary, and document the team's intended study-role decision rather than silently changing its protocol.

## Verified pages, snapshots and affected records

Downloads and row ledgers stay under ignored `research/data/`. [Machine-readable snapshot hashes and match counts](source-match-summary.json) identify exact file bytes. Public reports contain no message examples or row-level donor mapping. Version numbers below come from the live Kaggle API metadata retrieved during this inspection, not older search-cache snippets.

| Source | Verified original-host evidence | Affected supplied records / remaining boundary |
|---|---|---|
| ZERO (`onzero0`), **Tagalog-SMS v1** | [Dataset page](https://www.kaggle.com/datasets/onzero0/tagalog-sms). API lists **CC0: Public Domain**, version 1. Download contains `tagalog-sms.xlsx`, 3,454 rows; fields Date/sender/text/category. | **471 exact matches** among the 1,090 Kaggle-labeled rows; another 6 among archive-labeled rows. Candidate content correspondence established; acquisition/version/transformation chain still needs confirmation. |
| Scott Lee Chua, **PH Spam + Marketing SMS v15** | [Dataset page](https://www.kaggle.com/datasets/scottleechua/ph-spam-marketing-sms-w-timestamps). API lists **CC BY 4.0**, version 15. Download contains `text-messages.csv`, 8,895 rows, including receipt/read timestamps; page describes receipt times as UTC+8. | **303 exact + 329 whitespace-only matches** among the 1,090 Kaggle-labeled rows; 1 exact archive match. Do not transfer candidate timestamps to supplied records without verified row lineage. |
| BwandoWando, **Philippine Spam/Scam SMS v49** | [Dataset page](https://www.kaggle.com/datasets/bwandowando/philippine-spam-sms-messages). API lists **CC BY-NC-SA 4.0**, version 49. Download contains `SPAM_SMS.csv`, 1,021 rows. | **All 103 archive-labeled rows match**: 54 exact + 49 whitespace-only. One Kaggle-labeled row also matches after whitespace normalization. `archive.zip` alone was ambiguous; content now identifies this strong candidate, not the actual download chain. |
| Almeida / Gómez Hidalgo, **UCI SMS Spam Collection** | [Official UCI page](https://archive.ics.uci.edu/dataset/228/sms+spam+collection), [dataset DOI](https://doi.org/10.24432/C5CC84), listed **CC BY 4.0** and 5,574 instances. | **70 supplied ham rows remain supplementary.** Official ZIP requests failed certificate validation (expired certificate / alternate-host mismatch); verification was not disabled. No row match to official bytes is claimed. Need the team's original file/hash or a working authenticated official download. |
| Personal (received) | Only the supplied claim is available. | **10 rows**: anonymous donor mapping, donation consent/use scope and redaction review needed. |
| Reddit r/ScammersPH / Facebook | Supplied source names, no original-post URLs. Broad unrelated posts were not substituted as matches. | **2 Reddit + 1 Facebook rows**: private original references, message origin and applicable reuse evidence needed. |

The **union of the first two collections matches all 1,090 Kaggle-labeled rows**; 13 match both collections. Across all three downloaded candidates, 14 Kaggle rows and 7 archive rows match multiple collections. Counts overlap and must not be added as new samples. Matching is exact Unicode equality first, then whitespace collapse only; no case folding, URL replacement or near-template matching is used to establish these correspondences. Shared templates/reuploads mean even exact content does not prove which source was acquired or which terms apply to a particular copy. No license or approval flag was automatically set on our rows.

## Terms and attribution to retain

- [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) is the dedication shown for the Tagalog-SMS candidate. It does not itself verify ownership or remove every privacy/right-of-person concern.
- [CC BY 4.0 legal code](https://creativecommons.org/licenses/by/4.0/legalcode) supports sharing/adaptation under attribution and other conditions. Preserve creator/source credit, license link and change indications for the Chua/UCI materials where their origin is established.
- [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) adds noncommercial and share-alike conditions. Do not treat permission for academic analysis as unrestricted redistribution of data/model artifacts or as evidence of consent for personal information.

These are observed published terms, not blanket clearance for all supplied rows. The original author/version and transformations should remain attached to the coordinator's evidence ledger. Nothing is relabeled merely because a host lists an open license.

## Original-repository / publication search

The supplied [BantayText DOI](https://doi.org/10.1109/FMLDS67896.2025.00121) resolves to IEEE document 11446554, but the publisher required a JavaScript/bot check; its full paper was not read through that page. A [BantayText dashboard repository](https://github.com/Matcheww/bantaytext-smishing-detection-dashboard/tree/5e45424263da8d7769178a58096797301daf437b) describes a refreshed merged dataset and explicitly notes post-publication source drift. Its inspected tree has no source dataset, original acquisition notebook or declared repository license. It does **not** reproduce SmishGuard's supplied export, its five-seed/CV claims or its claimed calibration. Repository identity was not independently authenticated as the paper's complete original experiment archive. No model-performance numbers from it were adopted.

## What can proceed, and what cannot yet run

Source tracing, local overlap checks, app development, offline inference/parity and safe-fixture tests proceed under the recorded authorization. The local model/APK are preserved. **No new real-data baseline comparison was run:** independent target-task labels, human redaction verification and record-specific permitted-use/study-role decisions are not complete. The prepared importer therefore cannot yet produce the reviewed primary input. Unknown receipt provenance blocks chronology only; group evaluation does not require invented dates. After exclusions/grouping the minimum viable primary corpus must still be checked. UCI is not added to reach the minimum.

Current public source matches do not resolve label semantics: broad source `spam` is not automatically financial phishing, and notifications/ads/OTP categories do not by themselves prove legitimate sender identity. Previously used rows remain retrospective even after review. Calibration/threshold selection/final testing remain separate; no exploratory score is presented as validated thesis performance.

## One team checklist

1. **Confirm acquisition and transformations:** original downloaded files/version/hash or merge script linking the 1,090 Kaggle and 103 archive rows to the identified candidates; resolve multiply matched rows. Include the original UCI file/mapping for its 70 supplementary rows. Supply the chosen primary/supplementary role in the study protocol.
2. **Provide the private-only origin evidence:** donor consent/use scope for 10 personal rows; original post references and reuse basis for the 3 social rows. No new project/client approval requested.
3. **Complete the prepared reviews:** human redaction sign-off, then two independent blinded labels and adjudication/scope decisions. If these records already exist, provide them keyed to the coordinator mapping. Explain `date_collected`; provide genuine receipt timestamps only where known. Original training/split scripts are optional evidence for reproducing the old guide's claims, not a prerequisite for fresh group-based baselines.

Private preparation is at `research/data/review-v1/`: 1,276 anonymous IDs, restricted redaction queue and coordinator mapping, and two independently shuffled ID-only pending annotation sheets. Run the release command only after human review; annotators then receive reviewed text with no source, old label, notes, timestamp or model score. [Workflow and commands](../research/README.md). Physical-device testing remains pending.

## Completion review on 23 September 2026

Source evidence above remains the dated inspection record; no new source permission, consent, acquisition history or external download was inferred in this pass. The supplied package audit was reproduced exactly. Personal/social records remain excluded from model development until their specific evidence and human reviews are complete. The private freeze manifest and new annotation validator do not clear any source. Complete the exact files in `annotation-protocol.md`; source overlap remains correspondence, not proof of acquisition.
