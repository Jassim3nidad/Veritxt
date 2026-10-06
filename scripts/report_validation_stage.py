"""Publish aggregate preparation and APK identity evidence, never annotation records."""
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[1]
PRIVATE=ROOT/'research/data/validation-20261006'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    before=read(PRIVATE/'apk-before.json');after=read(PRIVATE/'apk-after.json')
    old=read(ROOT/'deliverables/expanded-20261005/mbert-apk-manifest.json')
    new=read(ROOT/'deliverables/validation-20261006/mbert-apk-manifest.json')
    old_apk=ROOT/'deliverables/expanded-20261005'/old['filename'];new_apk=ROOT/'deliverables/validation-20261006'/new['filename']
    assert sha(old_apk)==old['sha256']==before['apk_sha256']
    assert sha(new_apk)==new['sha256']==after['apk_sha256']
    with zipfile.ZipFile(old_apk) as a,zipfile.ZipFile(new_apk) as b:
        assert sorted(a.namelist())==sorted(b.namelist())
        assert len(set(a.namelist()))==len(a.namelist())
        for name in a.namelist():
            with a.open(name) as x,b.open(name) as y:
                assert hashlib.file_digest(x,'sha256').digest()==hashlib.file_digest(y,'sha256').digest()
        entries=len(a.namelist())
    assert old['asset_sha256']==new['asset_sha256']
    emulator=read(PRIVATE/'emulator-mbert.json');assert emulator['status']=='passed'
    parity=json.loads(re.search(r'MBERT_AGGREGATE=(\{[^\r\n]+\})',emulator['mbert_parity_policy_latency']).group(1))
    assert parity['class_changes']==0 and parity['cases']==468
    build=(PRIVATE/'build-mbert.log').read_text(encoding='utf-8',errors='replace')
    assert 'BUILD SUCCESSFUL' in build
    suites=[ET.parse(p).getroot() for p in (ROOT/'android/app/build/test-results/testMbertUnitTest').glob('TEST-*.xml')]
    tests={k:sum(int(s.get(k,0)) for s in suites) for k in ('tests','failures','errors','skipped')}
    assert not tests['failures'] and not tests['errors']
    lint=ET.parse(ROOT/'android/app/build/reports/lint-results-mbert.xml').getroot()
    lint_counts={severity:sum(i.get('severity')==severity for i in lint.findall('issue')) for severity in ('Error','Fatal','Warning')}
    assert not lint_counts['Error'] and not lint_counts['Fatal']
    history=read(PRIVATE/'history/inventory.json');index=read(PRIVATE/'history/index.json')
    freeze=read(PRIVATE/'prospective-freeze.json')
    for p,d in freeze['files'].items():assert sha(ROOT/p)==d
    packet=read(PRIVATE/'review/coordinator/packet-manifest.json')
    agreement=read(PRIVATE/'review/coordinator/blank-agreement-final/agreement.json')
    assert agreement['all_categories']['paired']==0 and agreement['all_categories']['kappa'] is None
    checks={}
    for name,filename in [('research','research-tests.log'),('apk_layout','apk-layout-tests.log')]:
        text=(PRIVATE/filename).read_text(encoding='utf-8',errors='replace')
        assert re.search(r'^OK$',text,re.M)
        checks[name]=dict(tests=int(re.search(r'Ran (\d+) tests?',text).group(1)),passed=True,log_sha256=sha(PRIVATE/filename))
    result=dict(status='prepared_and_verified; human validation pending',model_freeze=freeze,
        software_tests=checks,
        prepared_protocol_sha256={name:sha(ROOT/'docs'/name) for name in ('prospective-validation-plan-20261006.md','sms-labeling-guide-20261006.md','blinded-validation-workflow-20261006.md')},
        blinded_review=dict(records_per_packet=packet['records'],packet_orders='independently shuffled; disjoint random IDs',
            existing_labels_categories_confidence_predictions='absent',completed_decisions=0,agreement=agreement['all_categories'],
            workbook_verification=read(PRIVATE/'workbook-verification.json')),
        history=dict(inventory_entries=len(history['files']),local_files=sum('!' not in r['file'] for r in history['files']),
            archive_entries=sum(r['kind']=='archive' for r in history['files']),normalized_views=len(index['normalized_texts']),
            literal_fingerprints=len(index['exact_sha256']),inventory_sha256=sha(PRIVATE/'history/inventory.json'),
            index_sha256=sha(PRIVATE/'history/index.json'),limitations=history['limitation']),
        prospective=read(PRIVATE/'prospective/empty-template-check/summary.json'),physical_phone_results='pending; zero evidence received',
        apk=dict(old=old,new=new,saved_bytes=before['apk_bytes']-after['apk_bytes'],
            old_gap_bytes=before['gap_bytes'],new_gap_bytes=after['gap_bytes'],referenced_entries=entries,
            all_referenced_file_contents_identical=True,all_fitted_asset_hashes_identical=True,
            old_apk_preserved=True,build_log_sha256=sha(PRIVATE/'build-mbert.log'),jvm=tests,lint=lint_counts,
            emulator_test_count=sum(int(re.search(r'OK \((\d+) tests?\)',v).group(1)) for v in emulator.values() if isinstance(v,str) and re.search(r'OK \((\d+) tests?\)',v)),
            emulator_parity=parity,emulator_log_sha256=sha(PRIVATE/'emulator-mbert.log')))
    (ROOT/'docs/validation-stage-verification-20261006.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('Safe aggregate evidence generated:',entries,'identical active APK entries;',result['apk']['saved_bytes'],'bytes removed.')

if __name__=='__main__':main()
