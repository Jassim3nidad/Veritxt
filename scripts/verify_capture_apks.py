"""Check Android compositor screenshots and screen recording; package showcase APKs."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import time

from verify_theme_apks import MODELS, ROOT, digest
import hashlib
import zipfile


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--variant',choices=list(MODELS),required=True)
    parser.add_argument('--serial',default='emulator-5554')
    args=parser.parse_args()
    adb=['adb','-s',args.serial]
    def command(*parts,timeout=60):return subprocess.run(adb+list(parts),check=True,capture_output=True,timeout=timeout).stdout
    assert command('shell','getprop','ro.kernel.qemu').strip()==b'1', 'Emulator only'
    assert command('shell','getprop','sys.boot_completed').strip()==b'1'
    suffix,label,expected=MODELS[args.variant];package='ph.smishguard'+suffix
    runner=package+'.test/ph.smishguard.SoftwareTestRunner'
    apk=ROOT/f'android/app/build/outputs/apk/{args.variant}/app-{args.variant}.apk'
    destination=ROOT/'deliverables/Veritxt-Showcase-20261020'
    media=destination/'capture-evidence'/args.variant;media.mkdir(parents=True,exist_ok=True)
    run=ROOT/'research/runs/screen-capture-20261020'
    apk_hash=digest(apk)
    with zipfile.ZipFile(apk) as archive:
        actual={name:hashlib.sha256(archive.read(name)).hexdigest() for name in archive.namelist() if name.startswith('assets/')}
        assert actual==expected
    results=dict(variant=args.variant,apk_sha256=apk_hash,model_assets=actual,status='incomplete',tests={},physical_device=False)
    font=command('shell','settings','get','system','font_scale').decode().strip()
    remote='/data/local/tmp/veritxt-showcase-'+args.variant+'.mp4'
    def instrument(classes,*extra):
        output=command('shell','am','instrument','-w','-r','-e','class',classes,*extra,runner,timeout=180).decode(errors='replace')
        if 'OK (' not in output or 'FAILURES!!!' in output or 'INSTRUMENTATION_FAILED' in output:raise RuntimeError(output)
        return output
    installed=False
    capture=None
    try:
        command('install','-r',str(apk),timeout=180);installed=True
        command('install','-r',str(ROOT/f'android/app/build/outputs/apk/androidTest/{args.variant}/app-{args.variant}-androidTest.apk'),timeout=180)
        command('shell','pm','clear',package)
        command('shell','settings','put','system','font_scale','1.0')
        command('shell','cmd','statusbar','collapse')
        results['tests']['privacy_lifecycle']=instrument('ph.smishguard.PrivacyLifecycleTest')
        print(args.variant+': lifecycle checks passed',flush=True)
        # No secure flag is changed by instrumentation; the actual app window is captured.
        capture=subprocess.Popen(adb+['shell','am','instrument','-w','-r','-e','class',
            'ph.smishguard.ScreenCaptureTest#actualAppAllowsScreenshotsAndRecording','-e','record','true',runner],
            stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        deadline=time.monotonic()+90
        while time.monotonic()<deadline:
            probe=subprocess.run(adb+['shell','run-as',package,'test','-f','files/capture-review/recording-ready'],capture_output=True,timeout=10)
            if probe.returncode==0:break
            if capture.poll() is not None:raise RuntimeError(capture.communicate()[0].decode(errors='replace'))
            time.sleep(.3)
        else:raise TimeoutError('Capture test did not reach result screen')
        try:
            recorder=subprocess.Popen(adb+['shell','screenrecord','--time-limit','10','--size','720x1600','--bit-rate','4000000',remote],
                stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            try:
                # Scroll the actual result page: static displays can yield a one-frame
                # MP4 with a sub-second media duration despite a longer wall time.
                for i in range(8):
                    start,end=(1700,1000) if i%2==0 else (1000,1700)
                    command('shell','input','swipe','540',str(start),'540',str(end),'600')
                response=recorder.communicate(timeout=25)[0]
                if recorder.returncode!=0:raise RuntimeError(response.decode(errors='replace'))
            finally:
                if recorder.poll() is None:recorder.kill();recorder.communicate()
            command('pull',remote,str(media/'showcase.mp4'))
            payload=(media/'showcase.mp4').read_bytes();assert len(payload)>10000
            # Keep MP4 bytes on-device; adb shell stdin can alter binary input.
            command('shell',f"cat {remote} | run-as {package} sh -c 'cat > files/capture-review/showcase.mp4'")
            received=command('exec-out','run-as',package,'cat','files/capture-review/showcase.mp4')
            assert hashlib.sha256(received).digest()==hashlib.sha256(payload).digest(), 'Video transfer changed bytes'
        finally:
            command('shell','run-as',package,'touch','files/capture-review/recording-done')
        output=capture.communicate(timeout=45)[0].decode(errors='replace')
        (run/(args.variant+'-screenshots.log')).write_text(output,encoding='utf-8')
        if 'OK (1 test)' not in output or 'FAILURES!!!' in output:raise RuntimeError(output)
        results['tests']['os_screenshots']=output
        results['tests']['recording_decode']=instrument('ph.smishguard.ScreenCaptureTest#recordedDisplayContainsVisibleAppFrames',
            '-e','recordingVerification','true')
        for name in ['privacy','home','message','result','explanation-dialog','recording-frame-1','recording-frame-3']:
            (media/(name+'.png')).write_bytes(command('exec-out','run-as',package,'cat','files/capture-review/'+name+'.png'))
        for name in ['capture-verification','recording-verification']:
            results[name]=json.loads(command('exec-out','run-as',package,'cat','files/capture-review/'+name+'.json'))
        # Theme remains usable in the rebuilt showcase app.
        results['tests']['theme_switching']=instrument('ph.smishguard.ThemeSettingsTest','-e','deviceDark','false','-e','themePhase','switch')
        assert digest(apk)==apk_hash
        target=destination/f'Veritxt-{label}-Showcase-20261020.apk'
        shutil.copy2(apk,target);assert digest(target)==apk_hash
        results.update(status='passed',delivered_apk=target.name,apk_bytes=target.stat().st_size,
            recording_sha256=digest(media/'showcase.mp4'),screen_sharing='Secure-window restriction removed; third-party sharing apps not tested')
        (destination/(args.variant+'-verification.json')).write_text(json.dumps(results,indent=2),encoding='utf-8')
        print(args.variant+': OS screenshots, video frames and theme checks passed; delivered '+str(target),flush=True)
    finally:
        if capture is not None and capture.poll() is None:
            capture.kill();capture.communicate()
        if installed and results['status'] != 'passed':
            # Preserve fictional test captures for diagnosing compositor timing.
            for name in ['privacy','home','message','result','explanation-dialog']:
                probe=subprocess.run(adb+['exec-out','run-as',package,'cat','files/capture-review/'+name+'.png'],capture_output=True,timeout=15)
                if probe.returncode==0 and probe.stdout.startswith(b'\x89PNG'):
                    (run/(args.variant+'-failed-'+name+'.png')).write_bytes(probe.stdout)
        command('shell','rm','-f',remote)
        command('shell','settings','put','system','font_scale',font if font!='null' else '1.0')
        if installed:command('shell','pm','clear',package)
        (run/(args.variant+'-verification.json')).write_text(json.dumps(results,indent=2),encoding='utf-8')


if __name__=='__main__':main()
