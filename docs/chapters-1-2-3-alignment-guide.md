# Chapters 1 to 3 alignment guide

Version 1, 7 October 2026. Read `thesis-system-memory.md` first. This guide distinguishes the implemented manual Android app, completed preliminary retrospective comparison and pending human/device research. Audited source: `e8a9d38fac9419e985b4b88404a5be48986fb036`, branch `codex/thesis-completion-package`, clean tracked intake. Final title and replacement app name are pending; no adviser approval is inferred.

## Manuscript availability and audit boundary

Local text inspected read-only: Downloads copies named `SmishGuardPH_Chapter1_Introduction_1.docx`, `SmishGuardPH_Chapter2_RRL_1.docx`, `SmishGuardPH_Chapter2_RRL.docx`, and `SmishGuard_ProjectBrief_Client.docx`; repository `docs/chapter-3-methods-draft-20261006.md`. The Chapter 2 variants differ in citations and wording; filename suffixes do not prove approval or authoritative version. The Chapter 3 Markdown file is a working methods draft, not proof of an approved university-format Chapter 3. No clearly identified final original Chapter 3 was established in this inspection.

A targeted paragraph-text alignment audit was performed on available Chapter 1/2 material and the methods draft. It is not a complete page/layout/comment/embedded-diagram audit, reference-authenticity review or certification that these are the team's latest chapters. When the user supplies Chapters 1–3, the receiving AI must compare those exact versions again, preserving their format. Local manuscript files remain private and unmodified. Only brief nonpersonal excerpts needed to identify inconsistencies are reproduced here.

## Chapter 1 treatment

Background should motivate SMS phishing across financial and nonfinancial themes. Distinguish phishing from generic spam/scams; sector or URL presence is not a label rule. Retain relevant financial literature as a subset. Contextual statistics, laws and causal claims need original-source verification; they are not established by this repository audit. Do not turn the retrospective model ranking into a Chapter 1 premise.

Problem statements should concern a bounded classification/evaluation problem: inherited labels, template overlap, source/language coverage, historical exposure and offline deployment. Avoid claiming that the implemented methods isolate genuine language understanding or causally measure every shortcut. The present study has no completed link/weak-model ablation establishing that claim.

Map objectives to actual evidence: offline single-message Android inference and separate four-model integration are implemented; the common retrospective experiment is completed but preliminary; independent review and prospective comparison are pending; physical acceptance awaits actual observations. Proposed scope-aligned questions in `docs/scope-clarification-20261006.md` are working questions, not approved substitutions. Quantization is a separate optional condition.

Keep a decision ledger for historical objectives. Mark each as retained/pending, proposed revision, or proposed limitation, and state adviser/team review required. Never silently remove an approved objective, convert an unperformed experiment to past tense, or describe its replacement as approved. Reconcile partner and collection-form obligations separately from current app completion.

Scope should identify Android API 26 minimum, manual paste/share, four separate private APK variants, offline inference, transient result preview and disabled reporting/warnings. Limitations must include inherited labels, 3,269/3,340 historical exposure, 439/448 exposed test records, source imbalance, rough language labels, mBERT prefix truncation, app abstention, lack of physical/human validation and pending privacy review. Broader intended scope does not mean every theme was adequately sampled.

Significance should express potential usefulness, not adoption, guaranteed protection, population-level prevalence measurement, production readiness or verified user trust. No-phishing output does not certify safety. Public dataset release and ordinary-phone performance cannot be claimed from private source evidence and emulator tests.

## Chapter 2 treatment

Literature should support: SMS phishing mechanisms and multilingual/code-switching challenges; imbalanced text classification; unigram TF-IDF, Logistic Regression, Multinomial NB and Linear SVM; multilingual BERT/WordPiece and offline ONNX deployment; template/near-duplicate leakage, historical exposure and source shortcuts; blinded annotation, uncertainty, agreement and adjudication; calibration versus probability validity, validation threshold selection, AP versus trapezoidal PR-AUC, precision/recall/FPR, bootstrap uncertainty; abstention/coverage; privacy and accessible mobile interaction; retrospective versus prospective evaluation and emulator-versus-phone benchmarking.

Keep XLM-R, RoBERTa-Tagalog, calamanCy, character features and URL ablations where relevant as prior work, alternatives or unperformed objectives. They must not appear in a diagram or methods claim as components of the current four-model implementation. The current domain sanitizer is optional reporting metadata, not a separate trained URL-analysis branch, reputation service or ablation result.

