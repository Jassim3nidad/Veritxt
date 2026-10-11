# SmishGuard system memory for manuscript alignment

Version 2, engineering update begun 9 October and verified as recorded on 11 October 2026; original baseline 7 October. This is a self-contained factual handoff for an AI reading Chapters 1–3 without repository access. SmishGuard is an experimental offline Android SMS classifier with a completed minimalist interface and a preliminary retrospective four-model comparison. Independent labeling, prospective validation and physical-phone acceptance are not established. Implementation success must not be substituted for research validity.

Current software update: [audit fixes](app-audit-fixes-20261009.md) and [new APK handoff](apk-handoff-20261009.md) supersede baseline software-defect statements. Human, device and research limitations remain. The original audit is preserved.

## Evidence baseline and claim controls

Original 7 October documentation baseline: `e8a9d38fac9419e985b4b88404a5be48986fb036`, branch `codex/thesis-completion-package`; tracked intake was clean. The current engineering source is `470169efba0a10e1169827c369ee7ed64e647061`. The new private APKs retain all frozen model assets, thresholds, splits and research results; source fixes and exact emulator verification are documented in the dated handoff. Ignored private artifacts and earlier outputs remain preserved. Neither engineering nor documentation commits are the original experiment source commit.

Evidence priority: current source and exact model metadata establish behavior; 6 October scope/labeling decisions establish intended current scope; dated experiment records establish their own historical cohort; older plans establish commitments requiring reconciliation, not completed features. The 7 October app audit was made against `680b36fdf79ddcd58cc618346b8daf429a314af2`; the audited HEAD adds that audit. The expanded experiment records training implementation commit `56d0ddb`, followed by results commit `f4fd8d1`, validation/packaging commit `5699b31`, and review/INT8 commit `680b36f`.

Use these statuses explicitly:

| Status | Meaning in this package |
|---|---|
| Implemented and verified | Source exists and specified host, packaging or emulator evidence exercises it; never a claim of every-device acceptance. |
| Implemented but not fully verified | Behavior exists, but its named acceptance conditions remain untested or defective. |
| Preliminary research finding | Observed retrospective result with inherited labels, historical exposure and limited sampling. |
| Planned | A protocol or intended future procedure, with no completed observation. |
| Blocked by team input | Actual human returns, device observations, final wording or scope decisions are missing. |
| Out of current app scope | Excluded from the manual milestone, although historical commitments may remain. |
| Unresolved or contradictory | Competing requirements, stale wording or insufficient evidence; do not silently pick a convenient answer. |

Freshly executed for this package: source and Git inspection; read-only extraction of local Chapter 1/2 text and reading of the Chapter 3 draft; selected current model-metadata checks; hashing all 23 files in `research/data/validation-20261006/prospective-freeze.json` (23 matched, zero mismatches); arithmetic recalculation of precision, recall, phishing F1, macro-F1, accuracy and FPR from published confusion counts; document-only safety and archive checks. That documentation-only baseline performed no model fitting, dataset rebuild, new predictions, emulator, phone or human session. The later engineering update runs saved-reference/software emulator checks described above; it does not reopen research evaluation or establish physical/human acceptance. Existing performance and test reports are attributed below rather than presented as freshly rerun results. Citations in manuscripts were inspected as text, not verified against original publications.

## A Project identity and scope

Working app name: **SmishGuard**. Use `[FINAL APP NAME PENDING]` and `[FINAL THESIS TITLE PENDING]` for unresolved final wording, retaining the working name where needed to identify existing artifacts. No final replacement name/title or adviser approval is documented.

The intended beneficiaries are Filipino mobile users checking suspicious SMS, with researchers evaluating Filipino, English and Taglish classification. Historical documents also name banks, money services and a partner local government office as intended beneficiaries. No representative user study, actual partner adoption or public deployment is established. Demonstrated evidence comprises software fixtures, retrospective source-derived data and emulator use.

