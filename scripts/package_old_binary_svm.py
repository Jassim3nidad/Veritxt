"""Package the restored old binary model only after build and device checks pass."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'research/runs/old-binary-svm-20261020'

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,x):Path(p).write_text(json.dumps(x,indent=2),encoding='utf-8')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verification',type=Path,required=True)
    parser.add_argument('--destination',type=Path,required=True)
    args=parser.parse_args();verification=args.verification.resolve();dest=args.destination.resolve()
    r=load(verification/'emulator-results.json');identity=load(RUN/'model-identity.json')
    assert r['status']=='passed'
    apk=ROOT/'android/app/build/outputs/apk/oldSvm/app-oldSvm.apk'
    assert digest(apk)==r['apk_sha256']
    p=r['parity'];assert p['parity']['cases']==515 and p['raw_parity']['raw_cases']==33
    assert p['parity']['maximum_score_error']<=1e-10 and p['raw_parity']['maximum_score_error']<=1e-10
    assert p['risk_profile']=='evidence-index-v1' and p['cashback_rule_enabled'] is False
    with zipfile.ZipFile(apk) as z:
        assert set(n for n in z.namelist() if n.startswith('assets/'))=={'assets/model.json','assets/raw-sms-adapter.json'}
        assert hashlib.sha256(z.read('assets/model.json')).hexdigest()==identity['model_sha256']
        assert hashlib.sha256(z.read('assets/raw-sms-adapter.json')).hexdigest()==identity['adapter_sha256']
    assert load(RUN/'parity/selected-jvm-aggregate.json')['cases']==515
    assert load(RUN/'parity/raw-jvm-aggregate.json')['raw_cases']==33
    preserved=load(RUN/'preservation-before.json')
    changed=[name for name,h in preserved.items() if not (ROOT/name).is_file() or digest(ROOT/name)!=h]
    assert not changed,changed
    unit={k:sum(int(ET.parse(f).getroot().get(k,0)) for f in
        (ROOT/'android/app/build/test-results/testOldSvmUnitTest').glob('TEST-*.xml')) for k in ['tests','skipped','failures','errors']}
    assert unit['tests']>0 and unit['failures']==unit['errors']==0
    lint=ET.parse(ROOT/'android/app/build/reports/lint-results-oldSvm.xml').getroot()
    assert not any(i.get('severity') in ['Error','Fatal'] for i in lint.findall('issue'))
    signature=(RUN/'signature.txt').read_text(encoding='utf-8-sig')
    assert 'Verifies' in signature and 'v2): true' in signature
    tests={}
    for key in ['native-parity','manual-two-categories','existing-flows','privacy-lifecycle','risk-results','theme-settings','real_model_incoming_sms']:
        match=re.search(r'OK \((\d+) tests?\)',r[key]);assert match,key
        tests[key]=int(match.group(1))
    dest.mkdir(parents=True,exist_ok=False)
    target=dest/'VeriTxt-OldModel-Ham-Smishing-debug.apk';shutil.copyfile(apk,target)
    assert digest(target)==r['apk_sha256']
    (dest/'SHA256SUMS.txt').write_text(digest(target)+'  '+target.name+'\n',encoding='utf-8')
    summary=dict(apk=str(target),apk_sha256=digest(target),apk_bytes=target.stat().st_size,
        package=r['package'],launcher='VeriTxt · Ham/Smishing',version='0.3.0-ham-smishing-debug',
        model_identity=identity,parity=p,unit_tests=unit,android_tests=tests,android_test_total=sum(tests.values()),
        preserved_file_count=len(preserved),lint_errors=0,
        lint_warnings=sum(i.get('severity')=='Warning' for i in lint.findall('issue')),
        signing='Existing debug key; APK v2 verified',physical_device_tested=False)
    save(dest/'build-verification.json',summary)
    report=ROOT/'docs/old-binary-svm-20261020';report.mkdir(parents=True,exist_ok=False)
    for name in ['Ham.png','Smishing.png']:
        shutil.copyfile(verification/name,dest/name);shutil.copyfile(verification/name,report/name)
    for name in ['SHA256SUMS.txt','build-verification.json']:shutil.copyfile(dest/name,report/name)
    for name in ['emulator-results.json','old-binary-android-parity.json']:shutil.copyfile(verification/name,report/name)
    for name in ['model-identity.json','signature.txt','build.log']:shutil.copyfile(RUN/name,report/name)
    text=f'''# VeriTxt — old Ham/Smishing model restored

Install `{target}` and open **VeriTxt · Ham/Smishing**. This is a signed debug APK, package `{r['package']}`, built with the existing local debug key. It installs alongside earlier variants. No physical-phone test is claimed.

The model asset is byte-identical to `assets/model.json` inside the user's `Veritxt-0.3.0-Updated.zip` APK: SHA-256 `{identity['model_sha256']}`. It has 18,473 features, classes Ham/Smishing, and the unchanged validation-selected threshold {identity['threshold']}. Training percentage is not established by the old APK metadata. No retraining, parameter, feature, sigmoid or decision-threshold changes were made. The existing case-preserving raw-SMS adapter is retained unchanged (SHA-256 `{identity['adapter_sha256']}`).

The new `oldSvm` build uses the existing SelectedSvmDetector/scorer. It adds explicit Ham or Smishing display labels based directly on the binary decision; no Gambling class or invented model output is presented. The mathematical scorer is unchanged. Previous variants keep their existing behavior.

Following the user's latest direction, this build uses the base `evidence-index-v1` risk profile with the cashback override disabled. No bank-name rule or message-specific condition was added. Model category and the existing heuristic risk index remain separate; a risk score is not a calibrated fraud probability. This is a restoration of the old model, not evidence of improved accuracy or a promise that every scam is detected. No accuracy was inferred from parity tests.

Verification: 515 frozen Python/JVM/Android model fixtures and 33 raw-SMS preparation fixtures passed. Android maximum score errors: {p['parity']['maximum_score_error']:.3g} (model) and {p['raw_parity']['maximum_score_error']:.3g} (raw). Production app-path, binary category mapping, unchanged base risk routing, both category screens, manual/shared/pasted flows, privacy clearing, risk screens, themes and actual emulator incoming-SMS warning checks passed. Total Android tests: {sum(tests.values())} on API {r['api']}. Unit tests: {unit['tests']-unit['skipped']} passed, {unit['skipped']} conditional skips, zero failures/errors. Lint: zero errors, {summary['lint_warnings']} warnings. Normal non-test app launch succeeded.

Earlier artifacts/models/reports: {len(preserved)} original files passed SHA-256 preservation checks. The packaged application contains only the original binary model and its raw-SMS adapter; no parity fixtures, datasets or pickle files were included. APK SHA-256: `{r['apk_sha256']}`.

Reproduce with `scripts/build_old_binary_svm.ps1`, then `scripts/verify_old_binary_svm.py --output <fresh-output>` and `scripts/package_old_binary_svm.py --verification <fresh-output> --destination <fresh-deliverable>`. The parity files are copied into the new run directory so historical evidence is not overwritten.
'''
    (report/'RESTORATION.md').write_text(text,encoding='utf-8')
    save(report/'artifact-manifest.json',{f.name:digest(f) for f in report.iterdir() if f.is_file()})
    print(json.dumps(summary,indent=2))
    print('Report:',report/'RESTORATION.md')

if __name__=='__main__':main()
