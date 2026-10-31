# Scan risk policy and validation

Implemented 19 October 2026. Policy version: `evidence-index-v1`.

20 October update for the Ham/Smishing (`oldSvm`) variant: the application opts into `linked-cashback-claim-deadline-v1`. A cashback/rebate claim with an expiry deadline and a parseable link contributes the existing 30-point cashback cue. Combined with a model flag (40), this produces High Risk at 70. A model flag alone remains Medium Risk. See [the user-selected supporting-evidence policy and verification](linked-cashback-risk-20261020.md). The base policy and other variants described below remain available.

## Scope and meaning

The existing Android SMS paste/share result screen and incoming-SMS warning path now use one `RiskPolicy`. Embedded URL indicators use the same rules. The shared text entry also recognizes a standalone URL, email address, phone number, or email text with `From:`, `To:`, or `Subject:` headers. No separate scan screens or network services were added. Headerless prose remains SMS input; this application cannot reliably infer its original channel.

| Classification | Displayed integer score | Meaning |
|---|---:|---|
| Low Risk | 0–29 | No significant indicators detected by available checks; authenticity is not established. |
| Medium Risk | 30–69 | Suspicious elements warrant independent verification. |
| High Risk | 70–100 | Strong indicators warrant avoiding interaction and considering blocking/reporting. |
| Unable to assess | None (`null`) | Insufficient evidence, unsupported input, missing/invalid model, failed/busy check, or synthetic model fixture. |

The score is an **ordinal evidence index**, not a probability, model confidence, expected loss, or a NIST risk calculation. Classification always uses the displayed integer score through `RiskPolicy.classify`; model thresholds and display rounding cannot create contradictory risk labels. Model inference parameters, thresholds, calibration metadata, and research parity contracts remain unchanged. Raw model output and its exact threshold appear separately in the explanation dialog for assessed SMS only.

All result cards use Risk Level, Risk Score (omitted for abstention), Analysis, Detected Indicators, and Recommended Action. Existing green, amber, and red design tokens remain; abstention uses neutral gray. Text labels, heading semantics, and the polite live region communicate the result without relying on color. English and both existing Filipino resource sets use the same structure and advice.

## Evidence criteria

These weights express relative evidence strength and action priorities. They are **provisional engineering decisions**, informed by the sources below, not coefficients estimated by those studies. No cited authority establishes these exact numbers.

| Indicator | Points, once per input | Reason and limitations |
|---|---:|---|
| Request to send/share an OTP, PIN, password, CVV, or other credential | 70 | Direct credential disclosure is a strong social-engineering indicator. A credential mention by itself does not qualify. Sentence-local negation suppresses common security advice. Quoted examples, complex negation, and unfamiliar wording can still be misread. |
| SMS model flags the input under its frozen decision rule | 40 | Supporting contextual evidence; the experimental model alone cannot produce High Risk. Raw outputs are not rescaled into percentages or mixed across different model scales. |
| Credential entry/verification request | 30 | Distinct from sending credentials to someone; ordinary sign-in instructions can legitimately contain this request. Verification is appropriate. |
| Payment/money-transfer request | 30 | Needs independent verification; legitimate bills and deliveries can also match. |
| URL containing user information, an IP address, or a punycode hostname | 30 | Can obscure the destination; also used legitimately. This is a structural check, never a malicious-domain verdict. |
| Urgency/account restrictions | 10 | Weak contextual cue; ordinary urgent messages exist. |
| Prize/reward language | 10 | Weak cue shared by legitimate announcements. |
| Recognized URL shortener | 10 | Final destination is hidden; shortening does not establish fraud. |
| A link or recognized organization name appears | 0 | Context only; neither proves impersonation or fraud. An unfamiliar phone number also contributes no points. |

Each indicator counts once, repeated cues cannot inflate the score, and the total is capped at 100. Requests are evaluated outside URL paths/query strings and email addresses. Credential disclosure and credential entry do not double-count each other. A Low Risk message needs an assessable, nonsynthetic SMS model result; otherwise, absence of positive evidence yields abstention. A standalone URL or email body can produce Medium/High Risk from positive visible indicators, but cannot receive Low Risk merely because no indicator matched. A bare phone number or email address always abstains, even if a detector supplies a very high score. Non-SMS input bypasses SMS model inference.

### Verified, suspected, insufficient

Current outputs distinguish suspected indicators, absence of significant indicators, and insufficient evidence. **This offline app cannot verify a threat.** It has no live malicious-domain feed, URL fetch/redirect analysis, attachment scanning, phone reputation service, email authentication check, or verified sender registry. A link to a known malicious destination could be missed unless visible cues or the SMS model identify suspicious content. No fabricated domain blacklist, positive reputation result, or confirmed-fraud claim has been added. Verified-threat status would require an authenticated, current, provenance-bearing source and matching/expiry tests before activation.