Current scope, clarified by the team on 6 October, is **all SMS phishing**, financial and nonfinancial. Phishing means a deceptive SMS attempt to obtain credentials, personal information or money, or induce harmful action through impersonation or a misleading pretext. Links and financial brands are neither necessary nor sufficient. Genuine SMS are negatives. Non-SMS material, pure nonphishing spam/scam, uncertain labels and privacy/source holds must remain separately accounted for, never automatically treated as genuine. Job, loan, delivery, government or reward themes do not alone determine inclusion or label.

English, Filipino and Taglish are intended languages. Retrospective test labels contain 315 roughly identified English records (270 ham/45 phishing) and 133 Filipino/Taglish records (122/11). These are supplied language guesses, not a validated language audit; mBERT's multilingual pretraining does not prove broad language coverage. The app's ASCII/vocabulary assessability gate can reject meaningful unsupported text.

The current milestone is single-message manual entry/paste/share and offline inference, preferences and private demonstration APKs. There is no inbox, saved scan history, blocking/deleting SMS, RCS monitoring, cloud inference, enabled reporting or enabled automatic warning service. The earlier incoming-warning, dashboard, participant collection-form and partner-turnover commitments have not automatically been cancelled; the team/adviser must reconcile them with the thesis.

Evidence: `docs/scope-clarification-20261006.md`, `docs/sms-labeling-guide-20261006.md`, `docs/requirements-traceability-matrix.md`, `docs/thesis-gap-analysis.md`, `docs/project-authorization.md`, `docs/four-model-comparison-20261005.md`.

## B Actual Android application

Android native application, Kotlin 2.3.21, Jetpack Compose/Material 3. Minimum SDK 26 (Android 8.0); compile/target SDK 36; version 0.3.0/code 3. JDK 17, Gradle 8.13, Android Gradle Plugin 8.13.2. Pinned dependencies include Compose BOM 2025.12.01, activity-compose 1.13.0, lifecycle Compose 2.10.0, DataStore preferences 1.2.1 and coroutines-android 1.11.0; mBERT variants add ONNX Runtime Android 1.22.0. These are repository pins, not recommendations about latest releases. Minimum SDK is a build contract, not proof all variants work on all Android 8 phones.

### Screens and workflows

1. Onboarding explains local processing, experimental limitations and permissions, with “Continue without permissions.” Completion is stored locally.
2. Home offers “Check a message,” model status and disabled-feature notices. Bottom navigation has Home, Check and Settings.
3. Check accepts editable multiline text and system paste; shows a 10,000-character counter, clear control, busy indicator and check button. Submit hides the keyboard and runs background inference. Repeated submission is disabled while busy.
4. A successful scan replaces editable text with the result and the exact submitted message preview for that session. “Check another message” clears it. The `RESULT` enum exists, but the actual result normally lives on the CHECK route with non-null result state; this is not a missing screen.
5. “What does this mean?” opens a scrollable explanation dialog. Closing it preserves the current result. Its reporting-options link enters a separate report-disclosure route and clears the message preview. The route offers controlled metadata choices but submission is disabled and no payload is queued.
6. Settings shows SMS/notification permissions and manually selected city, consent controls, Android settings links and preference/session reset. Permission choices cannot override disabled model warning policy.
7. Android `ACTION_SEND`, `text/plain`, from another app routes text into Check via initial or new intent; it does not automatically scan. Extras and ClipData references are removed. The app does not erase the originating app's text or system clipboard.

### Validation and inference

`CheckViewModel.edit` keeps at most 10,000 Kotlin string units (not Unicode grapheme clusters) and warns that extra text was removed. Blank input returns “Unable to assess.” Model policy rejects number-only, links-only, placeholder-only, obvious keyboard mashing and text with no supported meaningful vocabulary word. A single known word can be accepted; there is no universal minimum word count. Abstention is not a genuine-message classification or a proof that the input is meaningless.

