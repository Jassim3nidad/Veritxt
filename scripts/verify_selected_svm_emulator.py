"""Offline actual-candidate verification on an explicitly verified emulator only."""
import argparse
import json
import re
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]


def verify(adb_path,serial,output,raw_sms=False):
    adb=[str(adb_path),'-s',serial]
    def command(*args,timeout=60):
        return subprocess.run(adb+list(args),check=True,capture_output=True,timeout=timeout).stdout.decode(errors='replace')
    if not serial.startswith('emulator-') or command('shell','getprop','ro.kernel.qemu').strip()!='1':
        raise ValueError('Verified emulator required; physical devices are never modified')
    if command('shell','getprop','sys.boot_completed').strip()!='1':raise ValueError('Emulator not booted')
    airplane=command('shell','settings','get','global','airplane_mode_on').strip()=='1'
    wifi=command('shell','settings','get','global','wifi_on').strip()=='1'
    results=dict(scope='API36 emulator software-only; actual selected frozen SVM, not prospective accuracy or physical-phone benchmark',serial=serial)
    try:
        command('install','-r',str(ROOT/'android/app/build/outputs/apk/development/app-development.apk'),timeout=120)
        command('install','-r',str(ROOT/'android/app/build/outputs/apk/androidTest/development/app-development-androidTest.apk'),timeout=120)
        command('shell','cmd','connectivity','airplane-mode','enable');command('shell','svc','wifi','disable')
        classes='ph.smishguard.SelectedSvmAndroidTest,ph.smishguard.OfflineModelTest,ph.smishguard.SuppliedModelTest'
        response=command('shell','am','instrument','-w','-r','-e','class',classes,'-e','offline','true',
            *(['-e','rawSms','true'] if raw_sms else []),
            'ph.smishguard.dev.test/ph.smishguard.SoftwareTestRunner',timeout=240)
        results['instrumentation']=response
        if not re.search(r'OK \(\d+ tests?\)',response) or 'FAILURES!!!' in response or 'INSTRUMENTATION_FAILED' in response:
            raise RuntimeError('Offline instrumentation failed; see private log')
        aggregate=command('exec-out','run-as','ph.smishguard.dev','cat','files/selected-svm-android-aggregate.json')
        results['selected_candidate']=json.loads(aggregate)
        if results['selected_candidate']['maximum_score_error']>1e-10:raise ValueError('Candidate parity failed')
        if raw_sms:
            raw=command('exec-out','run-as','ph.smishguard.dev','cat','files/raw-sms-android-aggregate.json')
            results['raw_sms']=json.loads(raw)
            if results['raw_sms']['maximum_score_error']>1e-10:raise ValueError('Raw SMS parity failed')
        results['status']='passed'
    finally:
        command('shell','cmd','connectivity','airplane-mode','enable' if airplane else 'disable')
        command('shell','svc','wifi','enable' if wifi else 'disable')
        output.write_text(json.dumps(results,indent=2),encoding='utf-8')
    print('Offline emulator selected/active-model checks passed; aggregate evidence saved')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--adb',type=Path,required=True);p.add_argument('--serial',default='emulator-5554');p.add_argument('--output',type=Path,required=True);p.add_argument('--raw-sms',action='store_true')
    a=p.parse_args();verify(a.adb,a.serial,a.output,a.raw_sms)
