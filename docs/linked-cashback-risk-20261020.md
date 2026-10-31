# Supporting evidence for High Risk in the Ham/Smishing app

The user requested High Risk for the cashback SMS and selected **Require supporting warning signs**, rather than automatically treating every positive model prediction as High Risk.

The Ham/Smishing variant now uses risk profile `linked-cashback-claim-deadline-v1`. Its existing model flag contributes 40 points. A cashback/rebate offer with a positive claim/redeem/collect action, a nearby expiry deadline and a parseable link with a hostname contributes another 30 points. Together these produce **High Risk, 70/100**. A model flag alone remains **Medium Risk, 40/100**. The cue without a model flag produces Medium Risk at 30 points, rather than High Risk.

The rule checks prose outside links, ignores negated claim advice, and counts the cue once. It does not depend on an EastWest/BPI name, the reported amount or a particular domain. The existing cashback/rebate matcher and its 30-point weight are reused; the Ham/Smishing profile additionally requires a link. Other model variants retain their established profiles, including the older separate cashback-review build.

## Why no model was retrained

The saved classifier already predicts **Smishing** for the reported SMS. Its reference score is 0.8037948780036812 at the unchanged inclusive threshold 0.36999999999999994. The former Medium Risk result came from the separate 40-point model indicator, which is independent of how far the classifier score exceeds its threshold. Retraining the binary model would not remove that rule.

The inspected training datasets contain binary Ham/Smishing labels, or Ham/Smishing/Gambling classes in the separate multiclass experiment. They contain no Low/Medium/High severity labels. A supervised risk-level model would require defined severity criteria and independently labeled examples. No severity labels were fabricated, no fit was performed, and the reported SMS was not inserted into training.

The fitted classifier, tokenizer, vocabulary, IDF, coefficients, sigmoid, decision threshold and raw-SMS adapter remain unchanged. Model SHA-256: `15cc0105b0e51e5342682ea36896c4436e515c39d165faf040476046b6b8059c`.

## Expected behavior

| Input and model result | Risk outcome |
|---|---|
| Reported cashback claim + expiry deadline + link, model flags Smishing | High Risk, 70/100 |
| Same message without a link | No new cashback points; model flag alone remains Medium Risk |
| Linked cashback offer without a claim action or deadline | No new cashback points |
| Cashback already credited / no action required | No new cashback points |
| Advice not to claim cashback from unsolicited links | No new cashback points |
| Linked cashback claim with deadline, model predicts Ham | Medium Risk, 30/100; model category remains Ham |
| Other model flag without supporting evidence | Medium Risk, 40/100 |

Additional existing indicators can increase the total. Risk scores remain a provisional evidence index, not a fraud probability or a verified malicious-domain finding. Regression checks establish the implementation behavior; they do not establish representative accuracy or validate the risk weights.

Manual results and incoming SMS use the same application risk policy. The previously requested notifications for every SMS are retained: other results get the neutral prompt, and High Risk gets the warning. The English and Filipino explanation dialog describes the added evidence and points.

## Build and verification

Build the current `oldSvm` variant using `scripts/build_old_binary_svm.ps1`. Run `python scripts/verify_all_sms_notifications.py --linked-cashback --output <fresh-output-directory>` to check frozen-model parity, routing/failure/privacy controls, the real-model cashback UI and all SMS modem paths, including the reported cashback message as High Risk.

Detailed results and APK hashes are supplied with the new delivery under `deliverables/Veritxt-Context-Risk-20261020/`. Earlier APKs remain in their existing folders for comparison.

Current checks passed: application/test assembly, lint with zero errors (12 warnings), 53 JVM tests with 11 conditional skips, and 17 Android tests on the API36 emulator. The real-model UI reproduced Smishing / High Risk / 70 with the unchanged model score, checked the no-link control, and kept an ordinary message Ham / Low Risk. Actual modem delivery verified Low, Medium, High and unassessable messages, plus the reported cashback SMS as High Risk at 70. Each produced one private notification and opened its exact message. Existing notification actions, expiry, privacy gates and frozen-model parity (515 model plus 33 raw-input cases) also passed. No physical-phone test is claimed.