Current classical models apply `sg-ascii-v1`: ASCII uppercase is lowered, URL/email/digit runs replaced by placeholders, non-ASCII-letter runs converted to spaces, then unigram counts, training-derived smooth IDF and L2 normalization. mBERT uses case-preserving minimization and its pinned cased basic/WordPiece tokenizer, without lowercasing/accent stripping. It adds special tokens, attention mask and type IDs and pads/truncates to 160 tokens, leaving at most 158 content tokens. Its assessability gate still uses the baseline ASCII/vocabulary policy. This mixture is actual behavior, not comprehensive multilingual semantic validation.

`SmishGuardApp` serializes initialization on IO, caps JSON metadata at 8,000,000 bytes and dispatches by variant. Only successful initialization is cached; another manual check retries failure. Cached mBERT bytes are hash verified and atomically repaired from original bundled assets. Model-free debug remains intentionally unavailable.

Scans run off the main thread under an application-scoped inference permit. Slow guidance appears after 7 seconds; a 60-second UI deadline discards the result. Cancellation and session generations prevent stale publication. Synchronous native work is not forcibly interrupted; the permit remains held until it returns. A new request receives a busy response, and a stuck operation requires Android Force stop/reopen. Controlled load/cancel/retry/cache checks are recorded in the 9 October evidence; physical acceptance remains pending.

### Results and exact policy

Success headings are **“Likely phishing”** or **“No phishing detected.”** Scores display **“Model score: x.x%”** with **“Experimental score; not a verified probability.”** Classification uses the unrounded score. Failure states are “Unable to assess,” “Model unavailable” or “Could not complete the check,” without fabricated scores. No-phishing output does not establish safety.

| Frozen model ID | Actual decision rule |
|---|---|
| `expanded-20261005-lr-c3abc4bb` | score >= 0.82 |
| `expanded-20261005-nb-c3abc4bb` | score >= 0.63 |
| `expanded-20261005-svm-c3abc4bb` | score >= 0.59 |
| `expanded-20261005-mbert-c3abc4bb` | score >= 0.8899999999999999 (serialized value; approximately 0.89) |

These values match frozen metadata. Result details now derive the exact threshold/comparator from the active policy. One-decimal Model score formatting never affects the unrounded classification; calibration executes once.

### Current module status (9 October update)

| Module | Status and remaining acceptance |
|---|---|
| Onboarding/Home/navigation | All-SMS-phishing copy implemented with experimental limits; human comprehension pending. |
| Manual entry, paste, preview and share | Implemented and verified within source/emulator evidence; actual phone acceptance pending. |
| Preprocessing and assessment | Frozen prefix retained; actual tokenizer truncation now triggers a notice and exact window details. |
| Offline loading and four variants | Implemented and verified at host/parity/emulator boundaries; physical acceptance pending. |
| Results and explanations | Active policy explanations and unrounded decisions implemented with boundary/calibration tests. |
| Preferences and privacy | Implemented and verified in exercised paths; no scan-history module intended. |
| Error/lifecycle recovery | Retry, verified cache repair, serialized work and UI deadlines implemented; no native hard-deadline or physical-acceptance claim. |
| Accessibility/layout | Semantic headings, polite result live region, control labels, minimum touch targets, scroll/IME/insets, font scaling and dark/light themes implemented. Automated large-font/320 dp checks are limited; TalkBack, focus/announcement comprehension, landscape and target-phone acceptance remain pending. |
| Packaging | Private development-signed APKs and guards implemented; production distribution is outside current scope. |

The 7 October audit recorded B1/B2/B3/B5 defects. The 9 October engineering update implements their coding fixes and records exact verification boundaries. The original audit is historical evidence, not a statement that these defects remain.

## C Architecture and data handling

Data path: typed/pasted/shared text → transient `CheckState` in ViewModel StateFlow → input cap/assessability → model-specific preprocessing → local model inference → once-only calibrated score and threshold decision → transient result/preview. Conservative domain extraction is separate optional metadata processing; it does not visit or evaluate the destination and is not a learned URL-feature branch.

