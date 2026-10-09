"""Additional emulator-only recovery and 320dp/200% font result checks."""
import argparse
import json
from pathlib import Path
import re
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial', required=True)
    parser.add_argument('--variant', choices=['lr', 'nb', 'svm', 'mbert'], required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output_dir.resolve()
    assert output.is_relative_to((root / 'output').resolve()) or output.is_relative_to((root / 'deliverables').resolve())
    output.mkdir(parents=True, exist_ok=True)
    adb = ['adb', '-s', args.serial]
    package = 'ph.smishguard.' + args.variant

    def command(*parts, timeout=180):
        return subprocess.check_output(adb + list(parts), timeout=timeout)

    assert command('shell', 'getprop', 'ro.kernel.qemu').strip() == b'1'
    api = int(command('shell', 'getprop', 'ro.build.version.sdk').strip())
    prior_font = command('shell', 'settings', 'get', 'system', 'font_scale').decode().strip()
    prior_size = command('shell', 'wm', 'size').decode()
    prior_density = command('shell', 'wm', 'density').decode()
    results = dict(api=api, variant=args.variant, scope='Fictional emulator checks; no human TalkBack acceptance', tests={})

    def run(label, classes):
        raw = command('shell', 'am', 'instrument', '-w', '-r', '-e', 'class', classes,
            '-e', 'diagnostics', 'true', '-e', 'largeFont', 'true',
            package + '.test/ph.smishguard.SoftwareTestRunner', timeout=900).decode(errors='replace')
        (output / (label + '.log')).write_text(raw, encoding='utf-8')
        statuses = [int(s) for s in re.findall(r'INSTRUMENTATION_STATUS_CODE: (-?\d+)', raw)]
        results['tests'][label] = dict(passed=statuses.count(0), skipped=statuses.count(-3), failed=statuses.count(-1) + statuses.count(-2))
        assert 'FAILURES!!!' not in raw and 'OK (' in raw and 'Process crashed' not in raw, label
        assert results['tests'][label]['failed'] == 0
        print(label + ': passed', flush=True)

    try:
        command('install', '-r', str(root / f'android/app/build/outputs/apk/{args.variant}/app-{args.variant}.apk'), timeout=300)
        command('install', '-r', str(root / f'android/app/build/outputs/apk/androidTest/{args.variant}/app-{args.variant}-androidTest.apk'))
        command('shell', 'pm', 'clear', package)
        command('shell', 'settings', 'put', 'system', 'font_scale', '2.0')
        command('shell', 'wm', 'size', '640x1136')
        command('shell', 'wm', 'density', '320')
        run('recovery', 'ph.smishguard.RecoveryTest')
        run('narrow_large_results', 'ph.smishguard.CompactResultTest,ph.smishguard.AccessibilityTest')
        for name in ['long-message-notice', 'accessible-result']:
            for ext in ['png', 'txt']:
                data = command('exec-out', 'run-as', package, 'cat', f'files/reliability/{name}.{ext}')
                (output / (name + '.' + ext)).write_bytes(data)
        if args.variant == 'mbert':
            run('native_resource_close', 'ph.smishguard.MbertResourceTest')
        results['status'] = 'passed'
    finally:
        command('shell', 'settings', 'put', 'system', 'font_scale', prior_font if prior_font != 'null' else '1.0')
        for setting, previous in [('size', prior_size), ('density', prior_density)]:
            match = re.search(r'Override ' + setting + r':\s*(\S+)', previous)
            command('shell', 'wm', setting, match.group(1) if match else 'reset')
        command('shell', 'pm', 'clear', package)
        (output / 'results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
