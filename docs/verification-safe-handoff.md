# Safe handoff verification — 23 September 2026

## Follow-up resolution — 24 September 2026

The API 36 Settings and result-flow failures recorded below are **resolved for the exercised emulator paths** by implementation commit `ef8639ddfc3a960f653774e5b54d0aaa14fb3a71`. A late model-status update overwrote current navigation/input; status is now awaited before copying current state. Result-flow instrumentation now waits for keyboard dismissal and visible controls. No research threshold, reporting policy or model parameters changed.

Final evidence: each affected test passed 10 isolated repeats; the API 36 specialized suite passed 19 tests, and ordinary instrumentation passed 15 with 5 explicit skips. API 26 passed 4 focused tests. Both JVM variants passed 6 with 1 skip each; research 38, backend 45 and safe-handoff 8 all passed. Both APK builds and lint passed (0 errors, 5 existing warnings per variant). The three controlled state-race tests failed before the production fix and passed afterward.

[Root causes, exact commands, repeat history, sanitized evidence and remaining limitations](api36-reliability.md) are the current verification record. Earlier failures and failure JSON files are retained below as historical evidence, not rewritten as successful runs. Physical Xiaomi testing remains blocked by secure FRP; reporting and automatic warnings remain disabled.

## Historical handoff report — 23 September 2026

This report distinguishes this run's checks from supplied experiment claims and historical evidence. No private training ZIP was accessed, no dataset-dependent training was run, and no private model was changed. Android source, threshold and user-visible warning/reporting behavior are unchanged.

## Independently checked in this run

| Check / exact command | Result |
|---|---|
| Two named safe ZIPs: member listings, CRC integrity, paths, text types and symlink checks | Passed: backend 7 files, evidence 12 files; hashes in safe-handoff-archive-audit.json |
| Backend isolated Python 3.12 environment; `python -m unittest test_backend -v` from backend/ | Original supplied suite: 37 passed. Final expanded suite: 45 passed, 0 failures/skips |
| `research/.venv/Scripts/python.exe scripts/verify_research.py` | 38 Python tests passed; pip check passed; fixtures only |
| `python scripts/verify_safe_handoff.py` | 8 passed: syntax without execution, table math, saved reference/count consistency, source hyperparameters, schema/policy, sanitized directory and failure-cleanup regression |
| `scripts/build.ps1 -Variant development` | Successful build/lint/JVM check; initial outputs were largely up-to-date |
| `gradlew.bat :app:testDevelopmentUnitTest :app:testDebugUnitTest :app:assembleDebug :app:lintDebug :app:assembleDevelopmentAndroidTest -PinstrumentedBuild=development --rerun-tasks --console=plain` | Passed, 118 tasks executed; each JVM variant has 6 passed, 1 skipped, 0 failures |
| `gradlew.bat :app:lintDevelopment --rerun-tasks --console=plain` | Passed; both lint variants have 0 errors and 5 warnings (OldTargetApi, four GradleDependency notices) |
| `research/.venv/Scripts/python.exe scripts/emulator_api26_verify.py` | Passed 4 focused API 26 tests: 2 offline parity/invalid-model tests, 2 development-flow/large-font tests; settings restored |
| `research/.venv/Scripts/python.exe scripts/emulator_verify.py --variant development` | API 36: latest specialized run passed 15 tests and failed 1 large-font accessibility test; incomplete overall |
| `gradlew.bat :app:connectedDevelopmentAndroidTest -PinstrumentedBuild=development --console=plain` | Final ordinary suite: 11 passed, 1 failed, 5 skipped (17 JUnit cases). Final failure: result-flow timeout at FlowsTest.kt:113. JSON records preserve both ordinary runs |
| `backend/.venv/Scripts/python.exe -m pip_audit -r backend/requirements.txt --no-deps --disable-pip --format json` | Seven pinned runtime packages; no known vulnerabilities reported by the service at run time. Not a comprehensive security certification |
| Local debug/development APK integrity, membership, packaged permissions and unchanged private asset hash | Passed; no INTERNET permission, dataset/database/source ZIP in APKs. Development retains its pre-existing private model and remains excluded from Git/releases |

JVM ExportParityTest was skipped in both variants because no separate legacy real-export directory was configured. The ordinary suite also skipped five setup-dependent modem/notification/offline tests; their dedicated specialized-run results are listed separately. Those two JVM skips are not passes; schema-v2 supplied-model parity was exercised by the emulator tests without reading a private dataset. The four handoff training scripts were parsed only, never imported or executed.

## Failures and execution limits

API 36 initially had a System UI ANR dialog; choosing Wait cleared the preflight blocker. The first specialized run then timed out in FlowsTest.invalidFailureAndSyntheticResultsStayHonest (8 passed, 1 failed in that group). On subsequent runs that group passed all 9. Both later specialized runs reached the large-font AccessibilityTest but timed out opening Settings at line 25; 15 other specialized cases passed. This repeated failure remains unresolved. The trailing private-storage check was not reached by those runs and must not be reported as passed. Initial and retry failure JSON records are retained.