Persistent app data: DataStore holds only onboarding completion, incoming-SMS consent and selected city. mBERT copies verified model weights to no-backup storage for inference; that persistent cache is model data, not message history. Reset clears preferences/session, not Android permission grants or the model cache. Input, checked-message preview, score, sanitized domain and check time exist only during the session. Editable input is cleared after inference, but the submitted preview remains until another check, navigation, back, backgrounding or recreation clears it. No SavedStateHandle/saveable text state or scan database exists. Cancellation clears references, not guaranteed forensic memory zeroization.

The Activity uses FLAG_SECURE, recents exclusion and disabled saved bundles; backup is disabled. Keyboard hints discourage learning, but OS/keyboard behavior is outside the app's storage guarantee. Source contains no message analytics/crash uploader or active network client. Manifest permissions are RECEIVE_SMS (optional incoming receiver plumbing) and POST_NOTIFICATIONS (optional warning channel). Telephony is optional. No INTERNET, READ_SMS, SEND_SMS, contacts or location permission; city is selected manually. Manual/share workflows require neither SMS nor notification permission. Bundled inference works offline and no URL is fetched/resolved.

Incoming plumbing can decode newly delivered SMS after consent/permission; it does not read the inbox or sender address. Production detectors have `automaticWarningsAllowed=false`, so automatic model inference/warnings are stopped by policy. Do not claim the receiver cannot receive any text. Notification/modem fixtures do not demonstrate approved live-model warnings.

`DisabledReportingRepository` always reports unavailable. Experimental/synthetic results cannot form sendable report payloads; UI submit is disabled and no endpoint/queue is configured. Separately, `backend/app.py` is a Flask/SQLite local reporting/dashboard prototype with allowlisted minimal metadata, validation, optional bearer gate, aggregate views and separated invented demo rows. It is not connected to Android, deployed to a partner, or evidence of production authentication/retention/security. Hosting, TLS, staff roles, rate limiting, deletion, log review and acceptance remain deployment work.

Conflict: `docs/privacy.md` says only class/score/domain/time remain after inference. Current `CheckViewModel.checkedMessage` also retains the submitted message for the active result preview. Use the current session-limited description, not that older absolute statement. Old backend README test-count prose also predates its newer 46-test evidence.

Evidence: `android/app/src/main/AndroidManifest.xml`, `data/PreferencesRepository.kt`, `privacy/Reports.kt`, `sms/IncomingSmsReceiver.kt` under the main Kotlin package; backup XML files; `docs/privacy.md`, `docs/reporting-readiness.md`, `backend/README.md`, `backend/app.py`.

## D Models and comparative experiment

Experiment: `expanded-20261005`, private run `research/data/expanded-20261005/experiment-v1/`. Separate APK IDs `ph.smishguard.lr`, `.nb`, `.svm`, `.mbert` share UI/workflow but carry separate frozen assets. They coexist for like-for-like demonstration; there is no combined runtime model switcher and no four independent UI implementations.

LR is scikit-learn LogisticRegression; NB is MultinomialNB; SVM is LinearSVC. All use raw-count unigram TF-IDF with smooth IDF and L2 normalization. Android schema-1 JSON exports contain the learned feature representation and linear parameters: LR coefficients/intercept, NB differences in class feature log probabilities and priors, or SVM separating margin. Sharing a linear scorer does not turn NB/SVM into LR. A fitted sigmoid maps each margin once to its model score; `ComparisonDetector` adds abstention/manual policy, not a second calibration.

mBERT fine-tunes `google-bert/bert-base-multilingual-cased`, revision `3f076fdb1ab68d5b2880cb87a0886f315b8146f8`, matching tokenizer, binary head and all 177,854,978 parameters trainable. Float32 ONNX deployment uses token IDs, mask/type tensors, then a saved sigmoid of positive-minus-negative logits once. Metadata identifies schema 5, class ordering, preprocessing, tokenizer and artifact hashes. The ONNX SHA-256 is `a319976073b401ac1e90c2b229bed8facb5be8c9f6367cf2df6f0781d8b57417`.

