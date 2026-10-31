"""Verify theme switching/persistence on an emulator, then deliver both signed APKs."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MODELS = {
    'nbGeneralization': ('.nb.generalization', 'Retrained-NB-80-20', {
        'assets/model.json':'7cd219db2c9c4559aec60fdea2558821e48cc73085455a9c9caf0b5465d9df5c'}),
    'selectedSvm': ('.svm.selected', 'LinearSVM-60-20-20', {
        'assets/model.json':'15cc0105b0e51e5342682ea36896c4436e515c39d165faf040476046b6b8059c',
        'assets/raw-sms-adapter.json':'11c3ee93fb7523e72b5658bec9f4bc5ee7389d9e5add25d5ca3fceceeedb5b8c'})}


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--serial',default='emulator-5554')
    parser.add_argument('--variant',choices=list(MODELS),required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--destination',type=Path,default=ROOT/'deliverables/Veritxt-Theme-Restored-20261020')
    args=parser.parse_args()
    destination=args.destination.resolve()
    if not destination.is_relative_to((ROOT/'deliverables').resolve()):raise ValueError('Use private deliverables')
    adb=['adb','-s',args.serial]
    def command(*parts,timeout=60):return subprocess.run(adb+list(parts),check=True,capture_output=True,timeout=timeout).stdout
    if command('shell','getprop','ro.kernel.qemu').strip()!=b'1':raise ValueError('Emulator only')
    if command('shell','getprop','sys.boot_completed').strip()!=b'1':raise ValueError('Emulator must be booted')
    prior=command('shell','cmd','uimode','night').decode().strip().split()[-1]
    if prior not in {'yes','no','auto','custom'}:raise ValueError('Unrecognized prior night mode')
    suffix,label,expected=MODELS[args.variant];package='ph.smishguard'+suffix
    apk=ROOT/f'android/app/build/outputs/apk/{args.variant}/app-{args.variant}.apk'
    apk_hash=digest(apk)
    with zipfile.ZipFile(apk) as archive:
        actual={name:hashlib.sha256(archive.read(name)).hexdigest() for name in archive.namelist() if name.startswith('assets/')}
        assert actual==expected, 'Frozen model assets changed or test fixtures entered APK'
    results=dict(variant=args.variant,apk_sha256=apk_hash,model_assets=actual,status='incomplete',physical_device=False,
        tests=[],screenshots=[])
    destination.mkdir(parents=True,exist_ok=True)
    installed=False
    try:
        command('install','-r',str(apk),timeout=180);installed=True
        command('install','-r',str(ROOT/f'android/app/build/outputs/apk/androidTest/{args.variant}/app-{args.variant}-androidTest.apk'),timeout=180)
        command('shell','pm','clear',package)
        command('shell','cmd','statusbar','collapse')
        for dark in (False,True):
            command('shell','cmd','uimode','night','yes' if dark else 'no')
            for phase in ('switch','verifyStoredDark'):
                if phase=='verifyStoredDark':command('shell','am','force-stop',package)
                response=command('shell','am','instrument','-w','-r','-e','class','ph.smishguard.ThemeSettingsTest',
                    '-e','deviceDark',str(dark).lower(),'-e','themePhase',phase,
                    package+'.test/ph.smishguard.SoftwareTestRunner',timeout=180).decode(errors='replace')
                results['tests'].append(dict(device_dark=dark,phase=phase,output=response))
                args.output.parent.mkdir(parents=True,exist_ok=True)
                args.output.write_text(json.dumps(results,indent=2),encoding='utf-8')
                if 'OK (1 test)' not in response or 'FAILURES!!!' in response or 'INSTRUMENTATION_FAILED' in response:
                    raise RuntimeError(response)
                print(args.variant+' '+str(dark)+' '+phase+': passed',flush=True)
            for name in ('light','dark','follow-system','dark-after-process-restart'):
                path=destination/'screenshots'/args.variant/('system-dark' if dark else 'system-light')/(name+'.png')
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(command('exec-out','run-as',package,'cat','files/theme-review/'+name+'.png'))
                results['screenshots'].append(str(path.relative_to(destination)))
        assert digest(apk)==apk_hash
        target=destination/f'Veritxt-{label}-Theme-Restored-20261020.apk'
        shutil.copy2(apk,target)
        assert digest(target)==apk_hash
        results.update(status='passed',delivered_apk=target.name,apk_bytes=target.stat().st_size)
        (destination/(args.variant+'-verification.json')).write_text(json.dumps(results,indent=2),encoding='utf-8')
    finally:
        command('shell','cmd','uimode','night',prior)
        if installed:command('shell','pm','clear',package)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(results,indent=2),encoding='utf-8')
    print('Delivered '+str(target),flush=True)


if __name__=='__main__':main()
