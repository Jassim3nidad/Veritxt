"""Verify/install/test only the restored binary SVM APK on a verified emulator.

Existing installed app packages are untouched. Emulator network settings restored.
"""
from pathlib import Path
import argparse
import json
import os
import subprocess
import time
import zipfile
from smishguard import multiclass_comparison as m

ROOT=Path(__file__).resolve().parents[1]
PACKAGE='ph.smishguard.svm.oldbinary'
RUNNER=PACKAGE+'.test/ph.smishguard.SoftwareTestRunner'
MODEL_SHA='15cc0105b0e51e5342682ea36896c4436e515c39d165faf040476046b6b8059c'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial',default='emulator-5554')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    apk=ROOT/'android/app/build/outputs/apk/oldSvm/app-oldSvm.apk'
    testapk=ROOT/'android/app/build/outputs/apk/androidTest/oldSvm/app-oldSvm-androidTest.apk'
    results=dict(status='incomplete',package=PACKAGE,apk_sha256=m.legacy.digest(apk))
    with zipfile.ZipFile(apk) as z:
        assets=[p for p in z.namelist() if p.startswith('assets/')]
        import hashlib
        assert hashlib.sha256(z.read('assets/model.json')).hexdigest()==MODEL_SHA
        assert set(assets)=={'assets/model.json','assets/raw-sms-adapter.json'}
        assert hashlib.sha256(z.read('assets/raw-sms-adapter.json')).hexdigest()=='11c3ee93fb7523e72b5658bec9f4bc5ee7389d9e5add25d5ca3fceceeedb5b8c'
        assert not any('cases.json' in p or p.endswith(('.pkl','.csv')) for p in assets)
        results['packaged_assets']=assets;results['model_sha256']=MODEL_SHA
    adb=['adb','-s',args.serial]
    def command(*parts,timeout=60,check=True):
        return subprocess.run(adb+list(parts),capture_output=True,timeout=timeout,check=check).stdout
    assert command('shell','getprop','ro.kernel.qemu').strip()==b'1','Emulator only'
    assert command('shell','getprop','sys.boot_completed').strip()==b'1','Emulator not booted'
    results['api']=command('shell','getprop','ro.build.version.sdk').decode().strip()
    prior_airplane=command('shell','settings','get','global','airplane_mode_on').strip()==b'1'
    prior_wifi=command('shell','settings','get','global','wifi_on').strip()==b'1'
    def save():m.save(out/'emulator-results.json',results)
    def run_test(label,classes,extra=()):
        output=command('shell','am','instrument','-w','-r','-e','class',classes,*extra,RUNNER,timeout=360).decode(errors='replace')
        (out/(label+'.log')).write_text(output,encoding='utf-8')
        if 'OK (' not in output or 'FAILURES!!!' in output or 'INSTRUMENTATION_FAILED' in output:
            raise RuntimeError(label+' failed:\n'+output)
        results[label]=output.strip();save();print(label+': passed',flush=True)
    save()
    try:
        command('install','-r',str(apk),timeout=180)
        command('install','-r',str(testapk),timeout=180)
        # This package is the newly created build only; no old application data is cleared.
        command('shell','pm','clear',PACKAGE)
        command('shell','cmd','connectivity','airplane-mode','enable')
        command('shell','svc','wifi','disable')
        run_test('native-parity','ph.smishguard.OldBinarySvmAndroidTest')
        raw=command('exec-out','run-as',PACKAGE,'cat','files/old-binary-android-parity.json')
        (out/'old-binary-android-parity.json').write_bytes(raw)
        results['parity']=json.loads(raw)
        run_test('manual-two-categories','ph.smishguard.OldBinarySvmFlowTest')
        for label in ['Ham','Smishing']:
            (out/(label+'.png')).write_bytes(command('exec-out','run-as',PACKAGE,'cat','files/old-binary/'+label+'.png'))
        # Existing regression tests retain their established injected fixtures.
        command('shell','pm','clear',PACKAGE)
        run_test('existing-flows','ph.smishguard.FlowsTest')
        command('shell','pm','clear',PACKAGE)
        run_test('privacy-lifecycle','ph.smishguard.PrivacyLifecycleTest')
        command('shell','pm','clear',PACKAGE)
        run_test('risk-results','ph.smishguard.RiskResultsTest')
        command('shell','pm','clear',PACKAGE)
        run_test('theme-settings','ph.smishguard.ThemeSettingsTest')
        # Actual modem SMS and the real bundled classifier, not a prediction stub.
        # The emulator's cellular radio must be on for console SMS delivery.
        # Offline numerical parity above deliberately ran with airplane mode on.
        command('shell','cmd','connectivity','airplane-mode','disable')
        command('shell','pm','clear',PACKAGE)
        process=subprocess.Popen(adb+['shell','am','instrument','-w','-r','-e','class',
            'ph.smishguard.IncomingPromptModemTest#realSmsFlaggedByModelShowsAutomaticWarning',
            '-e','modemWarning','true','-e','realModel','true',RUNNER],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        try:
            deadline=time.monotonic()+50
            while time.monotonic()<deadline:
                probe=subprocess.run(adb+['shell','run-as',PACKAGE,'test','-f','files/automatic-warning-ready'],capture_output=True,timeout=10)
                if probe.returncode==0:break
                if process.poll() is not None:raise RuntimeError(process.communicate()[0].decode(errors='replace'))
                time.sleep(.3)
            else:raise RuntimeError('Real-model SMS receiver test not ready')
            message='SGTEST Your account is suspended. Send your OTP and PIN to https://example.invalid/account immediately.'
            injected=command('emu','sms','send','5550100',message)
            if b'OK' not in injected or b'KO:' in injected:raise RuntimeError('Emulator rejected synthetic SMS injection')
            output=process.communicate(timeout=100)[0].decode(errors='replace')
            (out/'real-model-incoming-sms.log').write_text(output,encoding='utf-8')
            if 'OK (1 test)' not in output or 'FAILURES!!!' in output:raise RuntimeError(output)
            results['real_model_incoming_sms']=output.strip();save();print('real-model incoming SMS: passed',flush=True)
        finally:
            if process.poll() is None:process.kill();process.communicate()
        # Launch the normal app process (without the test Application injection).
        command('shell','am','force-stop',PACKAGE)
        launch=command('shell','am','start','-W','-n',PACKAGE+'/ph.smishguard.MainActivity').decode(errors='replace')
        assert 'Status: ok' in launch
        results['normal_launch']=launch.strip();results['status']='passed'
    except Exception as e:
        results['error']=str(e);raise
    finally:
        command('shell','cmd','connectivity','airplane-mode','enable' if prior_airplane else 'disable',check=False)
        command('shell','svc','wifi','enable' if prior_wifi else 'disable',check=False)
        save()


if __name__=='__main__':main()