Calibration is fitted on the calibration partition. Thresholds maximize validation F1 over 0.05–0.95 in 0.01 steps, breaking ties toward the larger threshold. They are not selected on test results. Fitted sigmoid calibration and retrospective Brier/log loss do not validate real-world probability statements.

Frozen dataset SHA-256: `c3abc4bb23742226deab491821c1828559d895242da55267c77ae6f7dfa07b21`.
Split SHA-256: `67e064af947e5194cada9facff7fa02663d02dd2fff0756acbee9c58c50c4b1f`.
Cased-view SHA-256: `67300b1401200ec34e7b8ee05bf3918f7f4f04bdd8a8dbe9bde1165dca27e954`.
These identify whole files; row IDs, vocabularies, parameters and predictions are deliberately absent from this handoff. All 23 entries in the prospective freeze matched during this task.

Historical supplied LR (schema 2), LR candidate (schema 3), folded LR4 (schema 4), earlier three/four-model runs and generic transformer scaffolding are separate conditions. Optional dynamic INT8 mBERT is a fifth deployment experiment, not a replacement for float32 mBERT in the frozen four-model result. On 6 October a packaging-only rebuild reduced float32 mBERT from 1,511,956,972 to 800,410,184 bytes by removing unreferenced ZIP space; all 160 referenced file contents remained identical. This was not quantization, retraining or an accuracy improvement. Classical APKs are approximately 12.94 MB each. The old large mBERT APK remains historical.

Evidence: `research/smishguard/linear_export.py`, `expanded_train.py`, `fair_compare.py`, `mbert_experiment.py`, `mbert_evaluate.py`; `docs/expanded-comparison-protocol-20261005.md`, `docs/mbert-packaging-audit-20261006.md`, `docs/mbert-int8-experiment-20261006.md`, `docs/model-contract.md`. Public source alone lacks private trained inputs and does not establish bit-identical independent reproduction.

## E Dataset and methodology

Supplied package: 3,552 included (3,084 ham, 468 smishing), 2,594 supplied template groups, 71 flags; 2,272 excluded (1,950 advertising, 322 fraud). No duplicate IDs, cleaned exact duplicates, conflicting redacted labels or mixed-label supplied groups were reported. Original raw sources were absent from that ZIP: auditing its CSV and pinned source snapshots is not a rebuilt original collection.

Used cohort: **3,340**, comprising **2,947 ham (88.23%) and 393 smishing (11.77%)**. Held 212: 60 unresolved GitHub-source permission records, 13 unresolved team/social origin/consent/use records and 139 automated privacy holds. Retained sources: ZERO v1/Tagalog (2,053 ham/66 phishing, CC0), Chua v15/marketing (877/164, CC BY), BwandoWando v49 (17/163, CC BY-NC-SA restricted in the recorded workflow to local noncommercial research). Source matching supports traceability, not proof of original acquisition or participant consent. Human privacy review remains pending. This package reports recorded source-use decisions, not a new legal assessment or public redistribution authorization.

Inherited labels came from source/rule decisions. The 71 flagged and 300 validation-review entries lacked completed labeler/final-label fields; 59 flags survived eligibility. Latest audited human records contain zero final decisions and 3,340 pending. Neither automated confidence fields nor “manually verified” descriptions establish independent review. Historical exclusion of job/loan fraud conflicts with broad current scope: 18 excluded records with possible phishing signals require new review, not silent inclusion/relabeling or altered old results.

Prediction features consist only of minimized message text. Source, sender, date, IDs, categories, language guesses, confidence and review fields are audit/grouping/descriptive metadata. Case-preserving URL/email/digit replacement is common; classical models additionally normalize to ASCII. Automated privacy screening and holds do not certify anonymization.

Label-blind grouping unions supplied template links, identical normalized views and SequenceMatcher near copies at ratio >=0.85. Merging 616 supplied groups produced 1,848 components. Seed 20260929 applied the deterministic approximately 55/15/15/15 allocation; group sizes mean achieved fractions differ from targets. All six partition-pair group-overlap counts are zero. This does not establish perfect semantic independence.