The first ordinary connected run had 11 passed, 1 failed, 5 skipped according to JUnit XML (17 cases; Gradle's progress banner reported 22 including skipped-case events). The failed denied-permission assertion followed a specialized failure that left SMS permission granted. The verifier now clears app state in finally even on failure; a mocked failure-path regression passes. This change does not alter Android behavior or mask the large-font failure. The ordinary retry installed into a state where the development package was absent after Gradle cleanup; its denied-permission test passed, but invalidFailureAndSyntheticResultsStayHonest timed out at line 113 (11 passed, 1 failed, 5 skipped). Thus API 36 has unresolved result-flow intermittency as well as the repeated specialized large-font failure. No further success was inferred from retries.

An intermediate backend run had 44 passes and one obsolete assertion that rejected the phrase in the new demo-view navigation link. The assertion now checks absence of the actual demo-row banner in the real-report view; final 45 pass, including a context-based cohort-isolation test. No model or Android expectations were loosened to pass tests.

Physical Xiaomi installation remains **blocked by secure_frp_mode=1**. Physical-device SMS testing remains **pending**. No security-setting changes, FRP bypass, bootloader operations, firmware flashing or reset were attempted. Dataset-dependent reproduction was **not performed**; prospective evaluation and calibration are **pending/not established**. Public deployment and real report submissions are **not applicable to this local-only task** and were not performed.

## Evidence classification

**Independently verified from safe files:** source syntax, final hyperparameters, table arithmetic, JSON keys/conversion mapping, supported backend fields and controls, domain/city/brand agreement, score/date validation, body limit, no IP storage column, no intentional request-body logging, demo separation and the stated software test results. Backend UTC offsets are restricted to +/-14:00, narrower than Java's theoretical +/-18:00; timestamps more than 14 hours ahead are rejected. These are documented server restrictions.

**Consistent with existing repository records:** 1,276 rows (1,054 ham / 222 smishing), five rounded guide scores within 0.00005, and existing runtime math. Counts and original guide-message inference were not recomputed from private data. Safe emulator probes independently exercise current model compatibility with tolerance 1e-10; this is software parity, not research performance.

**Handoff-reported only:** dataset-dependent fits, held-out procedure results, later refit/environment/vocabulary-overlap assertions, threshold and learning-curve results. Training and evaluation procedure documented with reproducible scripts and supplied result tables; dataset-dependent reproduction was not independently rerun in this handoff.

## Claims corrected

LR single-split supplied procedure evidence is accuracy 0.9453, smishing precision 0.8163, recall 0.8889, F1 0.8511. Handoff prose claims default/tuned five-seed F1 0.8635/0.8664 (+0.0029); its unchanged CSVs give 0.8610/0.8643 (+0.0033). RF single-split values also disagree; both versions rank RF highest on smishing F1, but Naive Bayes has the largest CV variability. All discrepancies are explicit in research/model_evidence/MODEL_EVALUATION.md. No unsupported number was silently promoted or rewritten in the source tables.

Selection favors compact portable LR inference, not best accuracy. The tuning difference is small, consistent with near-optimal defaults rather than a breakthrough. Inner CV leaks preprocessing because vectorization precedes folds; tuning reuse across overlapping splits is not nested validation. The full-data artifact has no prospective evaluation. No 95.3% unseen-traffic accuracy, calibration, probability/confidence, automatic-warning approval or production readiness is claimed. The >0.35 to <=0.50 caution band remains unimplemented research evidence.

## Privacy and sharing review

Known identifier-like vocabulary literals were omitted from repository-bound documentation using the requested sanitized wording. Full reference SMS examples and a literal model intercept were also omitted; the final-training script's embedded reference-message section was removed. Original ZIPs were unchanged. Seven untouched evidence source/table/parameter files retain original bytes in the working copy; Git may normalize line endings. No raw SMS, learned vocabulary, private weights, datasets, databases, credentials, .env, private training ZIP, APK or source-ZIP deliverable is part of this commit.

The copied evidence directory passes a mobile-number-like pattern scan. Candidate content also passed credential-pattern and exact full-reference-message exclusion checks against the authorized safe ZIP. The staged checker reads index bytes only, without opening private datasets/models. It and the packaging guard now reject databases, sidecars, joblib and named data/model exports. Pattern scans cannot prove arbitrary data is non-sensitive; source/doc review is also required. See handoff-sharing-review.json for the final index/archive/ignore results.

Reporting stays DisabledReportingRepository; neither an INTERNET permission nor Android endpoint, uploader, HTTP client, retry queue or transmitting button was added. Backend is a local readiness prototype only. All 13 deployment/consent/governance checklist items remain pending in reporting-readiness.md. No backend was publicly deployed, and only invented test metadata was stored in temporary databases.