The inherited organization-name matcher is used only as a zero-point identity claim. It is not an official-domain allowlist. No organization name or apparently familiar domain cancels other indicators. Indicator text explains observable cues, not the model’s internal reasoning.

## Threshold decision and evaluation

Retain the requested boundaries **30 and 70** for the initial implementation. They separate weak contextual cues, verification-worthy requests/model evidence, and strong disclosure or combined evidence. They have not been established as optimal thresholds for any installed model or Philippine deployment population.

`RiskEvaluationTest` runs 38 authored, labeled, fictional cases: 16 legitimate scenarios, 16 malicious scenarios, and six insufficient-input scenarios. With injected model flags as controlled inputs, Medium/High counted as positive:

| Result | Count |
|---|---:|
| True positives | 14 |
| False positives | 2 |
| True negatives | 14 |
| False negatives | 2 |
| Correctly unscored insufficient cases | 6 |

The two false positives are legitimate credential-entry and payment requests, both Medium Risk. The two false negatives are a subtle account-review lure and a conversational channel-switch lure with a negative model signal. These cases demonstrate why Low Risk cannot guarantee authenticity and Medium Risk must recommend verification rather than assert fraud. The fixture deliberately records these errors. It does not relabel them to obtain perfect accuracy.

Testing led to distinguishing credential entry (30) from disclosure (70), suppressing common negated requests, ignoring requests inside URL paths, recognizing a URL before email-like `userinfo@host`, and preserving the assessment when message text is cleared on reporting navigation. The band boundaries were retained: changing them to fit these small hand-authored cases would overfit. The companion test also evaluates available frozen development LR and selected SVM assets on the same labeled scenarios and emits aggregate counts without private weights or messages. See [machine-readable evaluation](risk-evaluation-20261019.json) for the actual executed results.

Actual frozen-model results on those same fictional scenarios, using Medium/High as positive:

| Model | True positive | False positive | True negative | False negative | Insufficient cases unscored |
|---|---:|---:|---:|---:|---:|
| Development LR | 15 | 9 | 7 | 1 | 6 |
| Selected SVM | 15 | 6 | 10 | 1 | 6 |

All of these legitimate positive results were Medium Risk. At the separate High Risk boundary of 70, each model produced 12 true positives, zero false positives, 16 true negatives, and four malicious scenarios below High Risk. Three of those four still received Medium Risk verification advice; one remained Low Risk. This supports keeping verification advice distinct from stronger warnings on this fixture, while also exposing a substantial false-verification burden from the models. It does not establish a real-world false-positive rate or validate either threshold. No parameters were tuned on these evaluation cases.

**These are regression checks, not independent model accuracy, calibration, or population estimates.** Existing research results predate this combined risk policy and cannot validate it. Prospective validation must freeze the combined rules first, use independently adjudicated legitimate/malicious samples with grouped source/time-separated validation and final test partitions, include ordinary OTPs, bank notices, legitimate payments, Taglish, unseen brands, and URL-only cases, and report class-specific errors, coverage/abstention, and uncertainty. Evaluate both the 30 verification threshold and 70 warning threshold. Select any future weights/thresholds on validation data only, document false-positive/false-negative tradeoffs, then evaluate the untouched final test set. Probability claims additionally require calibration and held-out reliability evaluation.

## User-controlled blocking and warning behavior

There was no automatic-number-blocking implementation in the inspected app. The app never writes Android’s blocked-number provider. This change adds no blocking permission or default-dialer role. For incoming SMS, a numeric origin supplied by Android now travels with its text through the in-process pending-check cache. All multipart segments must agree on the normalized number; missing, alphanumeric, inconsistent, or invalid origins have no associated phone number. This is a sender address, not verified identity, and never changes the risk score. Pending entries expire after ten minutes or are consumed/dismissed once; no sender is written to app storage, logs, saved state, notifications, or notification intents.

For Medium/High Risk SMS, **Block sender** appears when a numeric sender is available, and the result and confirmation show that number. **Copy sender number** explicitly copies only that origin to Android's clipboard, marked sensitive; nothing is copied automatically. **Block Number** remains the generic guidance action for text without sender metadata, with an explanation that a pasted/shared message does not establish its sender. Cancel/back/dismiss returns without blocking. **Open blocked numbers** uses `TelecomManager.createManageBlockedNumbersIntent()` after checking `BlockedNumberContract.canCurrentUserBlockNumbers()`. The user verifies, adds or pastes, and confirms the sender in Android's UI. No message or phone number is passed in the intent. Missing services, unsupported profiles, and launch failures show manual instructions instead. **Show instructions** is also available before launching. No embedded phone number is assumed to be the sender, no blocklist is stored, and no success claim is shown. Bare-number scans offer the same optional handoff without recommending blocking on the basis of unfamiliarity. Low Risk has no blocking suggestion or button. URL/email inputs have no phone-blocking button. Opening Android clears the scan through the existing background-session policy; returning does not reopen the confirmation or imply a number was blocked.