| Partition | Total | Ham | Phishing | Groups | Positive-bearing groups | Role |
|---|---:|---:|---:|---:|---:|---|
| Training | 1,860 | 1,637 | 223 | 1,044 | 104 | Fit vectorizers/models; grouped inner selection. |
| Validation | 622 | 561 | 61 | 283 | 30 | Select mBERT epoch and all thresholds. |
| Calibration | 410 | 357 | 53 | 270 | 25 | Fit sigmoid transformations. |
| Test | 448 | 392 | 56 | 251 | 25 | Final frozen retrospective comparison. |

Calibration/evaluation partitions met the predeclared floor of 20 positives and 10 positive-bearing groups; grouped-CV fallback was unnecessary. Five training-only grouped folds selected C/alpha from {0.1, 1, 10} by average precision with TF-IDF freshly fitted in each fold. Selected LR C=10, NB alpha=0.1, SVM C=10. Final classical fits used only training data.

mBERT: seed 20261005, two epochs, Adafactor learning rate 2e-5, weight decay 0.01, microbatch 1/accumulation 8, gradient checkpointing, deterministic CUDA, float16 training autocast on RTX 3050 Laptop 4 GiB. Validation AP selected epoch 2. Training-only p95 length 151.05 selected 160 tokens (rounded to 16 within 64–256); 67/1,860 training examples truncated versus 193 at 128. Training lasted 668.797 seconds within a 2,700-second budget. Checkpoints preserve optimizer/scaler/RNG state. This is bounded configuration selection, not an exhaustive transformer search. See `research/mbert-dependency-lock.txt` and `docs/expanded-comparison-reproduction-20261005.md` for pinned dependencies/reproduction contracts.

Historical exposure is substantial: 1,032 eligible texts matched prior original-source text (555 former train, 159 validation, 165 calibration, 153 test), with eight changed labels. Broader exact/near-copy exposure found 3,269/3,340, including 439/448 new test records. The remaining 71 unmatched records are not certified unseen. Earlier full training membership is incomplete. Source imbalance is severe: 44 of 56 test positives originate from a source with no test negatives, and language/category fields are not independently confirmed. New IDs/splits do not erase historical exposure.

Independent-review workflow is implemented but blocked on actual returns: two blinded, separately shuffled packets with unrelated IDs; labelers cannot see inherited labels/predictions/each other; responses include phishing/genuine/out_of_scope/uncertain, rationale and privacy flag. Record genuine distinct reviewer attestations and privacy release; compute raw agreement and Cohen's kappa before third-person adjudication; preserve uncertain/missing/excluded cases and version accepted labels separately. Software tests with fictional reviewers are not human agreement evidence.

Prospective evaluation is **planned, not completed**. Freeze the four original fitted pipelines and runtime; collect genuinely new messages after the recorded freeze, consecutively in a documented recruitment channel, closing at 200 approved distinct groups or 30 days, whichever first. Preserve receipt/source/privacy evidence; screen available history and within-batch duplicates, including both SequenceMatcher directions; human-review no-match semantic overlap; take the first eligible member per group. Freeze labels/cohort before one evaluation. Low class/group support is descriptive, not a reason to extend/tune after seeing predictions. Report coverage and abstentions separately, including sensitivity counting abstentions as failures. Relabeling old records cannot make them prospective. Evidence: `docs/review-completion-20261006.md`, `docs/prospective-validation-plan-20261006.md`, `docs/blinded-validation-workflow-20261006.md`, `research/smishguard/review_completion.py`, `validation_stage.py`.

## F Results and verification boundaries

The following supplied aggregate results are from `docs/expanded-four-model-results-20261005.json` and `docs/four-model-comparison-20261005.md`, experiment `expanded-20261005`, identical 448 test records. This package independently recalculates the displayed classification metrics from their confusion counts; it does not independently regenerate predictions or bootstrap/calibration outputs. Percentages except count columns and explicitly unitless values.