Separate every prior-work result from this study's own results. “Not reported in the publication reviewed” is different from “not done.” Do not invent a gap, citation, quotation, novelty priority or numerical comparison. Unqualified “first” and “no Philippine study” claims need a documented literature search. Preserve valid citations and academic voice while marking unsupported claims `[REFERENCE VERIFICATION REQUIRED]` or `[GAP CLAIM REQUIRES EVIDENCE]`.

Reference review is pending. Check each cited original publisher/paper for authors/year/title/DOI, task/dataset/language and the exact claim/page. In particular, verify the XLM-T/Barbieri citation's relationship to XLM-R, the AmericasNLI transfer claim's applicability to SMS, Mishra/Soni date differences across Chapter 2 versions, reported Philippine-study metrics, Whoscall press counts and legal wording. These are verification targets, not findings that the references are false. No external publications were consulted for this package and no new citations are supplied.

## Chapter 3 treatment

Use past tense for documented retrospective procedures and engineering checks, present tense for current system behavior, and future/conditional tense for pending human/device work. Distinguish a prepared protocol from its execution. The existing 6 October methods draft is largely aligned but should gain current architecture detail, model-specific decision policies, remaining defects and 7 October audit boundaries.

Describe: Compose/ViewModel/DataStore architecture; manual/share/session-clearing paths; permissions and disabled modules; common minimized input, ASCII TF-IDF versus cased WordPiece; grouping at SequenceMatcher >=0.85 with supplied-template unions; actual partition counts/seed; training-only grouped parameter selection; separate calibration and validation threshold roles; mBERT fixed training configuration; JSON and float32 ONNX export; identical held-out test IDs, metrics and group-bootstrap method; classifier versus app-coverage reporting; host/JVM/emulator checks and pending physical acceptance. Explain that genuine algorithm differences survive the common linear export.

Record the actual source-supported cohort and holds, inherited label origin, source imbalance and exposure. Do not describe the supplied CSV audit as original raw collection reproduction. Distinguish current broad eligibility from historical exclusions. Proposed collection targets from Chapter 1 are not achieved sample-size calculations or inferential guarantees.

Describe independent annotation/adjudication and prospective evaluation as prepared/pending: actual reviewer qualifications/attestations, privacy review, returns, agreement, collection dates/cohort and device observations require supplied evidence. The prospective freeze preserves models/thresholds; no test-driven retuning is permitted. Do not transplant fictional fixture reviewers or demonstration messages into participant/results tables.

Keep detailed outcome tables and model rankings in Chapter 4 unless the university's format explicitly requires otherwise. Chapter 3 may contain design facts such as partition counts, fixed training settings and metrics definitions. Neither the packaging shrinkage nor INT8 results change the original float32 comparison. No production/network deployment or approved live warnings were performed.

## Alignment table

All paths below are repository-relative evidence locators. The facts column is self-contained for readers without repository access.

