# Candidate handoff verification — 25 September 2026

Scope: review Mark's HANDOFF.md and only `smishguard_repo_update.zip`; preserve Android, private model, existing backend and API 36 reliability fixes. The two prohibited private archives were not accessed, opened, extracted, copied or used. No private inputs were requested. No candidate training, inference, source download, conversion, model rebuild or APK production occurred.

Initial commands: `git status --short`, `git branch --show-current`, `git remote -v`, `git log -6 --oneline`, `git branch -vv`, `git fetch origin`, `git rev-list --left-right --count HEAD...origin/codex/thesis-completion-package`. Clean branch at `a604e18eb2801bb557bbc54b500df965bb3c5750`; remote `https://github.com/Jassim3nidad/SMISHGUARD.git`; tracking counts `0 0`. No co-developer changes needed integration at that fetch.

## Checks actually executed

Commands below ran from repository root with Python 3.12.5. Counts do not include Mark's claimed executions or earlier Android runs.

| Command / check | Passed | Failed | Skipped | Scope |
|---|---:|---:|---:|---|
| `python scripts/verify_candidate_handoff.py --archive "C:\Users\Jassim Trinidad\Downloads\smishguard_repo_update.zip"` | 28 member checks; 10 source parses | 0 | 0 | Exact archive/member hashes, CRC on reads, paths/types/size bounds, privacy signals; no supplied code execution |
| `python scripts/verify_candidate_handoff.py` | Aggregate validation and stored-summary comparison | 0 | 0 | 30 metric rows, 20 reliability rows, two accepted source hashes; no archive needed |
| `research/.venv/Scripts/python.exe scripts/verify_research.py` | 45 | 0 | 0 | 38 existing + 7 new fixture/aggregate tests; includes research `pip check`, passed |
| `backend/.venv/Scripts/python.exe -m unittest discover -s backend -p test_backend.py -v` | 45 | 0 | 0 | Existing hardened backend; temporary fixture database only |
| `backend/.venv/Scripts/python.exe -m pip check` | Dependency check | 0 | 0 | No broken requirements |
| `python scripts/verify_safe_handoff.py` | 8 | 0 | 0 | Existing sanitized evidence and Android policy/static regression checks; no actual emulator execution |
| Android JVM, build, lint, emulators and physical device | 0 | 0 | Not run | No Android/build/runtime files changed; unnecessary for this review. Xiaomi secure FRP remains blocked |
| Private-input candidate fitting, inference, calibration/threshold reproduction and Kotlin parity | 0 | 0 | Not run | Outside authorized scope; supplied claims are not passes |

The first focused command, `$env:PYTHONPATH='research'; python -m unittest discover -s research/tests -p test_candidate_evidence.py -v`, had **6 passes, 1 failure, 0 skips**: a newly written assertion mistyped the pooled bin total as 1,316. Summing the supplied counts establishes 1,216; corrected only the assertion, not evidence. The full 45-test research suite subsequently passed all seven new tests. The focused run and full run overlap and are not distinct coverage. An initial display of source documentation hit the Windows console encoding limit; inspection resumed with `PYTHONIOENCODING=utf-8`. That was an inspection-output error, not an experiment or test result.

Additional read-only in-memory checks: separate and embedded handoffs match byte-for-byte; all 34 fresh rows are unique and covered by the 40 unique, finite-score parity cases. Only group totals and score/type summaries were displayed, never the fresh message bodies or phone-shaped literal. The aggregate report was generated with `$env:PYTHONPATH='research'; python -m smishguard.candidate_evidence > research/candidate_review/aggregate_check.json`. File hashes and all individual accept/reject decisions are in [archive_review.json](../research/candidate_review/archive_review.json). Supplied metric arithmetic is independently checked; underlying experiments and labels are not reproduced.

## Integration and research conclusion

Accepted only `calibration_metrics.csv` and `reliability.csv` into `research/candidate_review/`, plus an independently written review, archive manifest, aggregate checker/report and seven regression tests. Existing model evidence remains in place with a review pointer. No duplicate trainer is introduced. Strengthened `.gitignore` and index checks protect candidate exports, message-bearing probes, datasets and common fitted binary formats. File attributes preserve the two CSV source hashes without changing whitespace checks on other paths.

Candidate status: **under review, not deployed**. Reported everyday behavior improves, but recall falls and SSS ayuda/courier misses remain; saved scores also reveal a job-themed outside-scope miss. Fold-local calibration fitting is an improvement, but inherited parameter selection, transductive grouping, exposed fresh probes, sparse calibration bins and test-set threshold exploration prevent a clean independent deployment claim. See the [four evidence categories, methodology conflicts and prioritized research gates](../research/candidate_review/README.md).

No shipped model, `calibration_status`, strict `> 0.5`, reference expectation, caution band, automatic warning, Android network permission or reporting behavior changed. Reporting remains disabled; no backend deployment. Physical Xiaomi testing remains blocked by secure FRP. Existing API 36 evidence was preserved and not rerun.

## Final index and remote review

All 19 staged files were read from the index and compared to the reviewed working copies; Python/JSON were parsed and both accepted CSV index hashes match the original archive bytes. No private/generated path is tracked. `git diff HEAD --name-only -- android backend` is empty. No private model was opened to perform these checks.

`python scripts/check_staged.py` passed on 19 staged files. `git diff --cached --check` and `git diff --check` passed. Thirteen `git check-ignore --no-index -q -- <path>` probes cover root/research/training data, candidate export/guide, raw fresh/parity probes, joblib/safetensors, SQLite/database, research runs and Android build outputs. All are ignored. The existing Kotlin data package remains eligible for source control. An initial all-tracked-path audit exposed the new broad data-directory guard incorrectly flagging `PreferencesRepository.kt`; the guard and ignore exception were corrected and the focused seven-test suite reran **7 passed, 0 failed, 0 skipped**, including source-versus-CSV path assertions. The all-tracked-path audit then passed. No existing safeguard was weakened.

A final `git fetch origin` again returned `0 0` from `git rev-list --left-right --count HEAD...origin/codex/thesis-completion-package`; `git remote get-url --push origin` remained the expected repository. Commit/push are restricted to a normal update of this branch; no main merge or force-push. The resulting commit hash and push outcome are reported in the task response, avoiding a self-referential commit hash in this document.

Co-developer update, with local work preserved:

```powershell
git switch codex/thesis-completion-package
git pull --ff-only origin codex/thesis-completion-package
```

If fast-forward is refused, reconcile the co-developer's local work explicitly; do not reset or force-push.
