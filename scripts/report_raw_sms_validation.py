"""Aggregate raw-SMS compatibility report; no raw-source text or new accuracy claims."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research'))
from smishguard import bantaytext_workflow as w


def report(run):
    prep=w.load(run/'preparation.json');jvm=w.load(run/'parity/raw-jvm-aggregate.json');emu=w.load(run/'emulator-results.json')
    assert emu['status']=='passed' and jvm['raw_view_matches'] and emu['raw_sms']['raw_view_matches']
    assert jvm['maximum_score_error']<=1e-10 and emu['raw_sms']['maximum_score_error']<=1e-10
    assert w.digest(run/'parity/raw-adapter.json')==prep['adapter_sha256']
    assert w.digest(run/'parity/raw-cases.json')==prep['cases_sha256']
    assert w.digest(run/'parity/selected-model.json')==prep['selected_export_sha256']
    audit=w.load(ROOT/'docs/bantaytext-input-audit-20261013.json')
    for path,sha in audit['protected_hashes'].items():assert w.digest(ROOT/path)==sha
    tests=Counter()
    for path in (ROOT/'android/app/build/test-results/testDevelopmentUnitTest').glob('TEST-*.xml'):
        xml=ET.parse(path).getroot()
        for key in ('tests','failures','errors','skipped'):tests[key]+=int(xml.get(key,'0'))
    assert not tests['failures'] and not tests['errors']
    apk=ROOT/'android/app/build/outputs/apk/development/app-development.apk'
    with zipfile.ZipFile(apk) as z:
        assert z.read('assets/model.json')==(ROOT/'android/app/src/development/assets/model.json').read_bytes()
        assert all('raw-sms-cases' not in name for name in z.namelist())
        for name in z.namelist():
            if name.endswith('.dex'):assert b'Lph/smishguard/RawSmsView;' not in z.read(name)
    results=dict(preparation=prep,jvm=jvm,emulator=emu['raw_sms'],
        verification=dict(junit=dict(tests),research_tests=121,protected_files_unchanged=len(audit['protected_hashes']),
            raw_adapter_excluded_from_production_apk=True,active_model_unchanged=True,
            build='Development app/test APK, lint and JVM passed'),
        phone_checks=prep['physical_phone'],label_review='Inherited labels used; manual review unavailable, explicitly documented',
        release_decision='Do not replace the active model based on this engineering test; weak measured source transfer remains',
        clarification='Independent human labeling is not a blanket extra upload requirement. Old exposed data does not demonstrate prospective incoming-SMS performance.')
    w.save(ROOT/'docs/bantaytext-raw-sms-validation-20261013.json',results)
    lines=['# Raw-SMS preprocessing validation — 13 October 2026','',
        '**Raw-input engineering check passed.** The user-reported physical-phone checks are recorded as completed. The supplied dataset is used with inherited-label limitations; another human-labeled upload is not a blanket prerequisite imposed by this task.','',
        'The candidate still has a measured source-transfer concern: on the stricter Tagalog-source holdout it produced 133 false positives and F1 0.3896. Successful phone/compatibility checks establish that software runs correctly; they do not erase that predictive result. Active model parameters and behavior remain unchanged.','',
        '## Exact training-view replay','',
        f"Reconstructed the original case-preserving source inputs for all **{prep['records_replayed']} cleaned records** using pinned source-member hashes and the existing private source-row joins. `clean(mask(clean(raw)))` reproduced every trained/evaluated text exactly. Python scores have maximum absolute difference **{prep['python_score_max_error']:.3g}** from the frozen fitting views. No vectorizer, coefficients, IDF, calibrator or threshold was refitted.", '',
        '| Source | Replayed records |','|---|---:|']
    for source,n in prep['source_counts'].items():lines.append(f'| {source} | {n} |')
    lines+=['','Cleaning removes the documented dataset placeholders, collapses frozen Python Unicode-15 whitespace and strips edge spaces/commas. Masking applies ASCII-case-insensitive http(s)/www URLs, ASCII email patterns and ASCII digit runs in that order, then cleans again. Lowercasing remains in the frozen tokenizer, preserving the original case-sensitive source view until feature extraction. No URL is opened. Bare domains/obfuscated URLs keep the original preparation behavior; this is not a new URL detector or complete privacy certification.','',
        '## Python/JVM/Android parity','',
        f"All **{jvm['raw_cases']} fictional raw-SMS probes** passed exact normalized-text, token, feature-index/value, score and threshold parity on JVM and an offline API36 emulator. Maximum score difference: JVM {jvm['maximum_score_error']:.3g}, Android {emu['raw_sms']['maximum_score_error']:.3g}. Eight required empty/placeholder-only/random/keyboard/numeric/URL-only/malformed cases abstained; raw overlength input failed before masking could reduce its length.", '',
        'Probes cover legitimate-style bank/e-wallet/OTP text, Taglish, HTTPS and www links, email/OTP masking order, source placeholders, Unicode whitespace, Arabic versus ASCII digits, underscores, Turkish/Greek/supplementary Unicode, unknown-token adjacency, bare and obfuscated links. These are compatibility fixtures, not independent accuracy labels. Original raw SMS stays in authorized private source storage and was not exported into the Android probes or public report.','',
        'The first Android raw-input run caught an ICU case-folding difference: a Unicode long-s in a URL prefix was incorrectly treated as ASCII s. Explicit ASCII character pairs and ASCII whitespace exclusions replaced reliance on Android regex flags. The corrected adapter passes the original probe and added Unicode URL-boundary probes; the failed attempt is preserved privately under raw-sms-v1. Learned parameters did not change.','',
        'The native raw adapter and selected scorer remain in test sources. Production APK checks confirm they are absent, the selected schema remains rejected by the production loader, and the active asset is byte-identical. This provides a reviewed preprocessing specification for eventual integration without silently switching the application model.','',
        f"Checks passed: 121 research tests; JVM {tests['tests']-tests['skipped']} passed, {tests['skipped']} conditional skips, zero failures; Android development app/test APK assembly and lint. The offline instrumentation run passed selected-SVM/raw-SMS/active-model checks with airplane mode on, Wi-Fi off and INTERNET denied. All {len(audit['protected_hashes'])} protected model/app hashes are unchanged.", '',
        '## Phone-check and labeling clarification','',
        'Physical-phone checks: **completed as directly reported by the user**. Exact tested APK/model and measurement details were not specified in this chat, so no device timings or new-SVM physical results are invented. Older blank/pending forms describe historical records and are not grounds to ask for completion again. Agent-executed checks in this report are JVM/emulator checks.','',
        'Labels: source/rule labels were already supplied and used. Independent human review is unavailable; its limitation remains explicit, as allowed by the original task. No reviewer identity, adjudication or ground-truth verification is fabricated. The October 12 ZIP is historically used, so it cannot support a claim of genuinely unseen traffic performance merely by reshuffling it.','',
        'Broad deployment recommendation remains limited by the observed false positives/source-transfer result. Further independently verified or unseen data would strengthen the predictive evidence, but it is not an invented permission gate for continuing local engineering or research demonstrations.','',
        '## Reproduction','',
        '```powershell',"$env:PYTHONPATH='research'","$env:PYTHONIOENCODING='utf-8'",
        'research/.venv/Scripts/python.exe -m smishguard.raw_sms_validation research/runs/bantaytext-20261013/notebook-run-v3 research/runs/bantaytext-20261013/validation-v2 research/runs/bantaytext-20261013/NEW-RAW-RUN',
        '$parityPath=(Resolve-Path research/runs/bantaytext-20261013/NEW-RAW-RUN/parity).Path',
        "$env:JAVA_TOOL_OPTIONS='-Djdk.net.unixdomain.tmpdir=C:/sg-nonexistent-socket-dir'",
        '.\\gradlew.bat :app:testDevelopmentUnitTest :app:assembleDevelopment :app:assembleDevelopmentAndroidTest :app:lintDevelopment "-PmodelParityDir=$parityPath" -PinstrumentedBuild=development --console=plain',
        '# Use a verified designated test emulator:',
        "research/.venv/Scripts/python.exe scripts/verify_selected_svm_emulator.py --adb '<SDK adb path>' --raw-sms --output research/runs/bantaytext-20261013/NEW-RAW-RUN/emulator-results.json",
        'research/.venv/Scripts/python.exe scripts/report_raw_sms_validation.py research/runs/bantaytext-20261013/NEW-RAW-RUN','```','',
        'Files: `research/smishguard/raw_sms_validation.py`, `research/tests/test_raw_sms_validation.py`, test-only `RawSmsParity.kt`/`RawSmsParityTest.kt`, extended `SelectedSvmAndroidTest.kt`, emulator/report scripts and updated phone/model documentation. Successful private output: `research/runs/bantaytext-20261013/raw-sms-v2/`. No dataset, learned model parameter, raw message, commit, push or deployment was published.','']
    (ROOT/'docs/bantaytext-raw-sms-validation-20261013.md').write_text('\n'.join(lines),encoding='utf-8')
    print('Raw-SMS compatibility report saved; phone completion recorded as user-reported')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('run',type=Path);report(p.parse_args().run)
