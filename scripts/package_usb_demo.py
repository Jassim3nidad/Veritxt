"""Package the USB defense kit only after checks of the exact APK pass."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verification', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--replace', action='store_true', help='Refresh a previously generated USB demo kit in place')
    args = parser.parse_args()
    verification = args.verification.resolve()
    results = json.loads((verification / 'verification.json').read_text(encoding='utf-8'))
    apk = ROOT / 'android/app/build/outputs/apk/usbDemo/app-usbDemo.apk'
    assert results['status'] == 'passed' and results['apk_sha256'] == digest(apk)
    assert results['transport_sha256'] == digest(ROOT / 'scripts/usb-demo.ps1')
    assert results['samples_sha256'] == digest(ROOT / 'scripts/usb-demo-messages.json')
    assert results['normal_process_cold_start'].startswith('passed')
    actual = results['actual_model_reports']
    assert len(actual['cases']) == 6
    assert actual['parity']['cases'] == 515 and actual['raw_parity']['raw_cases'] == 33
    assert all(case['exact_result_opened'] for case in actual['cases'])
    assert results['offline_settings'] == {'airplane_mode_on': '1', 'wifi_on': '0', 'mobile_data': '0'}
    assert actual['sms_permission'] is False and actual['incoming_sms_consent'] is False
    assert all('OK (' in results[key] for key in ['offline-usb-transport', 'privacy-and-failures', 'existing-notification-regressions'])
    reports = ROOT / 'android/app/build'

    def unit_totals(variant):
        nodes = [ET.parse(path).getroot() for path in (reports / f'test-results/test{variant}UnitTest').glob('TEST-*.xml')]
        totals = {key: sum(int(node.get(key, 0)) for node in nodes) for key in ['tests', 'skipped', 'failures', 'errors']}
        assert totals['tests'] > 0 and totals['failures'] == totals['errors'] == 0
        return totals

    unit = unit_totals('UsbDemo')
    release_unit = unit_totals('Release')
    lint = ET.parse(reports / 'reports/lint-results-usbDemo.xml').getroot()
    assert not any(issue.get('severity') in ['Error', 'Fatal'] for issue in lint.findall('issue'))
    manifest = (ROOT / 'output/usb-demo-manifest.txt').read_text(encoding='utf-8-sig')
    release_manifest = (ROOT / 'output/usb-demo-release-manifest.txt').read_text(encoding='utf-8-sig')
    receiver = 'ph.smishguard.demo.UsbDemoReceiver'
    assert receiver in manifest and '"android.permission.DUMP"' in manifest
    assert receiver not in release_manifest
    assert 'android.permission.INTERNET' not in manifest
    signature = (ROOT / 'output/usb-demo-signature.txt').read_text(encoding='utf-8-sig')
    assert 'Verifies' in signature and 'v2 scheme (APK Signature Scheme v2): true' in signature
    release_apk = reports / 'outputs/apk/release/app-release-unsigned.apk'
    with zipfile.ZipFile(release_apk) as archive:
        assert not any(b'Lph/smishguard/demo/UsbDemoReceiver;' in archive.read(name)
                       for name in archive.namelist() if name.endswith('.dex'))
    for variant, expected in [('usbDemo', 'true'), ('release', 'false')]:
        generated = reports / f'generated/source/buildConfig/{variant}/ph/smishguard/BuildConfig.java'
        assert f'USB_DEMO_ENABLED = {expected};' in generated.read_text(encoding='utf-8')
    with zipfile.ZipFile(apk) as archive:
        assert {name for name in archive.namelist() if name.startswith('assets/')} == {'assets/model.json', 'assets/raw-sms-adapter.json'}
        for name, key in [('model.json', 'model_sha256'), ('raw-sms-adapter.json', 'adapter_sha256')]:
            assert hashlib.sha256(archive.read('assets/' + name)).hexdigest() == results[key]

    destination = args.destination.resolve()
    if destination.exists():
        assert args.replace, 'Use a fresh destination or explicitly refresh a generated kit with --replace'
        prior = json.loads((destination / 'build-verification.json').read_text(encoding='utf-8'))
        assert prior['package'] == results['package'], 'Only a generated USB demo kit may be refreshed'
    else:
        destination.mkdir(parents=True)
    shutil.copyfile(apk, destination / 'Veritxt-USB-Demo.apk')
    for name in ['usb-demo.ps1', 'usb-demo-messages.json']:
        shutil.copyfile(ROOT / 'scripts' / name, destination / name)
    shutil.copyfile(ROOT / 'docs/usb-demo-20261028.md', destination / 'README.md')
    evidence = destination / 'evidence'
    shutil.copytree(verification, evidence, dirs_exist_ok=args.replace)
    for name in ['usb-demo-signature.txt', 'usb-demo-manifest.txt', 'usb-demo-release-manifest.txt',
                 'usb-demo-final-build.log', 'usb-demo-release-isolation.log']:
        shutil.copyfile(ROOT / 'output' / name, evidence / name)
    android_count = sum(int(re.search(r'OK \((\d+) tests?\)', results[key])[1])
                        for key in ['offline-usb-transport', 'privacy-and-failures', 'existing-notification-regressions', 'prepare-normal-cold-start'])
    summary = dict(package=results['package'], version='0.3.0-usb-demo', apk_sha256=digest(apk),
                   apk_bytes=apk.stat().st_size, model_sha256=results['model_sha256'], adapter_sha256=results['adapter_sha256'],
                   unit_tests=unit, release_unit_tests=release_unit, android_tests=android_count,
                   lint_errors=0, lint_warnings=sum(issue.get('severity') == 'Warning' for issue in lint.findall('issue')),
                   api=results['api'], offline_transport='passed', actual_model_cases=6,
                   model_parity_cases=515, raw_sms_parity_cases=33, normal_process_cold_start='passed',
                   release_receiver_absent=True, release_demo_flag=False, internet_permission=False,
                   apk_v2_signature_verified=True, physical_phone_tested=False)
    summary['powershell_executable'] = results['powershell_executable']
    summary['transport_sha256'] = results['transport_sha256']
    (destination / 'build-verification.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    sums = '\n'.join(digest(path) + '  ' + path.relative_to(destination).as_posix()
                     for path in sorted(destination.rglob('*')) if path.is_file() and path.name != 'SHA256SUMS.txt') + '\n'
    (destination / 'SHA256SUMS.txt').write_text(sums, encoding='utf-8')
    bundle = shutil.make_archive(str(destination), 'zip', destination)
    print(json.dumps(summary, indent=2))
    print('Kit:', bundle)


if __name__ == '__main__':
    main()
