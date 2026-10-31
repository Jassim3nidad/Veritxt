"""Exercise the USB demo APK and the delivered PowerShell transport on an offline emulator."""
from pathlib import Path
import argparse
import base64
import hashlib
import json
import shutil
import shlex
import subprocess
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = 'ph.smishguard.demo.usb'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial', default='emulator-5554')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    adb = ['adb', '-s', args.serial]

    def command(*parts, timeout=90, check=True):
        return subprocess.run(adb + list(parts), capture_output=True, timeout=timeout, check=check).stdout

    assert command('shell', 'getprop', 'ro.kernel.qemu').strip() == b'1', 'Emulator only; never alter a physical phone'
    assert command('shell', 'getprop', 'sys.boot_completed').strip() == b'1'
    apk = ROOT / 'android/app/build/outputs/apk/usbDemo/app-usbDemo.apk'
    test_apk = ROOT / 'android/app/build/outputs/apk/androidTest/usbDemo/app-usbDemo-androidTest.apk'
    cases_file = ROOT / 'scripts/usb-demo-messages.json'
    cases = json.loads(cases_file.read_text(encoding='utf-8'))
    # Exercise Unicode, newlines and shell syntax without treating any input as a command.
    cases.append(dict(id='utf8-and-shell-literals', text='SGTEST Kumusta po 😀\nMeeting sa café; "quotes" & literal $(text)'))
    case_path = out / 'fictional-messages.json'
    case_path.write_text(json.dumps(cases, ensure_ascii=False), encoding='utf-8')
    powershell = shutil.which('powershell') or shutil.which('pwsh')
    assert powershell
    script = [powershell, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(ROOT / 'scripts/usb-demo.ps1'), '-Serial', args.serial]
    results = dict(status='incomplete', package=PACKAGE, physical_phone_tested=False,
                   api=command('shell', 'getprop', 'ro.build.version.sdk').decode().strip(),
                   apk_sha256=hashlib.sha256(apk.read_bytes()).hexdigest())
    results['powershell_executable'] = powershell
    results['transport_sha256'] = hashlib.sha256((ROOT / 'scripts/usb-demo.ps1').read_bytes()).hexdigest()
    results['samples_sha256'] = hashlib.sha256(cases_file.read_bytes()).hexdigest()
    with zipfile.ZipFile(apk) as archive:
        assets = {n for n in archive.namelist() if n.startswith('assets/')}
        assert assets == {'assets/model.json', 'assets/raw-sms-adapter.json'}
        results['model_sha256'] = hashlib.sha256(archive.read('assets/model.json')).hexdigest()
        results['adapter_sha256'] = hashlib.sha256(archive.read('assets/raw-sms-adapter.json')).hexdigest()
        assert results['model_sha256'] == '15cc0105b0e51e5342682ea36896c4436e515c39d165faf040476046b6b8059c'
        assert results['adapter_sha256'] == '11c3ee93fb7523e72b5658bec9f4bc5ee7389d9e5add25d5ca3fceceeedb5b8c'

    def save():
        (out / 'verification.json').write_text(json.dumps(results, indent=2), encoding='utf-8')

    def checked(label, output):
        text = output.decode(errors='replace')
        (out / (label + '.log')).write_text(text, encoding='utf-8')
        assert 'OK (' in text and 'FAILURES!!!' not in text and 'INSTRUMENTATION_FAILED' not in text, text
        results[label] = text
        save()

    prior = {key: command('shell', 'settings', 'get', 'global', key).strip().decode()
             for key in ['airplane_mode_on', 'wifi_on', 'mobile_data']}
    process = None
    try:
        install = subprocess.run(script + ['-Install', '-ApkPath', str(apk)], capture_output=True, timeout=180)
        (out / 'powershell-install.log').write_bytes(install.stdout + install.stderr)
        assert install.returncode == 0, install.stderr.decode(errors='replace')
        command('install', '-r', str(test_apk), timeout=180)
        command('shell', 'pm', 'revoke', PACKAGE, 'android.permission.RECEIVE_SMS', check=False)
        command('shell', 'svc', 'wifi', 'disable')
        command('shell', 'svc', 'data', 'disable')
        command('shell', 'cmd', 'connectivity', 'airplane-mode', 'enable')
        # Telephony may retain the global preference while airplane mode blocks its
        # radio; make the emulator preference explicit as well, then restore it below.
        command('shell', 'settings', 'put', 'global', 'mobile_data', '0')
        results['offline_settings'] = {key: command('shell', 'settings', 'get', 'global', key).decode().strip() for key in prior}
        assert results['offline_settings'] == {'airplane_mode_on': '1', 'wifi_on': '0', 'mobile_data': '0'}
        encoded = base64.b64encode(json.dumps(cases).encode()).decode()
        command('shell', 'run-as', PACKAGE, 'rm', '-f', 'files/usb-demo-ready')
        runner = PACKAGE + '.test/ph.smishguard.SoftwareTestRunner'
        process = subprocess.Popen(adb + ['shell', 'am', 'instrument', '-w', '-r', '-e', 'class',
            'ph.smishguard.UsbDemoTest#realUsbTransportReportsInstalledModelAndOpensEveryMessage',
            '-e', 'usbCasesBase64', encoded, runner], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            if subprocess.run(adb + ['shell', 'run-as', PACKAGE, 'test', '-f', 'files/usb-demo-ready'], capture_output=True).returncode == 0:
                break
            if process.poll() is not None:
                raise RuntimeError(process.communicate()[0].decode(errors='replace'))
            time.sleep(.3)
        else:
            raise TimeoutError('Demo test readiness')
        command('shell', 'input', 'keyevent', 'KEYCODE_HOME')
        sent = subprocess.run(script + ['-CasesPath', str(case_path), '-DelaySeconds', '1'], capture_output=True, timeout=90)
        (out / 'powershell-send.log').write_bytes(sent.stdout + sent.stderr)
        assert sent.returncode == 0, (sent.stdout + sent.stderr).decode(errors='replace')
        checked('offline-usb-transport', process.communicate(timeout=100)[0])
        results['actual_model_reports'] = json.loads(command('exec-out', 'run-as', PACKAGE, 'cat', 'files/usb-demo-results.json'))
        checked('privacy-and-failures', command('shell', 'am', 'instrument', '-w', '-r', '-e', 'class',
            'ph.smishguard.UsbDemoTest#demoRespectsPrivacyAndReportsModelFailuresWithoutScores', runner))
        checked('existing-notification-regressions', command('shell', 'am', 'instrument', '-w', '-r', '-e', 'class',
            'ph.smishguard.AllSmsNotificationsTest,ph.smishguard.PrivacyAndCheckPromptTest', runner, timeout=240))
        invalid = command('shell', 'am', 'broadcast', '-n', PACKAGE + '/ph.smishguard.demo.UsbDemoReceiver',
            '-a', 'ph.smishguard.action.USB_DEMO_MESSAGE', '--es', 'message_base64', 'invalid!').decode()
        assert 'result=2' in invalid and 'Invalid demo message' in invalid
        results['malformed_broadcast_rejected'] = True
        checked('prepare-normal-cold-start', command('shell', 'am', 'instrument', '-w', '-r', '-e', 'class',
            'ph.smishguard.UsbDemoTest#prepareNormalProcessColdStart', runner))
        command('shell', 'pm', 'revoke', PACKAGE, 'android.permission.RECEIVE_SMS', check=False)
        command('shell', 'am', 'force-stop', PACKAGE)
        # No instrumentation process or Check tap: Android creates the shipped Application here.
        cold = subprocess.run(script + ['-Message', cases[2]['text'], '-DelaySeconds', '0'], capture_output=True, timeout=30)
        assert cold.returncode == 0, (cold.stdout + cold.stderr).decode(errors='replace')
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            # Query only active keys; dumpsys also includes historical notifications.
            keys = command('shell', 'cmd', 'notification', 'list').decode().splitlines()
            active = [key for key in keys if '|' + PACKAGE + '|' in key]
            dump = '\n'.join(command('shell', 'cmd', 'notification', 'get', shlex.quote(key)).decode(errors='replace') for key in active)
            if 'Demo · High Risk' in dump and 'Risk Score: 100/100' in dump:
                break
            time.sleep(.2)
        else:
            raise AssertionError('Normal cold-start report was not published')
        (out / 'normal-process-cold-start.log').write_bytes(cold.stdout + cold.stderr)
        (out / 'normal-process-active-report.txt').write_text(dump, encoding='utf-8')
        results['normal_process_cold_start'] = 'passed; actual app, radios off, no SMS permission or incoming consent'
        command('shell', 'input', 'keyevent', 'KEYCODE_WAKEUP')
        command('shell', 'wm', 'dismiss-keyguard')
        command('shell', 'cmd', 'statusbar', 'expand-notifications')
        time.sleep(.8)
        (out / 'demo-notification.png').write_bytes(command('exec-out', 'screencap', '-p'))
        command('shell', 'cmd', 'statusbar', 'collapse')
        launch = command('shell', 'am', 'start', '-W', '-n', PACKAGE + '/ph.smishguard.MainActivity')
        assert b'Status: ok' in launch
        results['normal_launch'] = 'passed'
        results['status'] = 'passed'
    except Exception as error:
        results['error'] = str(error)
        raise
    finally:
        if process is not None and process.poll() is None:
            process.kill(); process.communicate()
        command('shell', 'cmd', 'connectivity', 'airplane-mode', 'enable' if prior['airplane_mode_on'] == '1' else 'disable', check=False)
        command('shell', 'svc', 'wifi', 'enable' if prior['wifi_on'] == '1' else 'disable', check=False)
        command('shell', 'svc', 'data', 'enable' if prior['mobile_data'] == '1' else 'disable', check=False)
        if prior['mobile_data'] in ['0', '1']:
            command('shell', 'settings', 'put', 'global', 'mobile_data', prior['mobile_data'], check=False)
        elif prior['mobile_data'] == 'null':
            command('shell', 'settings', 'delete', 'global', 'mobile_data', check=False)
        save()
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
