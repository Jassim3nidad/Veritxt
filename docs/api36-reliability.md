# API 36 test reliability follow-up — 24 September 2026

Continuation of `6e33360ae41d4a6673122f26072267a26cb4b17c` on `codex/thesis-completion-package`. The backend/evidence integration was already complete. This follow-up fixes asynchronous model-status initialization and instrumentation synchronization. Model parameters and the research/reporting policy are unchanged.

Implementation commit: `ef8639ddfc3a960f653774e5b54d0aaa14fb3a71`. The starting specialized failure is preserved in [api36-pre-fix-specialized-results.json](api36-pre-fix-specialized-results.json), alongside the existing handoff failure JSON. Earlier failure records remain unchanged; this follow-up marks the two API 36 failures resolved for the tested emulator paths.

## Diagnosis and correction

### Result-flow timeout

The original physical-click test failed once in three isolated runs without permissions and once in three with the specialized suite's granted permissions. In the granted failure, only two detector calls occurred before the third expected result timed out. The activity retained input, `busy=false` and no result: the next scan had never started. This does not indicate slow model initialization or a stuck inference coroutine.

A first correction used the button's semantic click action and required visibility. It passed nine of ten result-flow runs but failed its eighth run at the visibility assertion, before any detector call. Captured semantics placed the Check button at vertical coordinates 1219–1324 while its scroll viewport ended at 1155. The test-owned view rendering also showed the focused input and clipped controls. Thus a single `performScrollTo()` did not establish continued visibility while the native IME/inset and focused-field relocation changed the viewport. The evidence supports a test synchronization/coordinate problem; it does not prove which native layout callback won the race.

`FlowsTest` now dismisses the native keyboard and waits until IME insets report it hidden before scrolling. `scrollToVisible` rechecks scroll and display state within the existing ten-second bound, then activates the same accessible button callback. The keyboard step was added after a further visibility-only batch passed nine of ten result-flow runs but caught another viewport change between the display check and assertion. Visibility alone was therefore insufficient; that failed attempt is retained. Result headings still have the original ten-second wait. Every scan must invoke inference exactly once, clear the input, omit probability wording and leave report submission disabled. No assertion was removed, no fixed sleep was added, and no inference algorithm or model parameter changed. The approach uses Compose's documented [visibility and condition-wait APIs](https://developer.android.com/reference/kotlin/androidx/compose/ui/test/package-summary).

### Large-font Settings navigation

The first six isolated original-action runs at font scale 2.0 and a baseline specialized suite passed. A subsequent ten-run batch after an emulator restart exposed five large-font failures. Diagnostics showed Home restored after navigation, including after an accepted semantic Settings action; the tab was visible with a sufficient hit area. This ruled out coordinate tapping as the sole cause.

`CheckViewModel` initialized status with `mutable.value.copy(modelStatus = app.detector().status)`. Kotlin evaluates the receiver before the suspending argument: it captured the initial Home state, suspended during detector loading, and later wrote that stale state over current navigation/input. The correction awaits the status first, then copies the latest state. This preserves navigation and session-clearing behavior without waiting for model loading before the user can navigate.

`AccessibilityTest` now selects the actionable selectable Settings tab, requires a visible target at least 48 dp in both dimensions, invokes its semantic action and asserts the selected state. Heading, switch, input and scrolling checks remain. Additional ordinary physical taps on Home and Settings verify navigation hit targets after layout settles. Font scale is still 2.0 with the original minimum-scale assertion; accessibility scaling was not reduced. The deterministic `ModelInitializationTest` holds detector loading on a `CompletableDeferred`, changes navigation/input or clears the session, then releases loading and compares the entire state. This isolates the production race from UI timing without sleeps or private model assets. All three new tests failed against the original production code before the fix, independently confirming the stale-state defect.

## Evidence and commands

Each repeat invocation verifies emulator identity, API 36 and boot completion, clears app state between tests, restores font scale and clears test state in `finally`. Diagnostics are opt-in and live only in the instrumentation APK. `FLAG_SECURE` remains enabled. Test-owned view renderings exclude the native keyboard and system overlays, so they are not whole-device screenshots. Initial native screenshot attempts were black and are not usable layout evidence. Logs/renderings stay under ignored `deliverables/api36-reliability/`; only sanitized summaries are shared.

