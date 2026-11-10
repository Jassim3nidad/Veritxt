# Branch integration review — 10 November 2026

Reviewed and integrated into `main` at the user's request:

- PR #5, `notification-risk-meter`, commit `41980b0`: shield notification meter and band-boundary tests.
- PR #6, `scoring-fix-v2`, commit `96b627f`: variant-specific scoring rules and per-message score breakdown.

The `veritext-rename`, `score-ux`, and `codex/sync-ui-and-pending-changes` branch tips were already ancestors of `main`. Both remaining branches merged without conflicts. Review found no blocking code-integration defect; no implementation changes were needed.

The combined source preserves the trained model, model decision threshold, and 30/70 risk-band boundaries. Scoring v2 is enabled for `selectedSvm`, `oldSvm`, and `usbDemo`; the other variants retain their existing policies. Notification rendering uses the shared risk-band classifier.

## Verification of the combined source

| Check | Result |
|---|---|
| Debug APK build | Passed |
| Debug lint | 0 errors, 52 warnings |
| Debug unit tests | 74 total; 58 passed, 16 skipped |
| Selected SVM unit tests | 74 total; 58 passed, 16 skipped |
| Old SVM unit tests | 74 total; 58 passed, 16 skipped |
| USB demo unit tests | 76 total; 60 passed, 16 skipped |
| Selected SVM APK and instrumented-test APK builds | Passed |
| Android 16 / API 36, `AllSmsNotificationsTest` | 12 passed |
| Android 16 / API 36, `CompactResultTest` | 7 passed |
| Android 16 / API 36, `RiskResultsTest` | 8 passed |
| Git whitespace/conflict-marker check | Passed |

The 16 skips per unit-test variant require separately configured private model/parity fixtures. Local frozen SVM assets were used for build verification and were not committed. Testing used the dedicated `SmishGuard_Test_API36` emulator, not a physical phone. The full instrumented suite, including the API 36 `FlowsTest` failure reported in PR #6, was not rerun.

## Remaining scoring validation

PR #6 reports two unfinished empirical checks: fewer than 1% of held-out normal messages classified High Risk, and no verified bank promotions classified High Risk. Neither check was completed in this integration review. Passing software tests does not establish these false-alert rates or validate the provisional 0.90 model-score rule. The scoring change remains experimental; the PR's development-set figures are not independent accuracy evidence.

Pre-existing local documentation, notebook, and demo edits were kept outside this branch integration.
