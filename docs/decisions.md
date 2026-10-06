# Scope and implementation decisions

## Sources read

Read the complete implementation-relevant text of `SmishGuardPH_Chapter1_Introduction_1.docx`, `SmishGuardPH_Chapter2_RRL_1.docx`, and `SmishGuard_ProjectBrief_Client.docx` from the user's Downloads folder on 17 September 2026. The documents were initially absent from the attachments and were subsequently supplied by path. They provide research/product context; the user's explicit milestone and privacy instructions govern implementation. The initial workspace contained only `.idea`; no working source, dataset, or model was found.

## Resolved conflicts and assumptions

| Source issue | Decision for this milestone |
|---|---|
| Brief calls a domain the part before the first slash | Use URI parsing and a conservative suffix policy, never slash splitting. Credentials, subdomains, and URL remainders never enter reports. |
| Brief promises a dashboard and frequently describes "scam" as fact | Dashboard remains a future deliverable. UI says potential impersonation and treats labels as judgments, not proof. |
| Chapter 1 mentions network blocking as a possible future policy use | The app never blocks, deletes, hides, writes, or sends SMS. No SMS provider access. |
| Documents describe direct installation as addressing app-store restrictions | Android's installer allowlist and runtime permission still apply. No safeguard bypass, installer spoofing, default-SMS role, or automatic permission grants. |
| Three languages versus objective shorthand “Filipino and Taglish” | Filipino, English and Taglish all remain in scope. No measured language coverage is claimed before a real model exists. |
| Chapter 1 mentions calamanCy tokenization and character features | Portable deployment begins with an explicitly versioned simple unigram tokenizer. Character feature comparisons are supported in Python. calamanCy is a later experimental preprocessing branch with its own parity/export work, not silently substituted as an equivalent implementation. |
| Five research model families vs first phone runtime | LR, NB and linear SVM comparison/export foundation implemented. Transformer comparison adapter/protocol retained separately; transformer phone export is deferred. No winner chosen. |
| Brief wants linkless report counts but the allowed contract permits only nullable domain | Null can mean linkless **or unreportable URL**. Backend documentation forbids equating null-domain counts with proven linkless counts. Changing the metadata contract requires a later research decision. |
| Raw messages must not be stored, while a research dataset must exist | App scanning and dataset collection remain separate. Python reads only independently consented, reviewed, redacted data. No app donation/collection flow exists. |
| Target of 2,500 and minimum 1,200 samples | Sourced to supplied Chapter 1 and a proposal feasibility table; formal applicability/approval and the financial-only interpretation are not established. The implementation guard remains unchanged pending a versioned decision. This is not a universal statistical minimum. See [source trace and mismatch](sample-size-provenance.md). |

## Architecture

Single Activity with Compose/Material 3, one ViewModel and StateFlow for transient session state, DataStore repository for three preferences, replaceable detector and reporting interfaces. No Room is needed because there is no persisted report/scan history. No analytics, crash reporter, WebView, cloud model API, network client, or INTERNET permission.

Android source lives under `android/`; Gradle root is Android Studio's project entry. Research tooling is under `research/`; documentation under `docs/`; future service scope under `backend/`.

The required 12ui design workflow was attempted. CLI installer returned Windows `spawn EINVAL`; direct CLI execution worked, but hosted draft required a separate account sign-in. No design was generated or claimed as approved. The implementation uses native Material 3 components, scrolling screens, system font scaling and light/dark color schemes. This external-service limitation does not block native development.

## Supplied-package milestone — 21 September 2026

The local user-supplied ZIP, CSV, guide and model were read, along with the thesis documents and existing decisions, before integration. Drive was not accessed. This supersedes the historical no-package assumption above. The raw package is preserved with SHA-256 hashes; private working copies are excluded from Git/source packaging.

The supplied full-dataset LR model uses Python Unicode word unigrams/bigrams, not the earlier ASCII unigram research baseline. Schema 2 preserves its parameters through explicit conversion and separates provenance, technical compatibility, evaluation, calibration and intended-use metadata. Its development-only build is experimental, unverified, uncalibrated and never approved for automatic warnings. The default debug build remains model-free. Compatibility tests do not establish research validity.

The package has 1,276 rows; primary-study eligibility is not yet verified and eligible counts are unknown. Project/client authorization is now recorded separately in project-authorization.md; source names alone are neither permission evidence nor grounds for rejection. UCI stays supplementary. Other sources require review under the primary protocol. No dates, approvals, labels or performance were invented. Retrospective refitting cannot make the supplied rows prospectively unseen. The research workflow therefore records data history, isolates groups and training preprocessing, freezes candidate selection before final testing, and keeps uncertain labels out of training.

Model vocabulary is learned content: the audit flags two numeric identifier-like terms for privacy review. Parameters were not silently edited to hide this. No message rows or guide reference texts are included in the APK. Physical-device work remains pending; it does not block emulator development.

## Client authorization clarification

The team reports authorization to proceed and supplied a signed client-request letter. Record that go-ahead without repeating the request. The letter supports the thesis/client arrangement, not blanket licensing or formal ethics clearance. The importer now assesses documented use and study role for each source, including aggregators, while retaining donation-consent, redaction and independent-label checks. App development/offline integration/emulator testing/evaluation tooling are not blocked by unresolved research eligibility. See project-authorization.md and source-evidence.md.

## Team clarification — 6 October 2026

Current research scope is **all SMS phishing**. This is a team scope clarification; no adviser approval is invented or assumed. Revised thesis title: **Pending finalization**. Preserve the existing manuscript title as historical and leave title-dependent edits pending. Continue documentation and validation independently of the title. The [scope record](scope-clarification-20261006.md) governs current research questions, objectives, methods, labels and discussion; older constraints above are historical.
