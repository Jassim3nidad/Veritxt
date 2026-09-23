# Requirements traceability matrix

Read with `thesis-gap-analysis.md` and `verification-safe-handoff.md`. “In progress” can mean implemented tooling with research execution pending. All paths are repository-relative. Owners are unassigned roles, not invented commitments.

| ID / source requirement | Implementation | Test/evaluation and existing evidence | Status / missing work | Responsible role | Thesis placement |
|---|---|---|---|---|---|
| O1 Ch1 documented consented/redacted independent collection | `research/smishguard/intake.py`, `review_packets.py`, `annotation_results.py` | Intake/packet/annotation unit tests; `dataset-audit.json`, `source-evidence.md` | Requires researchers: rights, redaction, labels, agreement, adjudication; collection form missing | Data coordinator + independent annotators | Ch3 dataset/ethics; Ch4 characteristics/agreement |
| O2 Ch1 compare word/character LR, NB, SVM and two transformers | `train.py`, `compare.py`, `transformer_compare.py` | Synthetic fit/selection tests; supplied procedure comparison in model_evidence (not independently rerun) | In progress: eligible data, vetted local checkpoints, calamanCy condition, common selection protocol and timing/memory | ML researcher | Ch3 experimental design; Ch4 comparison |
| O3 Ch1 unfamiliar-message evaluation and random comparison | `data.py:template_groups,split_rows`, `train.py` | Label-blind near-copy components; six pairwise group overlaps; deterministic split tests | In progress: freeze real manifests; reserve genuinely unseen cohort; receipt dates absent for chronology | ML researcher + coordinator | Ch3 splitting; Ch4 generalization |
| O4 Ch1 URL ablation and three weak controls | `preprocessing.py:feature_text`, `train.py:transform` | Synthetic text-only, text-url, placeholders, shape, punctuation tests | In progress: truthful pre-redaction URL facts and approved experiment matrix | ML researcher | Ch3 conditions; Ch4 shortcut analysis |
| O5 Ch1 calibration/cut-off/error assessment | `train.py`, `evaluate.py`, `uncertainty.py` | Separate calibration/validation/final, sealed selection, bootstrap fixture tests | In progress: real reliability plots, FPR/FNR and reviewed warning policy | ML researcher + adviser | Ch3 metrics; Ch4 calibration; Ch5 limits |
| R1 Offline single-message paste/share | `MainActivity.kt`, `CheckViewModel.kt`, `SuppliedDetector.kt` | `DevelopmentFlowTest`, `FlowsTest`, offline `SuppliedModelTest`; API26/36 JSON | Complete for exercised emulator paths; physical validation pending | Android developer | Ch3 implementation; Ch4 software tests |
| R2 Permission-based incoming SMS and multipart | `sms/IncomingSmsReceiver.kt` | `SmsDecodingTest`, `ModemSmsTest`, `NotificationBehaviorTest` | In progress: plumbing tested; automatic model warnings intentionally disabled; carrier/device cases pending | Android developer + tester | Ch4 functional/device tests |
| R3 No blocking/deleting/default SMS replacement | `AndroidManifest.xml`, receiver | Manifest inspection; original inbox delivery in verifier | Complete for implemented policy; manufacturer behavior unverified | Android developer | Ch3 safeguards |
| R4 No scan text persistence/transmission | `CheckViewModel.kt`, preferences, manifest | `PrivacyLifecycleTest`, verifier fixture-marker search; no INTERNET/READ_SMS/SEND_SMS | Complete for exercised paths; no forensic erasure claim | Android developer | Ch3 privacy; Ch4 test scope |
| R5 Consent and permission denial/settings | `MainActivity.kt`, `PreferencesRepository.kt` | Flows, denial, notification channel tests | In progress: permanent denial/vendor restrictions need physical checks | Android tester | Ch4 tests |
| R6 Voluntary minimized reporting | `privacy/Reports.kt`, `backend/README.md` | Disabled repository and experimental payload rejection tests | Requires researchers: endpoint, governance, retention, access and deployment approval; no transmission | Team + client | Ch3 planned architecture; Ch4 pending |
| R7 Dashboard brand/domain/time/city/linkless reports | `backend/app.py`, `backend/templates/dashboard.html` | Local prototype and 45 backend tests; isolated demo aggregates | Local readiness only; requires approved deployment and partner acceptance; nullable domain ambiguity | Team + client | Ch3 planned service; Ch4 pending |
| R8 Filipino/English/Taglish | Unicode supplied detector; subgroup code | Fixed Unicode/Taglish probes; supplied language counts | In progress: language capability not established by lexical probes; no separately labeled Filipino rows supplied | Annotators + ML researcher | Ch4 subgroup results |
| R9 Missing/invalid model and extreme input | `Detector.kt`, `SuppliedDetector.kt` | `CoreTest`, `SuppliedModelTest`, `OfflineModelTest`, long/empty flow tests | Complete for tested rejection cases | Android developer | Ch4 software tests |
| R10 Lifecycle/accessibility | Activity/ViewModel/UI semantics | `PrivacyLifecycleTest`, `AccessibilityTest` | In progress: tested recreation and 2x font; TalkBack, landscape and broader screen coverage pending | Tester | Ch4 usability/limits |
| R11 Physical latency/memory and hardware validation | Test protocol in `physical-device-checklist.md` | Historical emulator results are software evidence only | Blocked on target Xiaomi; alternative authorized device may be separately documented | Device owner + tester | Ch4 device results |
| R12 Research artifacts, installable app and orientation | package script; cards; defense script | Local development APK checks; sanitized source archive | In progress: public model/data release withheld; final report/dashboard orientation pending | Release coordinator | Ch5 turnover/reproducibility |
| R13 Participant-side redaction and consent form | No implementation | Labeling guide is a different coordinator workflow | Requires researchers: ethics/consent protocol and approved form design | Coordinator + adviser | Ch3 collection |
| R14 2,500 target / 1,200 minimum and fallback | Training minimum guard | `test_minimum_is_not_bypassed` | Requires researchers: eligible counts, power rationale and finalized repeated-validation fallback | Adviser + ML researcher | Ch3 sample design; Ch5 limitations |

## Safe handoff status update

| Item | Correct status | Evidence |
|---|---|---|
| Offline manual scanning | Implemented | Existing Android code/tests |
| Android model integration | Implemented | SuppliedDetector and safe probe parity |
| Procedure-level model evaluation | Supplied and documented, conflicts unresolved | research/model_evidence |
| Independent dataset-dependent rerun | Not performed | No dataset/training ZIP accessed |
| Model calibration | Not established | No calibration study supplied |
| Prospective unseen-data evaluation | Pending | Full-data deployed fit |
| Automatic SMS warnings | Disabled/unapproved | Existing detector policy unchanged |
| Android reporting | Disabled | DisabledReportingRepository, no INTERNET |
| Backend prototype | Local readiness prototype only | backend unit tests |
| Public backend deployment | Not approved | reporting-readiness checklist |
| Physical Xiaomi installation | Blocked by secure FRP | External blocker unchanged |
| Physical-device SMS testing | Pending | Emulator evidence is separate |

O2 procedure comparison now has supplied scripts/tables, not independent predictive validation. Reporting/dashboard requirements have a local source prototype, not partner acceptance or production implementation. See verification-safe-handoff.md for this run; older rows retain their historical scope.
