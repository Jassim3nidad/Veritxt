# SmishGuard app completion audit

Audit date: 7 October 2026. Audited source commit: `680b36fdf79ddcd58cc618346b8daf429a314af2`, branch `codex/thesis-completion-package`. The tracked worktree and index were clean at intake. Ignored private assets, APKs, datasets, build outputs and earlier logs were present; clean Git status does not mean they were absent. No production source, model, threshold, split or existing result was edited for this audit.

**The evidence supports “approximately 80% of app implementation is complete” as a conservative progress statement. It does not support “the thesis is 80% complete,” “80% validated,” or a precise measured 80%.** This requirement-based audit estimates **90.5% core implementation (communicate as about 90%)** and **64% verification readiness (about 65%)** for the current offline manual-app milestone. Those are judgment-based audit indices, not accuracy, test-pass rates, remaining effort forecasts or statistical estimates. The visual design and major flows exist; several user-facing acceptance criteria and device checks remain open.

The [module matrix](module-completion-matrix.md) inventories implementation and verification separately. The [backlog](app-completion-backlog.md) specifies defects, acceptance criteria and team inputs. A [short adviser statement](adviser-progress-statement.md) is ready to use. Fresh aggregate evidence is in [app-completion-audit-evidence.json](app-completion-audit-evidence.json).

## Governing requirements and boundaries

Precedence is this audit request, the team's [6 October scope clarification](scope-clarification-20261006.md), the current [review-completion workflow](review-completion-20261006.md), dated Chapter 3/4 drafts and implementation, then historical requirements. Read the original private `SmishGuard_ProjectBrief_Client.docx` and Chapter 1 objectives/scope in Downloads, plus the repository requirements matrix, decisions, project authorization, minimalist design record, completion status, verification and packaging reports. Original manuscript factual/literature/legal claims were treated as requirement context, not independently certified by this software audit.

| Area | Current audit requirement | Superseded or unresolved material |
|---|---|---|
| Core Android app | Offline single-message entry/paste and Android plain-text share, four separately installed model variants, truthful experimental results, local preferences, transient message handling, usable navigation/accessibility, error states and installable private demo APKs | Shared features count once. There is no requirement for a combined model switcher, cloud inference or four independent apps. |
| Subject scope | All SMS phishing, including financial and nonfinancial themes; Filipino, English and Taglish remain relevant | Financial-only wording/exclusions do not govern new work. Expanded scope does not establish trained coverage. No adviser approval is inferred. |
| History | No scan/message history; retain only the current result session and three preferences | Absence of a History screen/database is intentional privacy behavior, not missing work. |
| Automatic SMS and reporting | Disabled for the current manual milestone; inspect safeguards and separately inventory existing optional plumbing/backend | Original brief promises incoming warnings and partner dashboard access. They remain a thesis/turnover reconciliation issue, not deductions from this app denominator. Latest instructions do not establish cancellation of every original partner commitment. |
| Models/research | LR, Multinomial NB, Linear SVM and float32 mBERT are the frozen four-model comparison | Historical LR, LR candidate, folded LR4 and INT8 mBERT are separate conditions. INT8 is not a replacement fourth model. Independent labels, fresh evaluation and calibration validity belong to research. |
| Thesis | Current methods/results drafts and reproducible evidence, with actual human findings inserted only when received | Revised thesis title and replacement app name are pending. Older XLM-R/RoBERTa-Tagalog, calamanCy, character/URL-ablation objectives, participant-side form and partner turnover need explicit manuscript reconciliation; they are not silently declared completed or mandatory app modules. |
| Deployment | A private development-signed thesis demonstrator | Production signing/distribution, backend hosting and warning approval are later deployment work. API 26 minimum is a build contract, not proof all current variants run on every API 26 phone. |

The scope assumption underlying the number is therefore explicit: **the current offline manual Android milestone**, not all original research/partner promises. Reintroducing live reporting or automatic warnings requires a new denominator. Renaming is blocked on the team's chosen name, but scope copy can be corrected without waiting for it. No new approval request is necessary to continue already authorized development.

## Scoring method defined before aggregation

