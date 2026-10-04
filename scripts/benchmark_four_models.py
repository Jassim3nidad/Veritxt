"""Same-session emulator measurements of the four hash-verified private APKs."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--serial',default='emulator-5554')
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    output=args.output.resolve()
    if not output.is_relative_to((ROOT/'research/data').resolve()):raise ValueError('Keep execution evidence private')
    if output.exists():raise ValueError('Preserve prior measurements')
    adb=['adb','-s',args.serial]
    def command(*parts,timeout=60):
        return subprocess.check_output(adb+list(parts),stderr=subprocess.STDOUT,timeout=timeout).decode(errors='replace').strip()
    if command('shell','getprop','ro.kernel.qemu')!='1' or command('shell','getprop','sys.boot_completed')!='1':
        raise ValueError('A booted emulator is required; no physical-device changes')
    if 'Application Not Responding' in command('shell','dumpsys','window'):raise ValueError('Resolve system ANR before benchmark')
    prior_airplane=command('shell','settings','get','global','airplane_mode_on')=='1'
    prior_wifi=command('shell','settings','get','global','wifi_on')=='1'
    names=('lr','nb','svm','mbert');records={}
    result=dict(status='incomplete',started_utc=datetime.now(timezone.utc).isoformat(),
        emulator=command('emu','avd','name').splitlines()[0],api=command('shell','getprop','ro.build.version.sdk'),
        memory=command('shell','cat','/proc/meminfo').splitlines()[:3],
        virtual_cpus=command('shell','getconf','_NPROCESSORS_ONLN'),
        conditions='CPU offline; one app process at a time; same 4 fictional probes, 20 warmups, 200 scans; load excluded',
        results=records,physical_device='not tested')
    try:
        for name in names:
            manifest=json.loads((ROOT/f'deliverables/comparison-20261001/{name}-apk-manifest.json').read_text())
            apk=ROOT/'deliverables/comparison-20261001'/manifest['filename']
            with apk.open('rb') as f:checksum=hashlib.file_digest(f,'sha256').hexdigest()
            if checksum!=manifest['sha256']:raise ValueError('Preserved APK changed')
            command('install','-r',str(apk),timeout=300)
            command('install','-r',str(ROOT/f'android/app/build/outputs/apk/androidTest/{name}/app-{name}-androidTest.apk'),timeout=120)
            command('shell','pm','clear',f'ph.smishguard.{name}')
        command('shell','cmd','connectivity','airplane-mode','enable')
        command('shell','svc','wifi','disable')
        for name in names:
            for other in names:command('shell','am','force-stop',f'ph.smishguard.{other}')
            test='MbertDeviceTest' if name=='mbert' else 'ComparisonRuntimeTest'
            log=command('shell','am','instrument','-w','-e','class',f'ph.smishguard.{test}','-e','offline','true',
                        f'ph.smishguard.{name}.test/ph.smishguard.SoftwareTestRunner',timeout=900)
            (output.parent/f'common-benchmark-{name}.log').write_text(log,encoding='utf-8')
            if 'OK (1 test)' not in log or 'FAILURES!!!' in log:raise ValueError(f'{name} benchmark failed; private log retained')
            if name=='mbert':
                values=json.loads(re.search(r'MBERT_AGGREGATE=(\{[^\r\n]+\})',log).group(1))
            else:
                match=re.search(r'algorithm='+name+r' probes=4 warmups=20 scans=200 scored=(\d+) abstained=(\d+) model_bytes=(\d+) p50_ms=([\d.]+) p95_ms=([\d.]+)',log)
                if match is None:raise ValueError('Missing recorded benchmark')
                scored,abstained,size,p50,p95=match.groups()
                values=dict(scored=int(scored),abstained=int(abstained),model_bytes=int(size),p50_ms=float(p50),p95_ms=float(p95),probes=4,warmups=20,scans=200)
            values['apk_sha256']=json.loads((ROOT/f'deliverables/comparison-20261001/{name}-apk-manifest.json').read_text())['sha256']
            records[name]=values
            output.write_text(json.dumps(result,indent=2),encoding='utf-8')
            print(f'{name}: common-device benchmark passed',flush=True)
        result['status']='passed';result['finished_utc']=datetime.now(timezone.utc).isoformat()
    finally:
        output.write_text(json.dumps(result,indent=2),encoding='utf-8')
        command('shell','cmd','connectivity','airplane-mode','enable' if prior_airplane else 'disable')
        command('shell','svc','wifi','enable' if prior_wifi else 'disable')
        for name in names:command('shell','am','force-stop',f'ph.smishguard.{name}')


if __name__=='__main__':main()
