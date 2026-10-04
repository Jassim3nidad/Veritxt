"""Stage, build, test and package one frozen expanded model; keep evidence private."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
PRIVATE=ROOT/'research/data/expanded-20261005'
RUN=PRIVATE/'experiment-v1'

def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def execute(command,log,env,timeout=1200):
    start=time.perf_counter()
    with log.open('wb') as f:r=subprocess.run(command,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
    return dict(exit_code=r.returncode,seconds=time.perf_counter()-start,log_sha256=digest(log))

def main():
    p=argparse.ArgumentParser();p.add_argument('algorithm',choices=['lr','nb','svm','mbert']);p.add_argument('--skip-emulator',action='store_true');a=p.parse_args();name=a.algorithm
    env=os.environ.copy();env['JAVA_TOOL_OPTIONS']=(env.get('JAVA_TOOL_OPTIONS','')+' -Djdk.net.unixdomain.tmpdir=C:/sg-nonexistent-socket-dir').strip()
    env['PATH']=str(Path(env['LOCALAPPDATA'])/'Android/Sdk/platform-tools')+os.pathsep+env['PATH']
    if not (RUN/'four-model-aggregate.json').exists():raise ValueError('Complete the four-model frozen evaluation before final APK staging')
    assets=ROOT/f'android/app/src/{name}/assets';backup=PRIVATE/'previous-assets'/name
    if not backup.exists():raise ValueError('Back up previous assets first')
    origin=RUN/'mbert/app-assets' if name=='mbert' else RUN/name
    names=('LICENSE.txt','model.json','model.onnx','vocab.txt') if name=='mbert' else ('model.json','review.properties')
    expected_version=json.loads((origin/'model.json').read_text())['model_version']
    if not expected_version.startswith(f'expanded-20261005-{name}-'):raise ValueError('Wrong new model identity')
    for file in names:shutil.copyfile(origin/file,assets/file)
    record=dict(algorithm=name,model_version=expected_version,asset_sha256={f:digest(assets/f) for f in names})
    title=name[0].upper()+name[1:];parity=RUN/'mbert' if name=='mbert' else RUN/name/'parity'
    prop='mbertParityDir' if name=='mbert' else 'modelParityDir'
    command=[str(ROOT/'gradlew.bat'),f':app:assemble{title}',f':app:lint{title}',f':app:test{title}UnitTest',f':app:assemble{title}AndroidTest',
        f'-PinstrumentedBuild={name}',f'-P{prop}={parity.resolve()}','--console=plain']
    record['build']=execute(command,PRIVATE/f'build-{name}.log',env)
    if record['build']['exit_code']==0:
        suites=[ET.parse(f).getroot() for f in (ROOT/f'android/app/build/test-results/test{title}UnitTest').glob('TEST-*.xml')]
        record['jvm']={key:sum(int(s.attrib.get(key,0)) for s in suites) for key in ('tests','failures','errors','skipped')}
        lint=ET.parse(ROOT/f'android/app/build/reports/lint-results-{name}.xml').getroot()
        record['lint']={severity:sum(i.attrib.get('severity')==severity for i in lint.findall('issue')) for severity in ('Error','Warning','Fatal')}
        if not a.skip_emulator:
            command=[sys.executable,str(ROOT/'scripts/emulator_verify.py'),'--variant',name,'--output',str(PRIVATE/f'emulator-{name}.json'),
                '--demo-screenshots',str(ROOT/f'deliverables/expanded-20261005/screenshots/{name}')]
            record['emulator']=execute(command,PRIVATE/f'emulator-{name}.log',env,1800)
        script='package_mbert.py' if name=='mbert' else 'package_comparison.py'
        command=[sys.executable,str(ROOT/'scripts'/script)]+([] if name=='mbert' else [name])+['--output-dir',str(ROOT/'deliverables/expanded-20261005')]
        record['package']=execute(command,PRIVATE/f'package-{name}.log',env)
    (PRIVATE/f'verification-{name}.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(json.dumps(record,indent=2),flush=True)
    if any(v.get('exit_code',0)!=0 for v in record.values() if isinstance(v,dict)):raise SystemExit(1)

if __name__=='__main__':main()