Weights reflect importance to the agreed app: inference and truthful results receive more weight than navigation or packaging. They do not depend on file counts, test counts or the desired 80% result. Runtime loading and variant identity are distinct: the former covers the shared execution service; the latter covers correct algorithms, exports and deployment separation. Privacy storage and lifecycle similarly distinguish persistence policy from cancellation/recovery.

Implementation factors: **1.00** means the scoped subfeatures exist and source/evidence reveals no material missing behavior; **0.75** means the principal flow works but a material acceptance slice remains; **0.50** means a substantial integration is missing; **0.25** means scaffolding only; **0** means missing. A pending device test alone does not reduce implementation. External inputs and out-of-scope work are identified separately. Factors express functional coverage, not estimated coding hours.

Verification factors: **0** no evidence; **0.25** source/static evidence; **0.50** host/fixture evidence or incomplete acceptance checks with a known unresolved gap; **0.75** relevant artifact-linked emulator/packaging evidence, with physical/user acceptance pending; **1.00** agreed acceptance demonstrated on the target physical configuration and, where applicable, by human usability review. A higher-level test does not erase a known acceptance gap. Broad accessibility remains 0.50 because automated reachability covers only a narrow subset. This intentionally prevents emulator passes from being represented as phone or human validation.

| Required module | Weight | Implementation factor | Earned implementation | Verification factor | Earned verification | Reason and evidence |
|---|---:|---:|---:|---:|---:|---|
| C1 Onboarding, Home and navigation | 8 | 0.75 | 6.00 | 0.50 | 4.00 | Routes and minimalist design work; financial-only copy contradicts current scope. MainActivity, minimalist screenshots, FlowsTest. |
| C2 Entry, paste and transient result preview | 8 | 1.00 | 8.00 | 0.75 | 6.00 | Editable input, clear, loading state and exact submitted preview; flow/lifecycle emulator evidence. Model-specific truncation is charged to C4. |
| C3 Android share-to-app | 6 | 1.00 | 6.00 | 0.75 | 4.50 | ACTION_SEND text/plain, new-intent route and payload cleanup; FlowsTest and offline reports. |
| C4 Preprocessing and input validation | 10 | 0.75 | 7.50 | 0.50 | 5.00 | Empty/random/OOV/length handling exists; mBERT silently truncates its token window. Assessability, BertWordPiece, parity tests. |
| C5 Model loading and offline inference | 15 | 1.00 | 15.00 | 0.75 | 11.25 | Real private assets, background load, model guards, missing/invalid states and offline execution. APK hashes/parity match. Failure recovery is charged to C9. |
| C6 LR/NB/SVM/mBERT identity and integration | 12 | 1.00 | 12.00 | 0.75 | 9.00 | Three genuine classical exports plus real float32 mBERT, distinct packages; identity guards and actual-export parity. |
| C7 Results, score and policy explanation | 12 | 0.75 | 9.00 | 0.50 | 6.00 | Decisions and exactly-once calibration follow artifacts; universal strict-50% help text is false for current variants. |
| C8 Preferences, privacy and permissions | 10 | 1.00 | 10.00 | 0.75 | 7.50 | Preference-only storage, session clearing, backup/screenshot restrictions, no INTERNET and disabled reports; tested emulator policy. |
| C9 Error handling and lifecycle recovery | 8 | 0.75 | 6.00 | 0.50 | 4.00 | Ordinary cancellation/recreation works; native inference lacks a proven hard deadline and cached load failures lack in-process retry. |
| C10 Accessibility and responsive layout | 6 | 1.00 | 6.00 | 0.50 | 3.00 | Scroll/IME/insets, headings, live region, touch targets and font scaling implemented; limited emulator evidence, no TalkBack/human acceptance. No broader layout defect asserted without reproduction. |
| C11 APK packaging and build tooling | 5 | 1.00 | 5.00 | 0.75 | 3.75 | Pinned wrapper/build, private asset gates, source-only packaging and signed APKs exist. All audited APK signatures/hashes verified; current isolated build checks pass. |
| **Total** | **100** | | **90.50** | | **64.00** | Research, thesis, historical variants and future services excluded. |

Calculation: implementation = sum(weight × implementation factor) / 100 × 100 = **90.5%**. Verification uses the same formula with its own factors = **64%**. Four partial modules account for 9.5 implementation points withheld; no missing required top-level module was discovered. Changing a factor by one 0.25 step changes its contribution by weight/4: these subjective boundaries justify “about 90%,” not reporting 90.5% as scientific precision. There is no evidence-based single percentage for the whole thesis while its objective reconciliation and human findings remain open.

