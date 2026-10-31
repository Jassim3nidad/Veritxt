"""Package only a built, signed, model-verified and emulator-tested multiclass APK."""
from pathlib import Path
import argparse
import json
import re
import shutil
import xml.etree.ElementTree as ET
import zipfile
from smishguard import multiclass_comparison as m

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verification',type=Path,required=True)
    parser.add_argument('--destination',type=Path,required=True)
    args=parser.parse_args();verification=args.verification.resolve();dest=args.destination.resolve()
    study=ROOT/'research/runs/multiclass-20261020/run-v1'
    integration=ROOT/'research/runs/svm60-android-20261020'
    export=integration/'export-v1'
    m.verify(study,'training-seal.json')
    preserved=m.load(integration/'preservation-before.json')
    changed=[name for name,sha in preserved.items() if not (ROOT/name).is_file() or m.legacy.digest(ROOT/name)!=sha]
    if changed:raise ValueError('Preserved files changed: '+repr(changed))
    device=m.load(verification/'emulator-results.json');jvm=m.load(export/'svm60-jvm-parity.json')
    assert device['status']=='passed' and device['parity']['matching_predictions']==954
    assert jvm['matching_predictions']==954 and jvm['mismatches']==0
    assert device['practical_parity']['matching_predictions']==40 and device['practical_parity']['mismatches']==0
    apk=ROOT/'android/app/build/outputs/apk/multiclassSvm60/app-multiclassSvm60.apk'
    assert apk.stat().st_size>0 and m.legacy.digest(apk)==device['apk_sha256']
    expected=m.load(export/'export-manifest.json')
    with zipfile.ZipFile(apk) as z:
        import hashlib
        assert hashlib.sha256(z.read('assets/model.json')).hexdigest()==expected['model_sha256']
        assert [n for n in z.namelist() if n.startswith('assets/')]==['assets/model.json']
    totals=dict(tests=0,skipped=0,failures=0,errors=0)
    for p in (ROOT/'android/app/build/test-results/testMulticlassSvm60UnitTest').glob('TEST-*.xml'):
        a=ET.parse(p).getroot().attrib
        for k in totals:totals[k]+=int(a.get(k,0))
    assert totals['tests']>=2 and totals['failures']==0 and totals['errors']==0
    lint=ET.parse(ROOT/'android/app/build/reports/lint-results-multiclassSvm60.xml').getroot()
    assert not any(i.get('severity') in ('Error','Fatal') for i in lint.findall('issue'))
    signing=(integration/'signature-final.txt').read_text(encoding='utf-8-sig')
    assert 'Verifies' in signing and 'v2): true' in signing
    tests={}
    for key in ['native-parity','manual-three-categories','existing-flows','privacy-lifecycle','risk-results','theme-settings','real_model_incoming_sms']:
        match=re.search(r'OK \((\d+) tests?\)',device[key]);assert match,key
        tests[key]=int(match.group(1))
    dest.mkdir(parents=True,exist_ok=False)
    target=dest/'VeriTxt-LinearSVM-60-New.apk'
    with target.open('xb') as f:f.write(apk.read_bytes())
    assert m.legacy.digest(target)==device['apk_sha256']
    (dest/'SHA256SUMS.txt').write_text(m.legacy.digest(target)+'  '+target.name+'\n',encoding='utf-8')
    m.save(dest/'build-verification.json',dict(apk=str(target),apk_bytes=target.stat().st_size,apk_sha256=m.legacy.digest(target),
        package=device['package'],version='0.3.0-svm60-debug',signing='existing local debug key; APK v2 verified',
        source_model_sha256=expected['source_pipeline_sha256'],packaged_model_sha256=expected['model_sha256'],
        frozen_experiment_files_preserved=True,preserved_file_count=len(preserved),
        unit_tests=totals,lint_errors=0,lint_warnings=sum(i.get('severity')=='Warning' for i in lint.findall('issue')),
        emulator_tests=tests,emulator_test_total=sum(tests.values()),api=device['api'],
        parity=device['parity'],practical_parity=device['practical_parity'],risk_rules_changed=False,thesis_test_messages_used=0,physical_device_tested=False))
    for name in ['Ham','Smishing','Gambling']:shutil.copyfile(verification/(name+'.png'),dest/(name+'.png'))
    print(json.dumps(m.load(dest/'build-verification.json'),indent=2))


if __name__=='__main__':main()