High Risk emphasizes avoiding interaction and considering blocking/reporting. Medium Risk emphasizes independent verification. Low Risk recommends ordinary caution without unnecessary blocking. Unable to assess requests more information or official-channel verification. Existing incoming-warning consent, permissions, and build approval still apply; only High Risk under the shared policy can trigger the existing generic notification. Warnings do not block/delete messages or numbers. Reporting remains disabled; the historical backend model-score payload contract is unchanged and is not the new risk index.

Results, sender, and blocking-dialog state remain in memory only. Editing or sharing new text detaches any old sender. Starting another check, navigating away, or leaving the app clears the scan session. Reporting navigation preserves the nonidentifying risk assessment while clearing the submitted message and sender, so returning does not change its classification. The privacy notice and incoming-SMS consent explain temporary sender handling and explicit clipboard copying.

## Research and platform references

- [NIST SP 800-30 Rev. 1](https://csrc.nist.gov/pubs/sp/800/30/r1/final), especially §2.3 and §3: supports explicit assessment assumptions, evidence, uncertainty, and repeatable organization-specific methods. Its organizational likelihood/impact framework does not validate a per-message phishing score or prescribe these thresholds. This app borrows transparency principles, not NIST certification.
- [FTC: Recognizing phishing](https://consumer.ftc.gov/articles/how-recognize-avoid-phishing-scams): supports credential theft, impersonation, account/payment pretexts, and independent verification through a known channel.
- [FTC: Spam text messages](https://consumer.ftc.gov/articles/how-recognize-and-report-spam-text-messages): supports identifying reward/delivery lures and offering user-controlled blocking/reporting options.
- [Timko and Rahman, Commercial Anti-Smishing Tools and Their Comparative Effectiveness Against Modern Threats (WiSec 2023; revised 2024)](https://arxiv.org/abs/2309.07447): the authors’ small testbed found both missed attacks and substantial benign blocking in some tools. This motivates evaluating both error types and keeping blocking voluntary; it supplies no weights for this implementation.
- [Tabassum, Faklaris, and Lipford, SOUPS 2024](https://www.usenix.org/conference/soups2024/presentation/tabassum-sarah): interviews with 29 users highlight message content, links, and context in judgments. This supports showing specific evidence and verification steps, not treating sender unfamiliarity as proof.
- [Android BlockedNumberContract](https://developer.android.com/reference/android/provider/BlockedNumberContract): blocked-number provider access is restricted to eligible system/default-role apps. Veritxt does not request those roles or modify the provider.
- [Android TelecomManager.createManageBlockedNumbersIntent](https://developer.android.com/reference/android/telecom/TelecomManager#createManageBlockedNumbersIntent()): supported handoff to Android's user-managed blocked-number screen, with manual instructions when unavailable.

Sources checked 19 October 2026. References support indicator selection and product safeguards; numerical weights and operating thresholds remain provisional pending representative evidence.

## Reproduce software checks

From the repository root, run `scripts/build.ps1 -Variant selectedSvm` for build, lint, and unit tests, or use `-Variant debug` in a checkout without private model assets. The ordinary public checkout skips optional private-model parity checks. The authored risk fixtures always run; actual-model scenario evaluation runs when the private development/selected-SVM assets are available. No training or model substitution occurs.

For test-only emulator UI verification, build `:app:assembleSelectedSvmAndroidTest -PinstrumentedBuild=selectedSvm`, install the two matching APKs on a verified emulator, and run `RiskResultsTest`, `CompactResultTest`, `FlowsTest`, `AccessibilityTest`, and `PrivacyAndCheckPromptTest` through `SoftwareTestRunner`. `RiskResultsTest` covers manual-blocking confirmation/cancellation, low-risk suppression, bare-number abstention, URL/email limitations, and risk stability after reporting navigation. Fixtures are fictional; no real number is blocked. The test-only `diagnostics=true` argument enables rendered layout evidence without removing production screenshot protection.

Recorded execution: **36 unit tests passed**, ten existing optional private parity/export tests skipped without configured parity directories, **23 API 36 UI/privacy/accessibility tests passed**, and **one actual selected-SVM incoming-SMS emulator test passed**. The latter verified High Risk notification privacy and the matching result opened by See why. Emulator radio must be enabled for SMS delivery; the initial radio-off attempt timed out and the radio-enabled retry passed, after which the original airplane-mode setting was restored. Selected-SVM APK build and lint passed (zero errors; 11 warnings). Model and adapter hashes were unchanged. See [aggregate verification evidence](risk-verification-20261019.json).