## Completed modules and completed subfeatures

“Verified” here always means the named environment and acceptance slice, not global completion on physical phones.

- **Manual entry/paste and submitted-message preview (C2):** `CheckViewModel.edit/scan`, `MainActivity` input/result route; `FlowsTest`, `CompactResultTest`, `PrivacyLifecycleTest` and API 36 reports exercise clear, submit, another-message and preview lifetime.
- **Android share (C3):** manifest share filter, `consumeShare/onNewIntent`, ViewModel share; plain-text emulator flow exercised and extras/ClipData discarded. No SMS permission needed.
- **Offline loading and inference (C5):** `SmishGuardApp.detector`, bounded metadata load, model-specific parsers and ONNX CPU runtime; current files and APK assets match the frozen manifest. Offline emulator verification exists for each variant.
- **All four model integrations (C6):** `linear_export.py` and Android linear scoring preserve LR, NB and SVM identity; `MbertDetector` uses a pinned multilingual BERT ONNX model. Baselines have 461 reference cases each; mBERT has 468. They are not renamed LR clones or mocked results.
- **Preference storage, privacy and permission controls (C8):** DataStore saves onboarding, SMS consent and manually selected city; messages/results remain in memory; reset, permission denial and lifecycle cleanup exercised. Five APKs independently rechecked without INTERNET permission. No history is expected.
- **Accessibility implementation (C10):** scrollable Compose layouts, labeled controls, semantic headings/live result region, minimum targets, font scaling and light/dark themes exist. API 36 large-font/320 dp tests are bounded verification, not human usability acceptance.
- **Private demo packaging/build tooling (C11):** three approximately 12.94 MB classical APKs, 800.41 MB repackaged float32 mBERT, guards, signatures and reproduction instructions exist. The historical 1.51 GB mBERT APK is retained separately.
- **Within partial modules:** Home/Settings/Check navigation and minimalist styling work (C1); abstention/character limit and export preprocessing work (C4); headings/one-decimal scores/classification and once-only calibration work (C7); ordinary loading/error states and session clearing work (C9).
- **Outside the app percentage:** local Flask report ingestion/dashboard passes 46 current fixture tests; research training/export/evaluation/review tooling exists, with a completed retrospective experiment. Neither fact completes Android reporting or independent research validation.

## Traced implementation and defects

### Manual and shared text to a result

`MainActivity` creates the Compose shell under `FLAG_SECURE` with saved-state storage disabled. Onboarding goes through DataStore; Home/Check/Settings are real routes. RESULT is an enum member handled by the Check/result branch; `scan()` deliberately uses CHECK with a non-null result, so a separately navigated RESULT screen is unnecessary. REPORT is reachable from the result explanation, including unavailable results; its submit button is deliberately disabled and its callback is empty. No enabled placeholder control or TODO that blocks a required manual flow was found in the inspected production paths.

The Android share filter accepts only `ACTION_SEND` with `text/plain`. `consumeShare` removes payload extras and ClipData, then `vm.share` clears the old session and populates Check. The regular multiline field supports system paste; there is no special clipboard uploader or READ_SMS inbox path. `edit()` limits input to 10,000 Kotlin string units and warns when extra text is removed. Blank input produces Unable to assess without a fabricated score. Busy checks disable repeated submission; `scan()` dispatches model work off the UI thread, retains a result-only message snapshot and clears editable text. Clear, another-message, navigation, background and recreation discard the snapshot. Closing the explanation alone leaves the active result visible, as intended.

**F1 — confirmed scope-copy defect:** `MainActivity.kt:119` still describes financial-institution impersonation; line 129 calls the input a financial SMS. These strings conflict with all-SMS-phishing scope. The minimalist layout is implemented, but its content is not fully current. Historical notification titles and optional financial-brand choices also remain financial-specific; they matter if those future paths are enabled.

### Model identity, transformation and decision

`SmishGuardApp` selects the detector by build type. Classical variants load `ComparisonDetector` and schema-1 `LinearDetector`; development loads the historical supplied Unicode LR; LR candidate/folded builds have their own parser contracts. Public debug intentionally contains no trained model. `mbert`/`mbertQuantized` load the ONNX detector by reflection from their variant sources.

