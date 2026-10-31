"""Document the exact SVM 60% application decision, independently of thesis conclusions."""
from pathlib import Path
import argparse
import shutil
from smishguard import multiclass_comparison as m

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package',type=Path,required=True);parser.add_argument('--verification',type=Path,required=True)
    parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    package,verification,report=args.package.resolve(),args.verification.resolve(),args.report.resolve()
    record=m.load(package/'build-verification.json');assert m.legacy.digest(record['apk'])==record['apk_sha256']
    integration=ROOT/'research/runs/svm60-android-20261020';export=integration/'export-v1'
    practical=m.load(export/'practical-comparison.json')['cases'];native=record['parity'];jvm=m.load(export/'svm60-jvm-parity.json')
    practical_android=m.load(verification/'practical-android-parity.json')
    report.mkdir(parents=True,exist_ok=True)
    for name in ['build-verification.json','SHA256SUMS.txt','Ham.png','Smishing.png','Gambling.png']:
        shutil.copyfile(package/name,report/name)
    for name in ['practical-comparison.csv','practical-comparison.json','export-manifest.json','svm60-jvm-parity.json','practical-jvm-parity.json']:
        shutil.copyfile(export/name,report/name)
    for name in ['emulator-results.json','svm60-android-parity.json','practical-android-parity.json']:
        shutil.copyfile(verification/name,report/name)
    for name in ['build.log','signature-final.txt']:shutil.copyfile(integration/name,report/name)
    labels=m.NAMES
    def margins(scores):return ', '.join(f'{v:.6f}' for v in scores)
    def safe(text):return text.replace('|','\\|').replace('\n',' ')
    comparison_table='\n'.join('| '+ ' | '.join([safe(r['text']),labels[r['svm60']['prediction']],margins(r['svm60']['scores']),
        labels[r['svm80']['prediction']],margins(r['svm80']['scores']),'Unavailable','Yes, both models'])+' |' for r in practical)
    test_table='\n'.join(f'| {key} | {count} | Passed |' for key,count in record['emulator_tests'].items())
    cash=practical[0]
    oldapk=ROOT/'deliverables/multiclass-svm-80-20261020/VeriTxt-LinearSVM-80-New-debug.apk'
    text=f'''# VeriTxt SVM 60% application deployment — 20 October 2026

The requested exact frozen SVM 60% model has been integrated, built into a new debug APK, and tested on an API {record['api']} emulator. The SVM 80% APK, both frozen Python pipelines, original dataset and completed research results are preserved.

**The switch does not fix the cashback example. Both frozen Python models and their Android scorers return Ham for that input, and the unchanged risk rules return Low Risk, 0/100.** The 20 documented practical inputs produced identical category predictions across the two models. This is the user's requested application testing choice, not measured proof that the 60% model is superior. The thesis's original controlled 80% comparison and its uncertainty are unchanged.

## New APK and exact source

- APK: `{record['apk']}` ({record['apk_bytes']:,} bytes).
- APK SHA-256: `{record['apk_sha256']}`.
- Build: **debug**, signed using the existing local debug configuration; APK Signature Scheme v2 verified. No signing credential was created or exposed.
- Launcher label: **VeriTxt · SVM 60%**.
- Application ID: `{record['package']}`; version `{record['version']}`.
- Minimum API 26 / Android 8.0; target/compile API 36. Only API {record['api']} runtime testing was performed.
- Source: `{ROOT / 'research/runs/multiclass-20261020/run-v1/svm-60.pkl'}`.
- Source pipeline SHA-256: `{record['source_model_sha256']}`.
- Packaged `assets/model.json` SHA-256: `{record['packaged_model_sha256']}`.

The frozen study's selection.json, configuration.json, environment.json, training-seal.json, PROTOCOL.md and THESIS-REPORT.md were inspected. The actual artifact verifies LinearSVC(C=10), classes [0,1,2], 30,227 features and three coefficient rows. It was fitted on the 2,281-record training portion; 761 validation records selected C, and 761 test records formed the shared final evaluation. Validation records were not incorporated into fitting this model. No new training, calibration, threshold tuning or thesis-test evaluation was run.

Class mapping remains 0=Ham, 1=Smishing, 2=Gambling. This model is neither the 3,042-record `svm-80.pkl` nor a historical binary SVM. File hashes, metadata, dimensions and explicit build-selected training percentage prevent substitution.

The distinct package suffix allows both application versions to remain installed. Open the new **SVM 60%** app to use this model; the previous SVM 80% application is not silently replaced or redirected.

## Original issue and risk investigation

The message was:

> {cash['text']}

| Frozen pipeline | Prediction | Ham margin | Smishing margin | Gambling margin |
| --- | --- | ---: | ---: | ---: |
| SVM 60% | {labels[cash['svm60']['prediction']]} | {cash['svm60']['scores'][0]:.9f} | {cash['svm60']['scores'][1]:.9f} | {cash['svm60']['scores'][2]:.9f} |
| SVM 80% | {labels[cash['svm80']['prediction']]} | {cash['svm80']['scores'][0]:.9f} | {cash['svm80']['scores'][1]:.9f} | {cash['svm80']['scores'][2]:.9f} |

Both choose the largest raw margin, Ham. Margins are uncalibrated one-versus-rest decision values, not probabilities or the app's risk index. This comparison does not authenticate EWB or verify that the message is fraudulent. No independent human-verified expected label was supplied. If independently confirmed as fraudulent, the Ham outcome would be a false negative for both models.

The risk score is a separate existing heuristic system in RiskAssessment.kt. It combines credential/payment requests, selected urgency/reward keywords, certain URL indicators and a model signal. A Smishing prediction supplies 40 points; a Ham or Gambling prediction does not. The score is Low below 30, Medium from 30 through 69 and High from 70 onward. These thresholds are unchanged.

The cashback example receives no model-signal points because it is Ham. The existing reward expression includes `won`, `winner`, `prize`, `claim your`, `nanalo` and `premyo`, but not `cashback` or `claim it`. The urgency expression does not include `expires today`. There is no matching request for credentials/payment in the supplied text, and it contains no URL. An identity hint, if detected, carries zero points. Thus no positive-weight indicator fires and the risk score is zero. **Zero is not a 0% fraud probability or a guarantee of safety.** The inherited reassuring wording remains a known limitation.

RiskAssessment.kt was hash-checked unchanged. No heuristic, risk weight, risk threshold, warning condition or safety override was added. Android tests separately verify the cashback result is Ham/Low/0 under both models, and that an explicit credential-request example can trigger High Risk through the existing rules independently of a model prediction.

## Exact inference integration

The new export copies the fitted vocabulary in its original index order, IDF array, 3×30,227 coefficients and three intercepts. Arrays were verified for exact equality after JSON serialization. Unicode tables and tokenizer settings come from the already verified shared feature contract, and vectorizer parameter dictionaries were checked equal across the two original pipelines.

Preprocessing remains whitespace collapse and Python-compatible Unicode 15 lowercase, including expanding lowercase and Greek final sigma. The original URL/currency/number/Unicode-word token pattern, 13 conservative stopwords, stopword removal before bigrams, unknown-token adjacency, raw TF, smooth IDF and L2 normalization are retained. No masking adapter, translation, stemming, probability sigmoid, new learned transform or feature approximation is introduced. All three margins use the original dot products and intercepts. Argmax selects the first class on an exact tie, including when all scores are negative.

MulticlassSvmDetector now supports explicitly requested 60% and 80% identities while sharing unchanged numerical inference. The default remains 80% for the old build. The `multiclassSvm60` build explicitly requests 60%, pins the new export hash and validates the 60% source artifact/version/features/training count. The old build and model asset remain available for rollback. The new application APK contains exactly one asset, the 60% `model.json`; the 80% model is used only in the separate test APK for comparison and is absent from the new application APK.

The current three-category UI and separate risk display remain. The only visible identification change is SVM 60% in the app label/header/status. Manual checks, pasted/shared SMS, notification-opened checks and opt-in incoming-SMS classification use the same active 60% detector. Consent, settings, languages, themes, privacy clearing, disabled reporting and Android blocking handoff are retained. No READ_SMS, INTERNET or other new Android runtime permission was added; existing RECEIVE_SMS and POST_NOTIFICATIONS remain. The app still has no persisted inbox/history or bulk historical inbox scanner.

Blank/invalid/over-limit input handling is retained separately from mathematical model scoring. Raw mathematical parity includes intercept-only predictions on empty/OOV input. The app still abstains on blank inputs and standalone phone/URL/email inputs and rejects malformed NUL/unpaired-surrogate or over-limit text. These guards do not retune the selected model.

## Practical comparison before switching

The exact user-provided example and 19 documented synthetic scenarios were transformed by both frozen Python pipelines before replacing the app's inference path. Scenarios cover informational/conversational SMS, cashback and expiry language, simulated bank/delivery/credential lures, shortened and ordinary URLs, Filipino/Taglish, unknown sender-style names, gambling and short/ambiguous text. Scenario descriptions are intended test construction, not reliable fraud labels. None has an independently verified human label; no accuracy or empirical superiority is calculated from this set.

Decision scores below are ordered **Ham, Smishing, Gambling**. Complete precision and provenance are retained in practical-comparison.json/CSV; observed Android scores are in practical-android-parity.json. Each model's Android prediction matches its frozen Python prediction on every row. Across models, all 20 predicted labels agree; differing margins do not establish that one model has higher calibrated confidence.

| Input SMS | SVM 60% | 60% margins | SVM 80% | 80% margins | Human-verified label | Android matches Python |
| --- | --- | --- | --- | --- | --- | --- |
{comparison_table}

## Numerical consistency and model selection guards

| Check | JVM | Android API {record['api']} |
| --- | ---: | ---: |
| 60% parity fixtures | {jvm['cases']} | {native['cases']} |
| Matching labels | {jvm['matching_predictions']} | {native['matching_predictions']} |
| Mismatches | {jvm['mismatches']} | {native['mismatches']} |
| Maximum margin error | {jvm['maximum_score_error']:.3g} | {native['maximum_score_error']:.3g} |
| Maximum TF-IDF error | {jvm['maximum_feature_error']:.3g} | {native['maximum_feature_error']:.3g} |
| Absolute tolerance | 1e-10 | 1e-10 |

The independent fixture set contains practical inputs, synthetic/Unicode/whitespace/URL/number/tokenizer stress cases, empty/long/invalid inputs, 400 deterministic fuzz probes and coverage of every 60% vocabulary term. It contains zero thesis test messages. The active app path matched direct model handling on {native['app_path_cases']} message-shaped fixtures within app boundaries. In addition, the practical comparison checked {practical_android['matching_predictions']}/{practical_android['predictions_checked']} model predictions across both frozen models, with zero mismatches and maximum margin error {practical_android['maximum_score_error']:.3g}. These are software consistency tests, not classification accuracy estimates.

Tests verify the actual detector reports trainingPercent=60, reject an 80% asset when 60% is requested, reject a 60% asset when 80% is requested, and preserve correct class order and exact tie behavior. Android initialization therefore cannot silently succeed with an old or differently trained model.

## Build and device verification

The Gradle build completed successfully: assembleMulticlassSvm60, lintMulticlassSvm60, testMulticlassSvm60UnitTest and assembleMulticlassSvm60AndroidTest. Lint: {record['lint_errors']} errors, {record['lint_warnings']} warnings. Host unit tests: {record['unit_tests']['tests']-record['unit_tests']['skipped']} passed, {record['unit_tests']['skipped']} skipped for other/private variants, zero failures/errors. All three new SVM 60% unit tests executed and passed. The existing local debug signature verifies with APK Signature Scheme v2. Packaged model bytes were checked against the exact export before installation and packaging.

The exact APK checksum in this report was installed and launched on a verified API {record['api']} emulator. Numerical parity ran in airplane mode. Synthetic incoming SMS were injected through the emulator console with its cellular radio enabled; no carrier SMS or physical device was used. Prior emulator network settings were restored afterward.

| Instrumentation group | Tests | Result |
| --- | ---: | --- |
{test_table}

Total: {record['emulator_test_total']} instrumentation tests passed. These include actual 60% model initialization, all three displayed categories, both-model practical comparison, unchanged risk behavior, manual/shared/pasted input, permission denial, navigation/clearing, privacy lifecycle, existing risk/blocking screens, theme settings and a real emulator incoming-SMS notification flow using the active classifier. The normal non-test app process was launched successfully after instrumentation. No crash occurred in these tested workflows.

## Preservation and modified files

SHA-256 verification confirmed preservation of all {record['preserved_file_count']} files in the pre-change manifest: the complete frozen multiclass experiment, original dataset ZIP, original research reports/protocol/results/figures, earlier 80% integration evidence, historical model assets and historical APK files. RiskAssessment.kt is also unchanged. The thesis's observed 80% SVM advantage and uncertainty are not rewritten because of this deployment choice. Original test/CV metrics were neither recomputed nor relabeled.

Changes are limited to:

- New private `src/multiclassSvm60/assets/model.json` and ignored-directory entry.
- `MulticlassSvmDetector.kt`: explicit 60/80 model-identity validation and training-percentage status, retaining shared feature/math code and default 80% behavior.
- `SmishGuardApp.kt`: explicit build-selected 60% loading and asset hash validation.
- `MainActivity.kt`: SVM 60% header identification; existing result UI retained.
- `android/app/build.gradle.kts`: separate 60% debug build, asset guard and fixture wiring.
- Shared parity helper: optional explicit training percentage, default 80% unchanged.
- New Svm60ParityTest, Svm60AndroidTest, Svm60FlowTest and Svm60PracticalParity tests.
- New export_svm60_android.py, build_svm60.ps1, verify_svm60_apk.py, package_svm60.py and report_svm60_deployment.py scripts and this separate deployment-report directory.

## Install and roll back

This APK is a **debug build**, despite the requested filename ending in `-New.apk`. Copy it to an Android 8.0+ device, open it and accept Android's installation prompt for the file-manager source. Launch **VeriTxt · SVM 60%** to use it. It installs alongside the SVM 80% app; settings are separate. Enable incoming scanning and existing permissions only through the normal in-app controls.

With an explicitly selected USB-debugging device:

```powershell
adb -s DEVICE_SERIAL install -r "{record['apk']}"
adb -s DEVICE_SERIAL shell am start -n {record['package']}/ph.smishguard.MainActivity
```

Rollback requires no model conversion or retraining: open the existing **VeriTxt · SVM 80%** app. If it is not installed, reinstall this preserved original APK:

`{oldapk}`

Its original SHA-256 remains `e31e440d1e02512b0cf2718cde2fcf87e3f7cc9de944eb0fe5e8ad1dcfd0d8ec`; package `ph.smishguard.svm.multiclass80`. Enable incoming scanning only in the version you intend to use to avoid duplicate notifications from two independently enabled apps. The old 80% asset and frozen `svm-80.pkl` also remain unchanged in the project.

## Reproduction and limitations

From the project root with the existing research environment:

```powershell
$env:PYTHONPATH='research'
.\\scripts\\build_svm60.ps1
research\\.venv\\Scripts\\python.exe scripts/verify_svm60_apk.py --output research/runs/svm60-android-20261020/NEW-VERIFICATION
```

The completed export and private test fixtures are in `research/runs/svm60-android-20261020/export-v1/`. On a fresh source checkout with authorized private frozen artifacts, export_svm60_android.py creates a fresh output and the private 60% asset without fitting; it refuses to replace an existing export asset. Pass another completed fixture directory via build_svm60.ps1 -ParityDir. Signature verification and package_svm60.py guard the tested APK checksum, sole asset, original-file preservation and test/lint results before creating a fresh deliverable directory. All new artifacts are separate from research outputs.

Physical-device/OEM/background behavior, runtime versions other than API {record['api']}, release signing/distribution and independent prospective labeled SMS are unverified. The 20 practical examples are not an independent accuracy study, and none has a reliable supplied human label. This application switch is experimental and user-directed; it does not establish improved fraud detection, fix the cashback example, change the thesis conclusion or make the heuristic score a probability. The model's and risk system's demonstrated limitations remain visible evidence for future separately evaluated improvements.

![Ham result](Ham.png)

![Smishing result](Smishing.png)

![Gambling result](Gambling.png)
'''
    (report/'DEPLOYMENT.md').write_text(text,encoding='utf-8')
    m.save(report/'artifact-manifest.json',{p.name:m.legacy.digest(p) for p in report.iterdir() if p.is_file() and p.name!='artifact-manifest.json'})
    print('Deployment report:',report/'DEPLOYMENT.md')


if __name__=='__main__':main()
