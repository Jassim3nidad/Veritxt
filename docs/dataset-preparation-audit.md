# Dataset preparation audit on 29 September 2026

This read-only audit reuses the original 1,276-row corpus, existing anonymous mapping, redaction queue, A/B pending sheets and pinned source snapshots. It produces private coordinator queues and public aggregate counts. No consent, permissions, labels, signatures, dates or unseen-test status was created; no model was trained. [Machine-readable aggregates](dataset-preparation-audit.json), [team task sheet](dataset-team-task-sheet.md) and [sample-size provenance](sample-size-provenance.md) accompany this report.

## Completed checks

| Check | Primary corpus result |
|---|---|
| Preserved source bytes | SHA-256 `554df67a04b65425e81b7bd577f36b82ddaf48287f2a61677f940213fb66269b`; also matches the primary CSV inside the later private-data ZIP |
| Schema/cohort | Expected 11-column schema; no malformed rows, duplicate IDs, blank message text, missing inherited labels or unsupported inherited label values; all existing anonymous IDs and mapped originals match |
| Inherited labels | 1,054 ham / 222 smishing; not independent judgments |
| Exact duplicates | 1,272 unique texts; four duplicate groups/four excess rows; no conflicting-label groups |
| Normalized duplicates | 1,249 groups; 20 duplicate groups/27 excess rows; no conflicting-label groups; three groups span supplied source labels |
| Heuristic templates | 940 components; 133 multirecord components/336 excess rows; two mixed-label components containing 22 rows; 21 components span supplied source labels |
| Source snapshot overlap | All three pinned member hashes verified. 1,193 primary rows match at least one candidate snapshot; 21 match multiple candidates. Recomputed row matches equal the existing private source ledger exactly. This is not proof of acquisition chain, applicable permission or source-label correctness. |
| Potential identifiers | 285 rows match one or more overlapping heuristics: email 3, long-number/phone-like 147, explicit URL 120, name-style salutation 1, obfuscated link 2, short code near OTP/PIN/code context 55 |
| Human redaction state | All 1,276 pending; zero reviewed texts and zero reviewer IDs |
| Independent A/B state | 1,276 IDs per sheet, zero released message texts and zero categories in either pending sheet; 2,552 missing independent judgments |

The original four identifier heuristics reproduce the earlier counts. Two added patterns broaden the review queue; the larger union is not a count of confirmed personal information. Regex false positives/negatives, names, obfuscation and meaning lost by replacement require human review on every retained record. Explicit URLs were not followed. Missing optional metadata is not automatically an exclusion: 78 collection dates, 70 claimed institutions, 70 official domains, 1,111 spoofed URLs and three notes are blank. A blank link field need not indicate a defective message. Collection dates are not verified receipt timestamps.

## Separate handoff records

| Collection inspected locally | Rows / inherited labels | Exact / normalized / template groups | Potential identifier candidates | Cross-corpus findings and disposition |
|---|---|---|---:|---|
| supplementary_everyday_ham.csv in private-data ZIP | 1,050 / all ham | 1,050 / 1,028 / 718 | 452 | No exact, normalized or combined-template overlap with primary at the tested policy. One normalized and five template components span its supplied sources. Labels were derived from source categories by the supplied builder, not independent annotation; none cleared for primary use. Prior training exposure still needs Mark's record. |
| fresh_test_messages.csv in earlier repository-update ZIP | 34 / 20 ham, 14 smishing | 34 / 34 / 34 | 5 | No tested overlap with primary or direct template match to the supplementary set. These probes were already exposed in candidate review, so lack of overlap does not make them a new unseen cohort. |

Both extra CSVs pass their own source schemas and have no missing inherited labels or duplicate source IDs (probe rows have no source ID column; audit-local row keys were assigned only in memory). The probe audit's missing metadata counts refer to its projection into the common audit representation, not a claim that its original three-column CSV is malformed. Neither collection was copied into primary A/B packets or added to training. Snapshot names/licenses remain historical source evidence; no new license or donor-permission conclusion is asserted.

## Reused work and new private files

Preserved, unchanged: `research/data/review-v1/coordinator/mapping.json`, `manifest.json`, `source-matches.json`, both pending A/B sheets and `redaction-review.csv`; the original dataset copies, model files and APK also remain unchanged.

New: `research/data/preparation-20260929/audit/coordinator-check-queue.csv` links existing anonymous IDs to review flags/groups without printing messages in logs; `origin-review.csv` has pending evidence fields and content-match hints. The latter's 1,276 annotation-access decisions are all pending. `controls/` contains header-only training-history, independence, unseen-reservation, methodology-decision and split-assignment templates. Empty `research/data/review-responses-v1/` is prepared for future returned sheets. No text-bearing released sheets or populated adjudication decisions exist yet.

Exclusion unions and remaining candidate/eligible counts are in the task sheet. The conservative 1,193-row candidate set has 1,189 exact-unique texts and 859 existing template components. Holding the two mixed-label components leaves 1,171 rows, 1,169 exact-unique texts and 857 components. These are counts of remaining memberships in the full-corpus grouping, not a fresh reclustering after exclusions. All still require review. No count meets an eligibility gate merely by excluding other records.

## Verification and reproduction

The exhaustive template calculation was accelerated by skipping pairs already connected and by a character-multiset upper bound before the same SequenceMatcher score. Neither shortcut changes the grouping rule. A synthetic regression test compares exact assignments against the exhaustive implementation at three thresholds, and real primary counts match the prior audit. The initially slow calculation was stopped before it wrote private queues, then completed with the equivalent implementation; no partial results were adopted.

Run from the repository root, with output under ignored `research/data/` and a new directory name:

```powershell
$env:PYTHONPATH='research'
research\.venv\Scripts\python.exe -m smishguard.prepare_team_data --output research/data/preparation-NEXT/audit --private-archive "$env:USERPROFILE/Downloads/smishguard_PRIVATE_data.zip" --exposed-archive "$env:USERPROFILE/Downloads/smishguard_repo_update.zip"
research\.venv\Scripts\python.exe scripts/verify_research.py
```

Verification: the full research software suite passed 57 tests with zero failures/skips, and the safe-handoff suite passed eight. The real release check correctly rejected the current origin-review ledger with “No documented annotation access; no messages released”; no release directory was created. Software tests also exercise verified-redaction gating, hidden previous metadata, frozen-text integrity, complete response cohorts, original-answer preservation, independent adjudicator IDs, and reserved-test assignment integrity. A prior random split can no longer be declared prospective by a CLI flag alone; the legacy training entry point directs prospective work to the manifest-based comparison workflow. No real response agreement or final label count is fabricated from pending sheets.

Android build/emulator checks were not repeated: this task changes no Android source, assets or settings. The historical LR model SHA-256 remains `9026c925679f9667b5bd09e34f31dd884cdb72607650d97f9a0708c86fa6bab2`; the delivered APK remains `62f1a7c96b4bbd59d95f9c6ab1f73aba27d3d2dbea1c7b3c43c774c0ca6526f0`. Earlier verified APK behavior is not a dataset-quality or model-accuracy claim.