The classical exporter inspects the actual scikit-learn class. LR uses fitted coefficients/intercept; NB exports the difference in class feature log probabilities and class log priors; Linear SVM exports its separating margin. All use the exported training-derived TF-IDF/L2 representation. The common runtime is mathematically appropriate for these distinct models. It applies `sigmoid(a × margin + b)` once, then the serialized threshold. `ComparisonDetector` adds abstention/manual-only flags, not another calibration pass.

mBERT verifies schema/base revision/class ordering/tokenizer/precision and hashes, copies the ONNX weights to no-backup storage, opens a CPU session and supplies IDs/mask/type tensors. It transforms the positive-minus-negative logit with the saved sigmoid once. Folded LR4 explicitly forbids extra calibration fields and uses the already folded parameters; candidate LR applies its separate calibration once. Fitted calibration is implemented; independent calibration validity remains unestablished.

| Current frozen variant | Actual model | Decision rule | Research status |
|---|---|---|---|
| LR | LogisticRegression export | score >= 0.82 | Preliminary retrospective |
| NB | MultinomialNB log-odds export | score >= 0.63 | Preliminary retrospective |
| SVM | LinearSVC margin export | score >= 0.59 | Preliminary retrospective |
| mBERT | Pinned bert-base-multilingual-cased, float32 ONNX | score >= 0.8899999999999999 | Preliminary retrospective |
| INT8 mBERT, optional | Same fitted reference, separate dynamic-quantized condition | Same serialized mBERT threshold | Experimental quantization; excluded from four-model count |

**F2 — confirmed explanation defect:** `MainActivity.kt:223` says “strictly above the unchanged 50% threshold” for every result. That is wrong for all four current variants, including equality semantics. `ResultCopy.heading` correctly uses the detector decision and `score()` formats one decimal; no evidence of a current decision/calibration arithmetic defect was found. The eventual fix should derive help text from the active policy, without changing frozen thresholds or deciding from the rounded percentage.

**F3 — confirmed long-input disclosure gap:** `BertWordPiece.kt:56` uses `ids.take(maxLength-2)`. Current metadata fixes max length at 160, leaving 158 content tokens. The UI still presents a 10,000-character allowance and the whole checked message with no token-window notice. A tail beyond the model window cannot affect logits. This is faithful export behavior, not evidence of a broken ONNX conversion, but users cannot tell which portion was assessed. The existing private training-length aggregate records 67/1,860 examples truncated at the selected length; it is not a new accuracy result. Preserve the frozen window and disclose the limitation; windowing/retraining is a separate research change.

Input assessment rejects blank, number-only, links-only, placeholder-only, obvious keyboard-mash and vocabulary-unsupported text. It accepts a short known meaningful word; it is not a semantic detector of every possible random string. Current baselines use ASCII normalization. mBERT uses a cased WordPiece tokenizer after redaction, but its assessability gate still uses the baseline ASCII/vocabulary policy. Meaningful unsupported text may abstain; that is not a correct negative and does not prove comprehensive Filipino or all-theme coverage.

### Privacy, permissions and lifecycle

DataStore holds only three preferences. No scan table, raw-message upload, analytics or crash-reporting service was found. Manifest has RECEIVE_SMS and POST_NOTIFICATIONS, optional telephony, no INTERNET/READ_SMS/SEND_SMS, backup disabled and recents exclusion. The mBERT no-backup model cache is persistent model data, not message history; preference reset does not remove that cache or revoke Android permissions. `SafeDomain` builds conservative metadata only; experimental/synthetic results cannot become `ReportPayload`s. Reporting repository always returns unavailable. The UI's report route does not transmit or queue.

Optional SMS plumbing can receive/decode new messages after consent/permission, but every production detector keeps `automaticWarningsAllowed=false`; it stops before automatic inference/warning. Thus “automatic warnings disabled” must not be embellished as “the receiver cannot receive any text.” Modem/notification tests include synthetic fixtures, not an approved live detector. No missing automatic-warning feature is charged to the current manual-app score.

Lifecycle cleanup is intentional privacy behavior, not recovery of a previous message. Tests cover ordinary background/recreation, navigation and the previously fixed delayed-model-status race. No physical process-death/low-memory acceptance is recorded.