| Model | TN/FP/FN/TP | Precision | Recall | Phishing F1 | Macro-F1 | Accuracy | FPR |
|---|---|---:|---:|---:|---:|---:|---:|
| LR | 391/1/25/31 | 96.88 | 55.36 | 70.45 | 83.62 | 94.20 | 0.26 |
| NB | 388/4/36/20 | 83.33 | 35.71 | 50.00 | 72.55 | 91.07 | 1.02 |
| SVM | 391/1/7/49 | 98.00 | 87.50 | 92.45 | 95.72 | 98.21 | 0.26 |
| mBERT | 392/0/33/23 | 100.00 | 41.07 | 58.23 | 77.09 | 92.63 | 0.00 |

| Model | Average precision | Trapezoidal PR-AUC | ROC-AUC | Brier | Log loss | Phishing F1 95% group interval |
|---|---:|---:|---:|---:|---:|---|
| LR | .94398 | .94309 | .98665 | .02576 | .09309 | .5455–.8571 |
| NB | .70746 | .69752 | .93622 | .06899 | .22882 | .2521–.8090 |
| SVM | .95793 | .95715 | .99048 | .02403 | .09549 | .7755–.9787 |
| mBERT | .89282 | .89227 | .96360 | .06533 | .24637 | .3278–.9020 |

Average precision and trapezoidal PR-AUC are distinct calculations; do not silently interchange them. Bootstrap intervals use 2,000 group resamples, seed 20260929, conditional on fixed fits and imperfect groups, without multiple-comparison or training-selection uncertainty. SVM has the highest observed phishing F1 in this run; paired SVM-minus-mBERT F1 interval (-.0801, .6331) includes zero. No final algorithm winner follows. Zero observed mBERT false positives does not prove zero population risk. Validation is reused for selection/threshold choice; inherited labels, exposure and sampling constrain every estimate. No cross-experiment improvement claim is supported merely by comparing older scores.

Classifier test coverage was 448/448 for each deployed pipeline. Subgroup metrics require >=20 records and >=5 of each class; otherwise report support only. Abstention is a separate app policy, never a correct negative.

Engineering evidence, distinguish environments:

| Evidence | What was actually supplied |
|---|---|
| 5 October host/JVM/build | Four builds/lints passed; 21 JVM tests reported per variant with three skipped. Parity evidence: 461 cases each classical model, 468 mBERT. |
| 5 October emulator | API 36 x86_64: 25 tests each classical variant, 24 mBERT; offline paste/share, permissions, failures, lifecycle/privacy and actual export checks. This is not phone evidence. |
| 6 October repackaging | 160/160 referenced APK entries unchanged; 24 emulator checks, 468 parity cases, zero class changes, no INTERNET, signature checked; new APK 800,410,184 bytes. |
| 7 October audit host | 21 mBERT JVM tests: 17 passed, four skipped, zero failures/errors; lint zero errors/fatal and five warnings; 46 backend fixture tests and 11 review-completion fixture tests passed. No attached adb target and no new connected run. |
| This package | Read-only source/metadata/23-hash verification and aggregate arithmetic/document/archive checks; no new Android runtime tests. |
| Physical/human | No completed phone observations, independent label returns, prospective cohort or user usability findings established by the inspected evidence. |

The four latest skipped JVM tests were private candidate parity, historical export parity, folded-candidate parity and actual cased-tokenizer parity requiring private configuration. Skips are not passes; prior artifact-linked parity is separate evidence. Historical API 26 tests do not prove all current frozen variants pass API 26 acceptance. Five preserved APK signatures/assets/no-INTERNET checks in the previous audit are not a new signature run by this package.

Common-session emulator benchmark (5 October, four virtual CPUs/4096 MiB, Windows 11 host/i5-11400H/about 24 GiB RAM, airplane mode, Wi-Fi off, one app process, four fictional probes, 20 warmups/200 scans):

| Model | Cold detector load ms | Warm median ms | Warm p95 ms |
|---|---:|---:|---:|
| LR | 260.025 | .302 | .646 |
| NB | 232.313 | .286 | .626 |
| SVM | 219.413 | .314 | .668 |
| mBERT | 8238.566 | 154.173 | 167.034 |

