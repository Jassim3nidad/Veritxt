"""Verify all-SMS routing and actual emulator modem delivery with the frozen binary model."""
from pathlib import Path
import argparse
import base64
import hashlib
import json
import subprocess
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = 'ph.smishguard.svm.oldbinary'
RUNNER = PACKAGE + '.test/ph.smishguard.SoftwareTestRunner'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial', default='emulator-5554')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--linked-cashback', action='store_true', help='Also verify the opt-in linked cashback risk profile')
    parser.add_argument('--initial-reports', action='store_true', help='Also verify three simultaneous modem SMS and their independent initial reports')
    parser.add_argument('--one-to-one', action='store_true', help='Verify five identical SMS from one sender create five separate reports')
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    adb = ['adb', '-s', args.serial]

    def command(*parts, timeout=60, check=True):
        return subprocess.run(adb + list(parts), capture_output=True, timeout=timeout, check=check).stdout

    assert command('shell', 'getprop', 'ro.kernel.qemu').strip() == b'1', 'Emulator only'
    assert command('shell', 'getprop', 'sys.boot_completed').strip() == b'1'
    apk = ROOT / 'android/app/build/outputs/apk/oldSvm/app-oldSvm.apk'
    test_apk = ROOT / 'android/app/build/outputs/apk/androidTest/oldSvm/app-oldSvm-androidTest.apk'
    with zipfile.ZipFile(apk) as archive:
        model_hash = hashlib.sha256(archive.read('assets/model.json')).hexdigest()
        assert model_hash == '15cc0105b0e51e5342682ea36896c4436e515c39d165faf040476046b6b8059c'
        assert set(n for n in archive.namelist() if n.startswith('assets/')) == {
            'assets/model.json', 'assets/raw-sms-adapter.json'}
    results = dict(status='incomplete', apk_sha256=hashlib.sha256(apk.read_bytes()).hexdigest(),
                   model_sha256=model_hash, package=PACKAGE, physical_device=False,
                   api=command('shell', 'getprop', 'ro.build.version.sdk').decode().strip())

    def save():
        (out / 'verification.json').write_text(json.dumps(results, indent=2), encoding='utf-8')

    def completed(label, output):
        text = output.decode(errors='replace')
        (out / (label + '.log')).write_text(text, encoding='utf-8')
        if 'OK (' not in text or any(s in text for s in ['FAILURES!!!', 'INSTRUMENTATION_FAILED']):
            raise RuntimeError(label + ' failed:\n' + text)
        results[label] = text.strip()
        save()
        print(label + ': passed', flush=True)

    prior_airplane = command('shell', 'settings', 'get', 'global', 'airplane_mode_on').strip() == b'1'
    try:
        command('install', '-r', str(apk), timeout=180)
        command('install', '-r', str(test_apk), timeout=180)
        classes = 'ph.smishguard.AllSmsNotificationsTest,ph.smishguard.OldBinarySvmAndroidTest'
        if args.linked_cashback:
            classes += ',ph.smishguard.LinkedCashbackFlowTest'
        completed('routing-and-frozen-model', command('shell', 'am', 'instrument', '-w', '-r',
                  '-e', 'class', classes, RUNNER, timeout=180))
        if args.linked_cashback:
            for name in ['linked-cashback-high.png', 'linked-cashback-flow.json']:
                (out / name).write_bytes(command('exec-out', 'run-as', PACKAGE, 'cat', 'files/' + name))
        cases = {
            'LOW': 'SGTEST Kita tayo bukas sa opisina. Ingat sa biyahe.',
            'MEDIUM': 'SGTEST Your accumulated 7,894.50 Philippine Pesos in cash expires today, or you can choose an https://example.invalid',
            'HIGH': 'SGTEST Your account is suspended. Send your OTP and PIN to https://example.invalid/account immediately.',
            'UNABLE_TO_ASSESS': '123456',
        }
        command('shell', 'cmd', 'connectivity', 'airplane-mode', 'disable')
        results['modem_cases'] = {}
        modem_cases = [(risk, risk, message) for risk, message in cases.items()]
        if args.linked_cashback:
            modem_cases.append(('LINKED_CASHBACK', 'HIGH', '[EWB]You have PHP 5,216 available for cashback. Claim it before it expires today. https://eastwinfu.com/ph'))
        for case_name, risk, message in modem_cases:
            # The test publishes its readiness before a real emulator modem SMS is injected.
            command('shell', 'run-as', PACKAGE, 'rm', '-f', 'files/all-sms-modem-ready')
            process = subprocess.Popen(adb + ['shell', 'am', 'instrument', '-w', '-r',
                '-e', 'class', 'ph.smishguard.AllSmsModemTest', '-e', 'allSmsRisk', risk,
                '-e', 'messageBase64', base64.b64encode(message.encode()).decode(), RUNNER],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            try:
                deadline = time.monotonic() + 40
                while time.monotonic() < deadline:
                    ready = subprocess.run(adb + ['shell', 'run-as', PACKAGE, 'test', '-f',
                        'files/all-sms-modem-ready'], capture_output=True, timeout=10)
                    if ready.returncode == 0:
                        break
                    if process.poll() is not None:
                        raise RuntimeError(process.communicate()[0].decode(errors='replace'))
                    time.sleep(.3)
                else:
                    raise RuntimeError('Modem test not ready: ' + risk)
                sent = command('emu', 'sms', 'send', '5550100', message)
                assert b'OK' in sent and b'KO:' not in sent
                completed('modem-' + case_name.lower(), process.communicate(timeout=90)[0])
                raw = command('exec-out', 'run-as', PACKAGE, 'cat', 'files/all-sms-modem-result.json')
                record = json.loads(raw)
                assert record['expected_risk'] == record['result_risk'] == risk
                assert record['message_matches'] and record['notification_count'] == 1
                results['modem_cases'][case_name] = record
                save()
            finally:
                if process.poll() is None:
                    process.kill()
                    process.communicate()
        if args.initial_reports:
            command('shell', 'run-as', PACKAGE, 'rm', '-f', 'files/initial-report-burst-ready')
            process = subprocess.Popen(adb + ['shell', 'am', 'instrument', '-w', '-r',
                '-e', 'class', 'ph.smishguard.InitialSmsBurstTest#threeIncomingSmsHaveIndependentInitialReports', '-e', 'initialReportBurst', 'true', RUNNER],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            try:
                deadline = time.monotonic() + 40
                while time.monotonic() < deadline:
                    ready = subprocess.run(adb + ['shell', 'run-as', PACKAGE, 'test', '-f',
                        'files/initial-report-burst-ready'], capture_output=True, timeout=10)
                    if ready.returncode == 0:
                        break
                    if process.poll() is not None:
                        raise RuntimeError(process.communicate()[0].decode(errors='replace'))
                    time.sleep(.2)
                else:
                    raise RuntimeError('Initial-report burst test not ready')
                command('shell', 'input', 'keyevent', 'KEYCODE_HOME')
                for sender, risk in [('5550301', 'LOW'), ('5550302', 'MEDIUM'), ('5550303', 'HIGH')]:
                    sent = command('emu', 'sms', 'send', sender, cases[risk])
                    assert b'OK' in sent and b'KO:' not in sent
                completed('initial-report-burst', process.communicate(timeout=90)[0])
                record = json.loads(command('exec-out', 'run-as', PACKAGE, 'cat', 'files/initial-report-burst-result.json'))
                assert record['notification_count'] == 3 and all(r['exact_message_opened'] for r in record['cases'])
                results['initial_report_burst'] = record
                save()
            finally:
                if process.poll() is None:
                    process.kill()
                    process.communicate()
        if args.one_to_one:
            command('shell', 'run-as', PACKAGE, 'rm', '-f', 'files/one-to-one-ready')
            process = subprocess.Popen(adb + ['shell', 'am', 'instrument', '-w', '-r',
                '-e', 'class', 'ph.smishguard.InitialSmsBurstTest#fiveIdenticalSmsFromOneSenderHaveFiveIndependentNotifications',
                '-e', 'oneToOneBurst', 'true', RUNNER], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            try:
                deadline = time.monotonic() + 40
                while time.monotonic() < deadline:
                    ready = subprocess.run(adb + ['shell', 'run-as', PACKAGE, 'test', '-f',
                        'files/one-to-one-ready'], capture_output=True, timeout=10)
                    if ready.returncode == 0:
                        break
                    if process.poll() is not None:
                        raise RuntimeError(process.communicate()[0].decode(errors='replace'))
                    time.sleep(.2)
                else:
                    raise RuntimeError('One-to-one SMS test not ready')
                command('shell', 'input', 'keyevent', 'KEYCODE_HOME')
                for _ in range(5):
                    sent = command('emu', 'sms', 'send', '5550601', cases['LOW'])
                    assert b'OK' in sent and b'KO:' not in sent
                completed('one-to-one-sms', process.communicate(timeout=90)[0])
                record = json.loads(command('exec-out', 'run-as', PACKAGE, 'cat', 'files/one-to-one-result.json'))
                assert record['incoming_sms'] == record['veritxt_notifications'] == record['distinct_tags'] == 5
                assert record['distinct_notification_keys'] == 5 and record['remaining_sms_reports'] == 0
                results['one_to_one_sms'] = record
                save()
            finally:
                if process.poll() is None:
                    process.kill()
                    process.communicate()
        # Existing UI checks cover private notification actions, expiry, and consent.
        completed('notification-privacy-actions', command('shell', 'am', 'instrument', '-w', '-r',
                  '-e', 'class', 'ph.smishguard.PrivacyAndCheckPromptTest', RUNNER, timeout=180))
        launch = command('shell', 'am', 'start', '-W', '-n', PACKAGE + '/ph.smishguard.MainActivity')
        assert b'Status: ok' in launch
        results['normal_launch'] = 'passed'
        results['status'] = 'passed'
    except Exception as error:
        results['error'] = str(error)
        raise
    finally:
        command('shell', 'cmd', 'connectivity', 'airplane-mode', 'enable' if prior_airplane else 'disable', check=False)
        save()


if __name__ == '__main__':
    main()