**F4 — bounded recovery weakness, source-confirmed mechanism; slow-device outcome not reproduced:** ViewModel wraps work in `withTimeout(7000)`, while ONNX `session.run` and parts of loading are synchronous. The timeout is not evidence of a hard seven-second native execution bound. Historical common-session mBERT cold detector loading was about 8.24 seconds; this is a reason to test cold interactions, not proof that the UI timed out. Lazy loader catches initialization exceptions into a cached MissingDetector; repeated Check cannot reconstruct it within that process. A corrupted existing cache is hashed/rejected but not automatically replaced. Ordinary error screens work; controlled delayed-inference, failed-copy/cache and fresh-process recovery checks remain needed. Do not claim a reproduced crash or stale-result disclosure from this inspection.

### Accessibility, layout and packaging

The minimalist theme and spacing match saved screenshots. Reviewed the historical main-screen montage, large-font result screenshot and current expanded LR result screenshot with fictional content. The large-font image is scrolled to its return action; a clipped heading in that scroll position is not by itself proof of an inaccessible layout. Existing tests establish selected target sizes/semantics/reachability and 200% font behavior. They do not establish TalkBack reading order, human comprehension, landscape/tablet/RTL or all four phones' long-result usability.

Build stack pins JDK 17, Gradle 8.13 and Android configuration; min SDK 26, target/compile 36. Gradle guards reject missing or mismatched private models; mBERT requires ONNX Runtime. Packaging scripts audit private assets and excessive ZIP gaps. Development variants are debug-signed and coexist via distinct application IDs. Public source can build the model-free debug app; trained variants require private assets. This is documented reproducibility with private inputs, not an independently reproduced public research model or a demonstrated bit-for-bit deterministic release.

## Evidence currency and checks performed

**Fresh checks, 7 October, Windows/JDK 17/Python 3.12 host:**

- Rehashed all 23 entries in the frozen manifest: all present and matching, including four fitted asset sets, research freeze records, listed scorer sources and protocol/dependency files.
- Rehashed five preserved APKs: LR/NB/SVM, original expanded mBERT and repackaged mBERT. All match previous aggregate records; each packaged asset matches its current variant source asset. APK signature verification passes for all five; `aapt dump permissions` confirms no INTERNET permission.
- Rehashed the prepared A/B annotation, prospective-intake and physical-phone workbooks: all four match the previously verified blank versions. Current prospective CSV contains zero rows; the local final-review summary records zero final decisions and 3,340 pending. Returns held outside this repository were not available to audit.
- Ran current `:app:testMbertUnitTest :app:lintMbert` with output redirected to a new ignored audit build directory: 21 tests reported, **17 passed, four skipped**, zero errors/failures; lint zero errors/fatal issues, five warnings. Skips are private candidate/folded/comparison/mBERT parity configurations, not passes. Existing private parity results were not overwritten.
- Ran the latest review-completion test file: **11 passed**, fictional temporary cohorts/reviewers only. Ran backend in its own environment: **46 passed**, temporary database only. No real labels, records, training or fresh-cohort predictions were created.
- No adb device or emulator was attached. No fresh connected/instrumentation or physical-phone run is claimed. Reused bounded valid evidence instead of relaunching full suites or retraining.
- Initial audit-only build redirection used an incorrect Gradle property and failed at configuration; corrected the temporary init script. Initial backend invocation used the research environment without Flask; reran successfully in `backend/.venv`. These were audit harness/environment errors, not production regressions. Both initial logs remain in ignored audit output.

The tests and artifact inspection are recorded as aggregates in the new evidence JSON; detailed fresh logs/helper scripts/XML are private under `output/completion-audit-20261007/`. Current lint warnings are target/dependency currency notices, not proven runtime defects. This audit did not update dependencies.

**Reused evidence and its limits:**