| Chapter/section | Current system fact | Evidence | Required manuscript treatment | Unresolved decision |
|---|---|---|---|---|
| 1 Background/problem | Current definition covers deceptive SMS across sectors, with or without URLs. | `docs/scope-clarification-20261006.md`; `docs/sms-labeling-guide-20261006.md` | Broaden financial-only framing; distinguish phishing from generic spam. | Team/adviser reconciliation of approved scope. |
| 1 Objectives/questions | LR/NB/SVM/float32 mBERT retrospective comparison exists; independent-cohort questions remain pending. | `docs/four-model-comparison-20261005.md`; `docs/review-completion-20261006.md` | Map each objective to implemented, preliminary or pending evidence. | Adopt/revise working questions through actual review. |
| 1 Historical objectives | Extra transformers, character/link controls and random-vs-group comparison are not established as completed. | `docs/thesis-gap-analysis.md`; `docs/module-completion-matrix.md` | Preserve objective history; propose revisions/limitations explicitly. | Retain and perform, or formally revise. |
| 1 Scope/app | Manual entry/paste/share, offline, separate APKs; no scan history; warnings/reporting disabled. | `android/app/src/main/java/ph/smishguard/MainActivity.kt`; `docs/privacy.md` | Describe actual milestone and transient preview; correct stale privacy prose. | Historical reporting/partner obligations. |
| 1 Significance | Intended beneficiaries exist; no real-user adoption/phone acceptance established. | `docs/app-completion-audit.md`; `docs/physical-device-checklist.md` | Use potential benefits, bounded demonstration claims. | Actual user/partner acceptance. |
| 1 Limitations | Labels inherited; 439/448 test records historically exposed; source/language support limited. | `docs/expanded-four-model-results-20261005.json` | Explain validity limits, avoid general winner/probability claims. | Future independent cohort. |
| 2 Algorithm literature | Actual baselines use unigram TF-IDF; transformer is mBERT with WordPiece. | `research/smishguard/expanded_train.py`; `research/smishguard/linear_export.py` | Support actual choices; retain other algorithms as related work. | Verify original citations. |
| 2 Gap/framework | No completed causal shortcut/ablation evidence; no certified novelty search. | `docs/thesis-gap-analysis.md`; current manuscript excerpts below | Narrow unsupported claims; separate proposals from implemented framework. | Scope/objective and literature review. |
| 2 Calibration | Sigmoid fitted on calibration; validation F1 chooses thresholds; scores remain experimental. | `docs/expanded-comparison-protocol-20261005.md`; `model/ResultCopy.kt` under main Kotlin package | Explain calibration limitations, not verified real-world probabilities. | Independent calibration evidence. |
| 3 Architecture/modules | Kotlin/Compose app with ViewModel transient state, three DataStore preferences, local CPU inference. | `android/app/build.gradle.kts`; `CheckViewModel.kt` and `SmishGuardApp.kt` under main Kotlin package | Include actual screens/data flow, permissions and error/lifecycle behavior. | Native timeout/retry and device acceptance. |
| 3 Dataset | 3,552 supplied included; 3,340 used; 212 held; historical exclusions preserved. | `docs/four-model-comparison-20261005.md`; `docs/source-evidence.md` | Show counts, label origins, eligibility and privacy/source holds. | Human review and 18 scope conflicts. |
| 3 Splits | 1,860/622/410/448 train/validation/calibration/test; 1,848 label-blind groups, seed 20260929. | `docs/expanded-comparison-protocol-20261005.md`; `docs/expanded-four-model-results-20261005.json` | Distinguish group separation from historical independence. | No fresh-cohort claim. |
| 3 Training/export | Training-only 5-fold AP search, calibration once, validation F1 thresholds; float32 ONNX mBERT. | `research/smishguard/expanded_train.py`; `docs/expanded-comparison-reproduction-20261005.md` | Describe exact methods and frozen IDs; do not claim exhaustive tuning. | Optional INT8 is separate. |
| 3 UI/policy | >= .82/.63/.59/.8899999999999999; help wrongly says strict >50%; mBERT prefix 158 tokens. | `model/Detector.kt`, `MainActivity.kt`, mBERT `BertWordPiece.kt`; `docs/app-completion-backlog.md` | State actual rule and disclosed defects; don't rewrite code behavior as fixed. | Engineering acceptance B1–B3. |
| 3 Evaluation | Common 448-record preliminary test; conditional group bootstrap and coverage accounting. | `docs/expanded-four-model-results-20261005.json` | Methods here; detailed outcomes in Chapter 4. | Independent/prospective validation. |
| 3 Testing | Host/JVM and API36 emulator evidence; latest host run skipped four private parity tests. | `docs/app-completion-audit-evidence.json`; `docs/expanded-four-model-verification-20261005.json` | Attribute dates/environments; skips are not passes. | Target physical phones and minimum-API checks. |
| 3 Human methods | Blinded packets/prospective tooling exist; zero actual final decisions in latest evidence. | `docs/review-completion-20261006.md`; `docs/prospective-validation-plan-20261006.md` | Future/conditional tense and explicit evidence placeholders. | Real reviewers, intake and device returns. |
| All Identity/approval | SmishGuard working name; final name/title pending; team scope instruction isn't adviser approval. | `docs/scope-clarification-20261006.md` | Preserve historical title; placeholders for revised wording. | Team supplies final wording/approval record. |

## Specific paragraph inconsistencies

These are text anchors, not page numbers. Search within the indicated heading in the actual supplied version. Excerpts are short identifying quotations; surrounding claims must also be reviewed.

