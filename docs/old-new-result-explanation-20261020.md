# Why the original and current APK show different risk labels

The exact cashback message in the user's screenshots was submitted to both APKs on the API36 emulator:

`[EWB]You have PHP 5,216 available for cashback. Claim it before it expires today. https://eastwinfu.com/ph`

Both classify it as phishing. The difference in red/amber and High/Medium comes from changed result rules, rather than disagreement on the binary class.

| APK | Native result reproduced |
|---|---|
| Original ZIP APK, package `ph.smishguard.svm.selected.update` | Likely phishing (scam); Warning signs: High |
| Current all-SMS APK, package `ph.smishguard.svm.oldbinary` | SMS category: Smishing; Medium Risk; Risk Score: 40/100 |

The model asset in both has SHA-256 `15cc0105b0e51e5342682ea36896c4436e515c39d165faf040476046b6b8059c`.

## Confirmed result-rule difference

Disassembly of the original APK's `ph.smishguard.WarningLevel.Companion.of` shows that `result.suspicious == true` directly produces `WarningLevel.HIGH`. A negative model result with at least two hints produces SOME; otherwise it produces FEW. The original High label is not the current numeric risk calculation.

The current `RiskPolicy` assigns a positive model classification 40 points. Medium Risk covers 30–69; High Risk begins at 70. For this message, the model flag is the only scoring indicator. A recognized organization and a link are displayed as context with zero points. The current urgency/reward patterns do not match this particular cashback/expiry phrasing. The separate cashback review override is disabled in the Ham/Smishing build. The resulting score is therefore 40, displayed consistently as Medium Risk.

This is a difference in application decision/presentation policy, not merely a wrong color or text rendering. The recent all-SMS-notification update did not change this risk calculation.

## Additional preprocessing difference

Matching weights do not establish identical end-to-end inference. The original APK contains only `assets/model.json`. Its `CheckViewModel.scan` passes the submitted text to `SmishGuardApp.assess`, which forwards it to `SelectedSvmDetector.detect`; the detector tokenizes and scores that input directly. These call paths were checked in the original DEX.

The current app additionally uses the frozen `RawSmsView` adapter, preparing `clean(mask(clean(raw)))` before scoring, as expected by the selected training pipeline. It replaces URLs and digit sequences with the training placeholders. This can change model scores even with identical weights.

A reference replay against the matching frozen pipeline gives 0.5786125067800187 for the raw message and 0.8037948780036812 for the prepared message. Both exceed the same stored threshold, 0.36999999999999994, so the binary prediction remains positive. These are reference model scores, not the displayed risk index or validated probabilities; the native UI comparison above independently confirms both positive classifications.

The earlier statement that the model was preserved refers to its fitted parameters. It should not be read as a claim that the original APK and the latest app have identical preprocessing or result policies.

## Evidence

- [Original native result](../output/old-new-result-comparison-20261020/old-result.png)
- [Current native result](../output/old-new-result-comparison-20261020/new-result.png)
- Native UI text and package evidence: `output/old-new-result-comparison-20261020/native-results.json`.
- Original DEX disassembly: `output/old-new-result-comparison-20261020/classes3.dex.txt` and `classes4.dex.txt`.
- Current policy: `android/app/src/main/java/ph/smishguard/model/RiskAssessment.kt`.
- Current preprocessing: `android/app/src/main/java/ph/smishguard/model/RawSmsView.kt` and `SelectedSvmDetector.kt`.

The original APK was installed alongside the current app on the emulator for this comparison. No application source, model, threshold or risk rule was changed during this investigation.