| Stage | Large font | Result flow | Meaning |
|---|---:|---:|---|
| Original actions, denied permissions | 3 passed / 0 failed | 2 passed / 1 failed | Valid isolated baseline |
| Original actions, granted permissions | 3 passed / 0 failed | 2 passed / 1 failed | Valid permission-state baseline |
| First semantic-action correction | 10 passed / 0 failed | 9 passed / 1 failed | Visibility race caught; superseded |
| Visibility wait, before state fix | 5 passed / 5 failed | 10 passed / 0 failed | Exposed stale model-status state after emulator restart |
| State fix, before keyboard dismissal | 10 passed / 0 failed | 9 passed / 1 failed | Final large-font repeats; result-flow fix still incomplete |
| Keyboard dismissal plus state fix | Not rerun in this isolated batch | 10 passed / 0 failed | Final result-flow repeats |

An earlier diagnostic setup encoding error was corrected before the valid baseline; those runs are excluded from the table and retained locally under `diagnostic-setup`. A later repeat attempt stopped at emulator preflight because the emulator was unavailable, executing no tests. The dedicated emulator was restarted and boot completion verified. Neither setup attempt counts as a test pass. An intermediate keyboard-dismissal implementation did not compile because Espresso core was not a direct test dependency; it was replaced with the already available AndroidX window-insets API, adding no dependency. The failed compilation is not counted as a successful build.

Commands used for isolated runs (root directory):

```powershell
python scripts/repeat_api36.py --phase baseline --runs 3
python scripts/repeat_api36.py --phase baseline --runs 3 --granted --batch granted
python scripts/repeat_api36.py --phase fixed --runs 10
python scripts/repeat_api36.py --phase fixed --runs 10 --batch visible
python scripts/repeat_api36.py --phase fixed --runs 10 --batch final
python scripts/repeat_api36.py --phase fixed --runs 10 --case result-flow --batch ime
```

The final per-case evidence is **10/10 large-font runs and 10/10 result-flow runs**, with zero skips in either batch. The three controlled initialization tests changed from 0 passed / 3 failed before the production fix to 3 passed / 0 failed after it. [Sanitized run summaries and local artifact hashes](api36-reliability-results.json) retain every valid repeat stage, including failed intermediate corrections.

The baseline commands describe historical source versions; running them on this branch now exercises the corrected tests. The harness refuses to overwrite a nonempty evidence directory; use a new `--batch` for subsequent runs.

## Final regression results

| Check | Passed | Failed | Skipped | Evidence / qualification |
|---|---:|---:|---:|---|
| API 36 specialized | 19 | 0 | 0 | development-emulator-results.json; includes 3 new initialization tests |
| API 36 ordinary instrumentation | 15 | 0 | 5 | api36-connected-reliability-results.json; 20 JUnit cases |
| API 26 focused emulator | 4 | 0 | 0 | api26-results.json; offline parity/invalid model and development/2x-font flows |
| JVM development | 6 | 0 | 1 | Legacy export parity directory not configured |
| JVM debug | 6 | 0 | 1 | Same explicit legacy parity skip |
| Research Python | 38 | 0 | 0 | Software fixtures only; pip check also passed |
| Backend Python | 45 | 0 | 0 | Local prototype tests; pip check also passed |
| Safe handoff | 8 | 0 | 0 | Includes model-evidence consistency and failure cleanup |

The five ordinary instrumentation skips are modem, permission/notification and offline setup-dependent tests. Their specialized executions passed; skips remain skips in the ordinary count. Gradle's progress banner includes skipped-case events and says 25; the JUnit XML contains 20 cases. Repeated tests and overlapping suites must not be added together as distinct coverage.

Both Android variants built. Lint has zero errors and five existing warnings per variant (one OldTargetApi and four GradleDependency notices). Test APK compilation passed after the final keyboard correction. App APK CRC/member checks passed; test-only diagnostic/regression classes are absent from app DEX. Packaged permissions still omit INTERNET, READ_SMS and SEND_SMS. The specialized private-storage check inspected two files and found zero raw fixture markers; this is bounded app-storage evidence, not forensic memory erasure.

## Regression commands

