"""Isolated API 36 reliability runs, using only the dedicated emulator and test fixtures."""
import argparse
import json
from pathlib import Path
import subprocess
import re

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = 'ph.smishguard.dev'
CASES = {
    'accessibility': ('AccessibilityTest#labeledControlsAndHeadingsRemainReachable', '2.0'),
    'result-flow': ('FlowsTest#invalidFailureAndSyntheticResultsStayHonest', '1.0'),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', required=True, choices=['baseline', 'fixed'])
    parser.add_argument('--runs', type=int, default=3)
    parser.add_argument('--case', choices=['both', *CASES], default='both')
    parser.add_argument('--batch', default='', help='Optional unique evidence subdirectory')
    parser.add_argument('--granted', action='store_true', help='Reproduce the specialized suite permission state')
    args = parser.parse_args()
    if not 3 <= args.runs <= 20:
        parser.error('Use 3 to 20 independently initialized runs')
    output = ROOT / 'deliverables/api36-reliability' / args.phase
    if args.batch:
        if not re.fullmatch(r'[a-z0-9-]+', args.batch):
            parser.error('Batch must contain lowercase letters, digits or hyphens only')
        output = output / args.batch
    if output.exists() and any(output.iterdir()):
        parser.error('Evidence directory is not empty; choose a new --batch to preserve previous runs')
    output.mkdir(parents=True, exist_ok=True)
    adb = ['adb', '-s', 'emulator-5554']
    def command(*parts, timeout=180):
        return subprocess.run(adb + list(parts), check=True, capture_output=True, timeout=timeout).stdout
    assert command('shell', 'getprop', 'ro.kernel.qemu').strip() == b'1', 'Emulator only'
    assert command('shell', 'getprop', 'ro.build.version.sdk').strip() == b'36', 'API 36 required'
    assert command('shell', 'getprop', 'sys.boot_completed').strip() == b'1', 'Boot must finish'
    assert b'Application Not Responding' not in command('shell', 'dumpsys', 'window'), 'Resolve emulator ANR first'
    old_font = command('shell', 'settings', 'get', 'system', 'font_scale').decode().strip()
    command('install', '-r', str(ROOT / 'android/app/build/outputs/apk/development/app-development.apk'))
    command('install', '-r', str(ROOT / 'android/app/build/outputs/apk/androidTest/development/app-development-androidTest.apk'))
    results = []
    try:
        for name, (test, scale) in CASES.items():
            if args.case != 'both' and args.case != name:
                continue
            for run in range(1, args.runs + 1):
                assert command('shell', 'pm', 'clear', PACKAGE).strip() == b'Success'
                if args.granted:
                    for permission in ('RECEIVE_SMS', 'POST_NOTIFICATIONS'):
                        command('shell', 'pm', 'grant', PACKAGE, 'android.permission.' + permission)
                command('shell', 'settings', 'put', 'system', 'font_scale', scale)
                flags = ['-e', 'largeFont', 'true'] if name == 'accessibility' else []
                log = command('shell', 'am', 'instrument', '-w', '-e', 'class', 'ph.smishguard.' + test,
                              '-e', 'diagnostics', 'true', *flags,
                              PACKAGE + '.test/ph.smishguard.SoftwareTestRunner').decode(errors='replace')
                prefix = f'{name}-{run}'
                (output / (prefix + '.log')).write_text(log, encoding='utf-8')
                passed = 'OK (1 test)' in log and 'FAILURES!!!' not in log and 'INSTRUMENTATION_FAILED' not in log
                evidence = []
                for suffix in ('txt', 'png'):
                    probe = subprocess.run(adb + ['exec-out', 'run-as', PACKAGE, 'cat',
                                                 f'files/reliability/{name}.{suffix}'], capture_output=True)
                    if probe.returncode == 0:
                        (output / f'{prefix}.{suffix}').write_bytes(probe.stdout)
                        evidence.append(f'{prefix}.{suffix}')
                results.append(dict(case=name, run=run, font_scale=scale, status='passed' if passed else 'failed', evidence=evidence))
                (output / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
                print(f'{args.phase}: {name} run {run}: {results[-1]["status"]}', flush=True)
    finally:
        command('shell', 'settings', 'put', 'system', 'font_scale', old_font if old_font != 'null' else '1.0')
        command('shell', 'pm', 'clear', PACKAGE)
    if any(r['status'] != 'passed' for r in results):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