| Local file and heading | Short excerpt | Evidence-based treatment |
|---|---|---|
| Chapter1_Introduction_1, Background and Rationale | “pretends to be a bank or an e-wallet” | Definition is too narrow for current scope; financial impersonation is an example. |
| Same, Background and Rationale | “No Philippine study has checked for either problem” | Unsupported exhaustive gap claim; verify literature and qualify by reviewed publications. |
| Same, General Objective | “imitate banks and money services” | Propose broad-phishing wording, preserving original objective in decision log. |
| Same, Specific Objectives | “against two newer language models, XLM-RoBERTa and RoBERTa-Tagalog” | Actual fourth model is mBERT; substitution requires explicit objective reconciliation. |
| Same, Specific Objectives | “comparing the result against a plain random division” | Grouped split exists; random-versus-group outcome not established as completed. |
| Same, Specific Objectives | “training three deliberately weak models” | No completed weak-control/link-ablation study established; retain pending or propose reviewed revision. |
| Same, Significance, Partner Local Government Unit | “receives a dashboard” | Local prototype exists; deployment, Android reporting and partner receipt/acceptance are unverified. |
| Same, Significance, Filipino Language Technology Researchers | “releases a cleaned Taglish collection” | Public release is not established; private provenance/privacy/distribution constraints remain. |
| Same, Scientific Contribution | “the first measurement” | No verified priority/novelty evidence or completed causal shortcut measurements. |
| Same, Scope of the Study | “a form that removes personal details on their own phone” | Coordinator intake is not the promised participant-side form. Reconcile requirement. |
| Same, Scope of the Study | “The target is 2,500 messages” | Historical target differs from 3,552 supplied/3,340 eligible; do not retrofit an achieved power calculation. |
| Same, Scope of the Study | “with calamanCy” | Current baselines use ASCII token normalization; mBERT uses WordPiece. Retain calamanCy as prior work only unless performed. |
| Same, Scope of the Study | “reads incoming text messages and scores each one” | Current models disable automatic inference/warnings; manual/share is actual workflow. |
| Same, Scope of the Study | “the application sends only the domain” | Android sends nothing; describe disabled interface and separate backend prototype. |
| Same, Practical Contribution | “run on an ordinary phone” | Offline emulator execution is established; physical-phone evidence remains pending. |
| Chapter2_RRL_1 and Chapter2_RRL, discussion of message/link evidence | “This study follows the same idea” | No separate trained link-feature branch or performed link ablation; qualify proposed versus performed. |
| Chapter2_RRL_1, Synthesis and Research Gap | “focused on messages that imitate banks and money services” | Broaden current scope, retaining historical cohort restriction as limitation. |
| Chapter2_RRL_1, annotation discussion | “reports a chance-corrected agreement score” | Agreement workflow prepared; no actual independent-return agreement result established. |
| Both Chapter 2 versions, Conceptual Framework | “Each weak model is designed to fail” | Proposed control framework differs from actual frozen four-model experiment; require decision, not fictional outcomes. |
| Chapter2_RRL_1, opening paragraph | “All sources reviewed here were published within the last five years” | Check date policy/exceptions; the manuscript also refers to the 2012 privacy law. Do not delete relevant foundational sources mechanically. |
| Methods draft 3.7 | “completed minimalist UI” | Layout exists; add scope-copy, threshold-help, truncation-disclosure and recovery defects so “completed” does not imply all acceptance passed. |
| Methods draft 3.7 | “no quantization or replacement was introduced” | Correct for frozen four-model float32 comparison; add that a later separate INT8 condition exists. |
| Methods draft 3.8 | “prepared, not completed” | Preserve this distinction; do not fill brackets with fictional reviewer/phone findings. |

## Decision and evidence checklist for revision

- Select the authoritative Chapter 2 version and supply the intended final Chapter 3/university template.
- Confirm exact final title/name; keep placeholders until then.
- Reconcile each historical objective and partner/form/release commitment with the team/adviser. List proposed wording and rationale; never assert approval.
- Request only missing evidence relevant to a claim: actual reviewer returns, consent/use/privacy records, prospective cohort and phone observations. Absence stays explicit.
- Maintain source-to-claim traceability, classify the claim status, and separate completed methods from planned work in every chapter.
- Preserve valid citations and numbering; original-source reference checks remain a separate unfinished task.
- Keep Chapter 4 outcome tables out of Chapter 1. No performance winner, calibrated-probability guarantee, enabled warning/reporting or all-device claim.
- Deliver revised chapters plus a change log with original heading/short excerpt, change, reason/evidence, status and unresolved decision. Record objective changes separately for adviser review.
