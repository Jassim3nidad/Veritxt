# Thesis gap analysis

Assessment: 23 September 2026. The offline development prototype is technically testable; the thesis evaluation and partner turnover are incomplete. Statuses refer to evidence, not projected dates. No approved scope has been removed.

Reviewed local sources: `SmishGuardPH_Chapter1_Introduction_1.docx` (Objectives; Scope and Limitations), `SmishGuardPH_Chapter2_RRL_1.docx` (evaluation pitfalls; frameworks), and `SmishGuard_ProjectBrief_Client.docx` (sections 3–8). Originals remain private in Downloads. Existing decisions, source evidence, authorization, tests and Git history were reconciled with these documents. Their literature claims were read as manuscript claims, not independently reverified findings; retain the bibliography and verify each original paper before final submission.

| Status | Item | Exact evidence or missing evidence |
|---|---|---|
| Complete | Existing Python baseline independently rerun | `python -m unittest discover -s research/tests -v`: 30 tests, OK, before edits; updated verification in `verification-20260923.md` |
| Complete | Supplied package aggregate audit and source separation tooling | `dataset-audit.json`; `research/smishguard/audit_package.py`; frozen-byte recheck in current verification |
| Complete | Blinded packet preparation mechanism | `review_packets.py` restricts text release to verified redaction; `test_review_packets.py` tests hidden original labels/sources and withheld text |
| Complete | Experimental manual inference implementation | `SuppliedDetector.kt`, `CheckViewModel.kt`, `DevelopmentFlowTest.kt`; exact current API results in current verification |
| Complete | Disabled reporting and automatic-model warning policy | `Reports.kt:DisabledReportingRepository`, `IncomingSmsReceiver.kt`, `SuppliedModelTest.kt`; no INTERNET permission in manifest |
| In progress | Reproducible research workflow | LR/NB/SVM, split isolation, calibration and selection code exist; only software-fixture tests have run |
| In progress | Thesis Chapters 3–5 and defense package | Draft support and explicit placeholders in `thesis-drafting-materials.md` and `defense-materials.md`; no final results manuscript |
| Blocked | Xiaomi installation and carrier/device validation | User reports `secure_frp_mode=1`, setup/provisioning=1, restart ineffective; Xiaomi support pending; no phone installation attempted this session |
| Requires researchers | Dataset eligibility, redaction, independent annotations, acquisition lineage | `source-evidence.md`, `annotation-protocol.md`; no complete approved primary dataset |
| Requires researchers | Ethics evidence for new collection and consent forms | Chapter 1/brief require university ethics approval before collection; client go-ahead is a distinct recorded status |
| Requires researchers | Experiment matrix, checkpoints, thresholds, small-sample protocol | Five families in Chapter 1; transformer adapter exists but no vetted local checkpoints or valid comparisons |
| Requires researchers | Collection form, reporting service/dashboard and partner acceptance | Promised in manuscript/brief; a local readiness prototype now exists in `backend/README.md`; Android remains disconnected; endpoint, access, retention and operational governance unresolved |

## Scope inconsistencies requiring explicit resolution

1. Supplied export uses all 1,276 rows, mostly English. That is not a prospectively held-out Filipino/Taglish evaluation. The 1,205 nominal financial candidates include unreviewed records; 1,201 unique texts and 869 heuristic groups cannot establish the 1,200 eligible minimum. No collection target was lowered.
2. Supplied labels derive partly from source categories. Spam is not equivalent to financial impersonation; source overlap is not acquisition history. The 70 UCI rows remain supplementary, one explicit nonfinancial row is excluded from primary scope, and personal/social records remain held.
3. Chapter 1 promises calamanCy and word/character comparisons with LR, NB, SVM, XLM-RoBERTa and RoBERTa-Tagalog. Current supplied runtime is frozen Unicode word unigram/bigram LR; research baselines use ASCII preprocessing. These are different conditions. No transformer winner or calamanCy equivalence is established.
4. Chapter 1 promises calibrated warnings. The supplied score is uncalibrated and threshold 0.5 provisional. Automatic warnings remain disabled. Future warning policy requires reviewed evidence, not merely a passing build.
5. The brief promises voluntary reporting/dashboard and linkless counts. Reporting is disabled; nullable domain also means unreportable URL and cannot establish linklessness. Researchers/client must settle the data contract before implementation and turnover.
6. A participant-side redaction form is promised but absent. Do not describe the private coordinator packet workflow as that collection form. New collection must follow the manuscript's ethics/consent prerequisites.
7. Public dataset/model release is promised but rights and learned-token privacy remain unresolved. Release sanitized methods/templates now; do not release the supplied model, raw collection or letters.
8. Manuscript novelty statements such as “first” and broad absence-of-prior-work claims need a documented literature search. Chapter 2's “last five years” statement also needs qualification for older statutory sources. No novelty or causal policy claim is certified here.

Owners below are roles for the team to assign; no person has been assigned work or signed approval by this audit.

## Safe handoff reassessment

The local Flask prototype now exists and is tested; Android remains disconnected and all reporting deployment gates remain pending. Procedure-level model scripts and result tables are supplied. This closes the absence-of-methods-documentation gap, not prospective performance or calibration gaps. The evidence package's five-seed means and RF values conflict with its CSVs; its highest-CV-variability claim is contradicted by Naive Bayes. Inner CV pre-vectorizes outside folds, and tuning uses overlapping repeated splits. Researchers must reconcile run provenance and correct methodology before adopting definitive results.

Physical Xiaomi installation remains blocked by secure_frp_mode=1. Device SMS delivery, vendor battery behavior, usability, real-world performance, ethics/data rights, independent labels, manuscript scope alignment and partner acceptance remain unfinished. No FRP bypass, bootloader change, firmware flash or factory reset is part of this work. Approved Chapters 1 and 2 remain untouched; suggested wording belongs in the separate supporting document.

Current API 36 verification has unresolved large-font Settings and intermittent result-flow timeouts. API 26 focused checks passed; do not use that to erase API 36 failures. These software-test gaps are separate from secure-FRP physical testing.