All scored 200/200 benchmark scans. Single-session sequential execution/cache effects limit comparisons; cold loading is distinct from warm inference. CPU training times were about 1.041/.939/1.030 seconds for LR/NB/SVM; failed baseline memory probes are unavailable, not zero. Do not replace this common-session benchmark with separate repackaging/INT8 timings. Evidence: `docs/expanded-four-model-verification-20261005.json`, `docs/expanded-four-model-benchmark-20261005.json`, `docs/app-completion-audit-evidence.json`.

App completion audit: 90.5% implementation and 64% verification readiness for the manual milestone (communicate about 90% and 65%). They are weighted judgment indices using coverage factors, not accuracy, test-pass rate, thesis completion, statistical estimates or remaining effort. About 80% app implementation is conservative shorthand in the previous audit, not a measured thesis percentage. Disabled services/human research were excluded from that denominator; broader scope requires a new assessment.

## G Outstanding work and acceptance

1. B1 implemented: exact active-policy result details and boundary tests; see the 9 October evidence.
2. B2 implemented: all-SMS-phishing manual copy; final name/title remain pending.
3. B3 implemented: tokenizer-derived truncation disclosure and fictional tail-cue tests; frozen window unchanged.
4. B5 implemented: controlled slow/cancel/retry/cache regression checks. UI deadlines do not terminate synchronous native calls; actual phone acceptance remains pending.
5. Obtain actual authorized phone installation/offline/share/storage/lifecycle/failure measurements, APK hashes/API/ABI and TalkBack/200% text/landscape/user comprehension evidence. All four current APKs passed on API26 and API36 x86_64 emulators; physical phones and other ABIs remain untested. An emulator-only demo must state these boundaries.
6. Obtain independent A/B labels, privacy/source checks and third-review adjudication; version guide changes and reviewed cohorts, compute agreement only from real returns. Collect/freeze/evaluate prospective data once under the existing protocol.
7. Team/adviser must reconcile unperformed XLM-R/RoBERTa-Tagalog, calamanCy, character features, URL/weak-control ablations, random-vs-group experiments, participant-side consent/redaction form, partner turnover and public dataset-release commitments. Do not silently rewrite approved objectives.
8. Supply final title/name; align Chapters 1–5, verify references and novelty claims, integrate only actual future evidence. Production signing/distribution, backend hosting/governance, reporting/warnings and partner acceptance are later work if retained.

Detailed acceptance criteria: `docs/app-completion-backlog.md` B1–B15. A historical Xiaomi device/FRP blocker is not a successful device test or authority to bypass protections. Prepared worksheets and remote guides are not observations.

## Claims the manuscript must not make

- Any algorithm is generally superior or the final winner; observed SVM F1 alone cannot establish this.
- Scores are validated probabilities, guarantees of safety or proof every scam is prevented.
- Independent labels, adjudication, consent, ethics/adviser approval or prospective testing are completed without actual evidence.
- Emulator/JVM passes establish physical-phone performance, human usability or all-device/minimum-API acceptance.
- Reporting, live dashboards from Android or automatic model warnings are enabled.
- Historical extra models, URL/character ablations, participant form, partner turnover or public data release were completed.
- A final thesis title/app name has been adopted or broader scope has documented adviser approval.
- The old job/loan exclusions govern current all-phishing eligibility, or the wider intended scope proves representative coverage.
- Group-disjoint new partitions erase historical exposure; unmatched messages are certified unseen.
- Packaging shrinkage is quantization or a new accuracy result; INT8 replaces the frozen float32 comparison.
- No message text remains immediately after inference (the current session preview remains), or reference clearing proves forensic erasure.
- Audit percentages measure thesis completion or research validity; synthetic tests are human research outcomes.

This memory contains aggregate facts and short manuscript excerpts only through its companion guide. It contains no raw/private SMS, row IDs, vocabulary identifiers, fitted weights, individual predictions, credentials, signed documents or APKs. Private original artifacts were not modified.
