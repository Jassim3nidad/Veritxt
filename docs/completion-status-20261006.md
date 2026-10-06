# Completion engineering status

Revised thesis title: **Pending finalization**. The original title remains historical; title-dependent edits remain pending. The scope is **all SMS phishing**, recorded as a team clarification without claiming adviser approval.

Completed:

- Updated current scope, working questions/objectives, Chapter 3/4 drafts and labeling guidance. Older financial-only protocols and results remain historical; frozen protocol files were not edited.
- Extended the existing annotation tooling with preserved input snapshots/hashes, return integrity checks, reviewer/timestamp validation, third-person adjudication and a new dataset version that retains original labels and exclusions.
- Added screened prospective admission and a single-opening four-model evaluator with private paired predictions and JSON/CSV/Markdown comparison tables. It reuses the four original frozen scorers, calibration and thresholds. A separate runtime lock preserves the original model-freeze time and hashes.
- Improved historical screening for header aliases, archived headerless UCI data, symmetric near-copy checks and empty normalized text. Refreshed the private index: 281 local files, 5,040 normalized views. No-match still requires human semantic review.
- Produced and verified the separate [mBERT INT8 experiment](mbert-int8-experiment-20261006.md), including accuracy limitations, size, host speed, score/decision differences and Android emulator compatibility. Original models/APKs remain intact; reporting stays disabled.

Verification: 95 research tests passed and dependency checks passed; eight safe-handoff checks passed; the 11 new completion tests include a fictional end-to-end pipeline and integrity/chronology failures. Actual frozen scorers reproduced saved reference scores on 13 synthetic probes (linear errors below `1e-10`, mBERT maximum `3.39e-6`). The INT8 build/lint/JVM/emulator evidence and hashes are in the [aggregate verification record](completion-engineering-verification-20261006.json).

Concrete blockers:

- No completed independent A/B returns, signed review controls or adjudication were supplied/found. Prepared packets still record zero human decisions; no real agreement or relabeling is claimed. Use the [completion runbook](review-completion-20261006.md) when returns arrive.
- No new prospective messages or closed independently reviewed cohort were supplied. Actual four-model fresh-test evaluation remains pending collection, evidence/semantic screening and labels. Synthetic fixtures and old records are not substituted.
- No groupmate physical-phone results were supplied. Installation, crash, loading and layout fixes must follow actual device evidence; emulator passes do not establish physical-phone compatibility. Existing Xiaomi restrictions remain documented in the phone guide.
- The revised thesis title is still pending finalization. Documentation and validation proceeded independently of that decision.

No messages were sent to groupmates, no reviewer responses or physical results were invented, and no private model/data/APK is included in the public change set.
