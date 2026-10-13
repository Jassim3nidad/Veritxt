# Remote physical-phone test

13 October 2026 update: physical-phone checks are completed as reported directly
by the user. The older pending form below is historical; exact tested build and
measured observations were not specified in this retraining chat. Software checks
and predictive/source-transfer validation remain distinct.

**Physical-device results: pending.** No groupmate test has been received. This is a short engineering check, not a new accuracy experiment. Use only the identical fictional examples below; keep real SMS and contacts out of screenshots and recordings.

The coordinator supplies private, verified LR/NB/SVM APKs from `deliverables/expanded-20261005/` and the repackaged mBERT APK from `deliverables/validation-20261006/`, with the matching SHA-256 manifests. Install only on an Android 8.0/API 26 or newer phone whose owner agrees. Record the exact APK hash/model ID. The four variants coexist; a same-algorithm installation replaces that variant. Preserve the old installers for rollback. Record storage/installation errors honestly; do not bypass device locks or protections.

1. Fill the device section of the private results form: anonymous tester/device code, manufacturer/model, Android version, RAM/storage if known, date, battery condition and test order. Do not record IMEI, phone number, account names or serial number. Choose an order before testing and rotate it across groupmates to reduce order effects.
2. Enable airplane mode and disable Wi-Fi. Launch each app in the recorded order with other SmishGuard variants closed. Record launch/model-loading time separately from scanning. Verify the displayed algorithm/model ID and the disabled reporting/automatic-warning behavior. Keep normal privacy controls and the minimalist UI unchanged.
3. Run P1–P4 by manual paste in every app, then share P1 from a local notes app. Never open the example URL. Photograph or record the actual result, score or abstention; do not change an unexpected answer to the intended example label.
4. Run the empty and random-input checks. Construct the long-input probe from P1 repeated 100 times locally. Record actual behavior, responsiveness and any crash. Use fictional content only.
5. For simple manual timing, force-stop and reopen for three cold trials per app. Separately perform 20 unrecorded warmup scans cycling P1–P4, then record 20 warm scans (five cycles). Prefer a screen recording; time from pressing Check to visible result using its timestamps. Enter milliseconds only when measured, with the method and trial number. Manual UI timing includes rendering/touch delay and is not directly comparable with instrumented emulator inference. If timing cannot be measured, leave it blank and explain.
6. Return the filled form and privately shared evidence references. Record every installation failure, crash, abstention and incorrect example result. Restore the phone's previous network state afterward. The coordinator checks completeness and hashes before summarizing. A blank return is not a pass.

| Probe | Paste exactly | Intended purpose |
|---|---|---|
| P1 | Your account is suspended. Verify your password at https://account.example now. | Fictional English phishing example |
| P2 | Bayad na po. Salamat sa tulong, kita tayo bukas. | Fictional benign Taglish example |
| P3 | Hello po | Short Taglish policy check |
| P4 | Your payment is received. | Short English policy check |
| E1 | Leave input empty | Empty-input behavior |
| E2 | qwerty | Random-input behavior |
| L1 | P1 repeated 100 times, separated by spaces | Long-input behavior |

Record all model outcomes without checking an expected answer in advance. These same messages are shared by all variants. Prospective research intake is a separate workflow, and no fictional phone-test input may enter that evaluation. Current emulator results and APK hashes are documented separately; no physical performance is inferred from them.