Executed from the repository root on Windows with JDK 17. The existing host Java pipe workaround was set for Gradle only:

```powershell
$env:JAVA_TOOL_OPTIONS='-Djdk.net.unixdomain.tmpdir=C:/sg-nonexistent-socket-dir'
.\gradlew.bat :app:testDevelopmentUnitTest :app:testDebugUnitTest :app:assembleDevelopment :app:assembleDebug :app:lintDevelopment :app:lintDebug :app:assembleDevelopmentAndroidTest -PinstrumentedBuild=development --rerun-tasks --console=plain
.\gradlew.bat :app:assembleDevelopmentAndroidTest -PinstrumentedBuild=development --console=plain
adb -s emulator-5554 shell am instrument -w -e class ph.smishguard.ModelInitializationTest ph.smishguard.dev.test/ph.smishguard.SoftwareTestRunner
research/.venv/Scripts/python.exe scripts/emulator_verify.py --variant development
$env:ANDROID_SERIAL='emulator-5554'
.\gradlew.bat :app:lintDevelopment :app:connectedDevelopmentAndroidTest -PinstrumentedBuild=development --console=plain
research/.venv/Scripts/python.exe scripts/emulator_api26_verify.py
backend/.venv/Scripts/python.exe -m unittest discover -s backend -p test_backend.py -v
backend/.venv/Scripts/python.exe -m pip check
research/.venv/Scripts/python.exe scripts/verify_research.py
python scripts/verify_safe_handoff.py
python scripts/check_staged.py
git diff --check
git diff --cached --check
```

The controlled initialization command ran once against the original app and once after installing the fixed app and test APKs. The specialized suite also ran once before the production correction with `--diagnostics` (16 passed); its final run omits diagnostics and includes the three new tests (19 passed). The full Gradle regression executed all 141 tasks. Instrumentation was rebuilt after the keyboard correction, and development lint was repeated for that final test source. No private-data training command was executed.

## Changed files and sharing checks

- Application: `android/app/src/main/java/ph/smishguard/CheckViewModel.kt` only.
- Instrumentation: `AccessibilityTest.kt`, `FlowsTest.kt`, new `ModelInitializationTest.kt` and new `ReliabilityDiagnostics.kt` under `android/app/src/androidTest/java/ph/smishguard/`.
- Verification tooling: `scripts/emulator_verify.py` and new `scripts/repeat_api36.py`.
- Evidence/docs: this report and its two new JSON summaries, refreshed API 26/36 result JSON, README, verification reports, requirements traceability matrix and thesis gap analysis.

Index-only sharing checks and manual diff review exclude private datasets/models, identifier literals, real SMS/report data, credentials, databases, APKs, ZIPs and diagnostic screenshots. Ten Git ignore path probes passed without opening private files. A broader index scan flagged one pre-existing mobile-like negative fixture in `research/tests/test_research_workflow.py`; redacted context confirms it tests PII rejection, and its complete file is unchanged from the starting commit. It is not a new learned-vocabulary value. No literal is reproduced here; no scanner rule was weakened. No private/generated artifact path appears in the tracked tree. APKs and local diagnostics remain ignored. No release or public service was created. The private training ZIP and original handoff archives were not accessed in this continuation.

Sharing review resumed on 25 September. After transient GitHub HTTPS connection failures, a fresh fetch succeeded and confirmed no co-developer commits beyond the starting remote head.

Both test emulators were shut down after their scripts restored settings and cleared test app state. Physical devices were not changed. Public deployment and physical-device testing are blocked/pending; dataset-dependent reproduction is not applicable to this software-only follow-up and was not performed. Neither is included in passed counts.

## Boundaries

Reporting remains `DisabledReportingRepository`, with no Android network permission or backend connection. Automatic model warnings remain disabled/unapproved and the strict `> 0.5` classification rule is unchanged. The private training package was not accessed. No dataset-dependent evaluation or model modification was performed. Procedure-level results remain supplied evidence; calibration and prospective evaluation remain unestablished.

The Xiaomi secure-FRP issue remains an external blocker. Physical-device SMS, manufacturer behavior, TalkBack, landscape, broader screen coverage, prospective research evaluation and partner approval remain pending. Emulator stability is bounded software evidence, not production readiness or proof that an intermittent failure can never recur.
