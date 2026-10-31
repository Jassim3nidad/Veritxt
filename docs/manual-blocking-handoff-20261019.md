# Android manual-blocking handoff — 19 October 2026

The result-screen **Block Number** action now offers **Open blocked numbers** after confirmation. For incoming SMS with a numeric sender supplied by Android, the result displays the origin and labels the action **Block sender**. The confirmation displays the same number and offers **Copy sender number**; it never chooses a number from the message body. Multipart segments must agree on the numeric origin. Missing/alphanumeric origins and pasted/shared text remain unassociated with a sender.

The handoff uses Android's `TelecomManager.createManageBlockedNumbersIntent()` and checks `BlockedNumberContract.canCurrentUserBlockNumbers()`. The user verifies and enters or pastes the sender's number in Android's UI. No scan data or number is included in the intent. Unsupported devices/profiles and launch failures show manual instructions, also available directly from the confirmation.

Sender metadata stays with the text in the in-process pending-check cache, expires logically after ten minutes, and is consumed once or discarded on dismissal. It is absent from notification content/intents, app storage, saved state, and reporting. Editing or sharing other text detaches the sender. Opening Android clears the scan through the existing background-session policy. Returning does not reopen confirmation or claim a number was blocked. No blocklist is read or modified by Veritxt; no new permission or default-app role is requested. The privacy notice and SMS-consent copy explain temporary sender handling.

## Verification

- Selected-SVM APK and test APK built successfully; frozen model/adapter integrity checks passed.
- Unit tests: 38 passed, 10 existing optional private parity/export checks skipped; no failures. Sender tests cover numeric formatting, invalid/alphanumeric origins and mismatched multipart origins.
- Lint: zero errors, 11 existing warnings.
- API 36: four `ManualBlockingHandoffTest`, eight `RiskResultsTest`, four `PrivacyAndCheckPromptTest`, and four `SenderBlockingTest` cases passed across the final applicable runs. These cover cancellation, instructions without launch, confirmation invoking the handoff once, unavailable-service/activity/security fallbacks, no data/extras in the platform intent, risk-based button visibility, sender copying, no sender inferred from body text, sender clearing and notification privacy.
- The real Android UI handoff test passed: confirmation opened Android's own blocked-number activity; returning cleared both scan and sender and left no blocking dialog. The test captured the empty Android blocklist, without adding or blocking a number.
- A real emulator-modem SMS from a fictional sender passed through the actual selected-SVM detector, private High Risk notification, sender-bearing result, and sender-specific blocking confirmation. No number was blocked. Airplane mode was restored after testing.
- The first clipboard test found that emulator host-clipboard mirroring replaces clip descriptions, including the sensitivity hint. The final checks verify the copied number through the system clipboard and verify the outgoing sensitivity hint before publishing; they do not claim Android or host clipboard retention/security beyond this hint.
- Native Android screenshot: `output/manual-blocking-20261019/android-blocked-numbers.png` (local ignored output).
- Real incoming-SMS screenshots: `output/manual-blocking-20261019/incoming-scan-block-option.png` and `incoming-sender-confirmation.png` (fictional text and sender only).

Physical-device/vendor-specific behavior remains untested. System screen text and available controls depend on the installed Phone app.

References: [TelecomManager handoff API](https://developer.android.com/reference/android/telecom/TelecomManager#createManageBlockedNumbersIntent()), [blocked-number provider restrictions](https://developer.android.com/reference/android/provider/BlockedNumberContract).