| Evidence | What remains valid | Currency/limit |
|---|---|---|
| [Expanded four-model verification](expanded-four-model-verification-20261005.json) | API 36: 25 specialized checks per baseline, 24 for mBERT; actual-model parity and fixture-storage checks | Exact preserved APK/model hashes now rechecked. Historical run, not rerun today. |
| [Validation-stage verification](validation-stage-verification-20261006.json) | 800.41 MB mBERT package, 160 byte-identical referenced entries, 468 parity cases/zero class changes, 24 emulator checks | New hash matches actual file. Five current files/variants are available locally, not published here. |
| [Completion engineering](completion-engineering-verification-20261006.json) | INT8 experiment, 95 research software tests, 13 actual-scorer synthetic probes, float32 host regression | Later commit adds INT8 dispatch/precision guards. That host regression is JVM, **not** a new float32 emulator run. |
| [Minimalist redesign](minimalist-redesign.md), [API 36 reliability](api36-reliability.md) | Shared UI/lifecycle/font tests and historical resolved races | Screenshots/tests from earlier versions; relevant source inspected, no new user study. |
| [API 26 report](api26-results.json), comparison LR API26 report | Focused historical development/LR compatibility | Does not certify current expanded NB/SVM/mBERT on API 26. |
| [Remote phone guide](remote-phone-test-20261006.md) | Prepared protocol and blank form | No completed returns. Xiaomi FRP blocker is previously reported, not re-diagnosed today. |

Compared `f4fd8d1..680b36f`: only Android build configuration, SmishGuardApp dispatch and MbertDetector precision handling changed, to add the isolated INT8 variant. UI and baseline scorer sources remain unchanged. Preserved shipped APKs predate that source change; they are **not falsely identified as fresh builds from audited HEAD**. Existing APK tests support those exact artifacts; fresh isolated host checks support HEAD compilation and unit behavior. Exact-HEAD device regression is still a verification task before a new handoff.

## Research and thesis status outside the app percentage

**Model/research validation: partially complete.** Four models were genuinely trained/exported/evaluated on a common 3,340-record retrospective cohort with 448 test records; parity, timing, calibration diagnostics, uncertainty and subgroup tooling/results exist. Current evidence reports 439/448 test records with historical overlap; the other nine are not certified unseen. Labels are inherited/source-rule based. Prepared 3,340-row A/B packets have zero completed human decisions in the latest records; prospective intake and phone forms have zero observations. This audit found no newer completed-return evidence and did not invent any. Independent labels, privacy/source releases where held, adjudication, genuinely new cohort and independent performance/calibration claims remain blocked by actual evidence. Current research tooling itself is not “missing.”

The observed SVM advantage belongs to the exposed retrospective experiment; mBERT's weak phishing recall and the common ASCII abstention gate are research limitations, not excuses to relabel test outcomes or retune frozen thresholds. INT8 is a fifth deployment experiment with different scores; do not replace the float32 comparison member. A participant-facing on-device redaction/consent collection form remains **missing relative to the historical manuscript**, distinct from the implemented private coordinator intake/workbooks. Resolve whether that deliverable is retained before treating it as an app requirement.

**Thesis documentation: drafts prepared, not submission-complete.** Current Chapter 3/4 drafts, results/presentation tables, protocols, cards, defense support and reproduction guides exist. Final title/app name, actual annotation/prospective/phone findings, Chapter 5 synthesis, final cross-chapter objective reconciliation, bibliography/novelty verification, adviser review and partner turnover remain open. Older README/matrix/gap-analysis sections retain historical financial-only, unavailable-model and prior test-count statements beneath newer notices; they must not be quoted as current findings. No responsible whole-thesis percentage can be derived from file presence.

## Remaining work and release record

Core work is concentrated in **scope-aligned copy, model-specific threshold explanations, mBERT truncation disclosure and recovery hardening**. Accessibility/phone compatibility need verification, not an assumption that the layouts are absent. Final identity needs team input. Independent research and final writing require separate workstreams; optional warnings/reporting/backend deployment are later scope decisions.

Essential before claiming a verified thesis demonstration: fix misleading result/scope copy, expose truncation, exercise recovery and representative physical-device offline paste/share flows with exact APK hashes, and label the presentation's research limits accurately. Do not claim the thesis fully validated until genuine review/evaluation evidence exists. See prioritized [acceptance backlog](app-completion-backlog.md).

The audit change set is limited to the five new documentation files named in this package. `main` is not checked out or modified. Private audit intermediates remain ignored. Commit/push outcome is reported in the task's final response; this document does not claim a push before it occurs or embed its own circular commit hash. Remote branch equality is checked after a normal non-force push.
