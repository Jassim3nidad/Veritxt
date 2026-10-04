"""Isolated synthetic metadata checks for the dated experiment's Android gates."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]

def main():
    env=os.environ.copy();env['JAVA_TOOL_OPTIONS']='-Djdk.net.unixdomain.tmpdir=C:/sg-nonexistent-socket-dir'
    with tempfile.TemporaryDirectory(prefix='smishguard-expanded-guards-') as d:
        project=Path(d)
        for file in ('settings.gradle.kts','build.gradle.kts','gradle.properties','local.properties','android/app/build.gradle.kts','android/app/src/main/AndroidManifest.xml','docs/expanded-comparison-protocol-20261005.md'):
            dest=project/file;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/file,dest)
        protocol=hashlib.sha256((project/'docs/expanded-comparison-protocol-20261005.md').read_bytes()).hexdigest()
        def check(name,expected=None):
            result=subprocess.run([str(ROOT/'gradlew.bat'),'-p',str(project),f':app:verify{name[0].upper()+name[1:]}Model','--console=plain'],cwd=ROOT,env=env,capture_output=True,text=True,timeout=180)
            assert (result.returncode==0 if expected is None else result.returncode!=0 and expected in result.stdout+result.stderr)
            print('PASS',name,'accepted synthetic metadata fixture' if expected is None else 'rejected '+expected,flush=True)
        assets=project/'android/app/src/lr/assets';assets.mkdir(parents=True)
        baseline=dict(schema_version=1,algorithm='lr',synthetic=False,calibration_evaluated=False,calibration={'method':'sigmoid'},
            protocol_sha256=protocol,evaluation_status='preliminary_retrospective',label_status='inherited_unconfirmed',model_version='expanded-20261005-lr-software',
            automatic_warnings_approved=False,score_transform='fitted_sigmoid',calibration_fit_partition='calibration',threshold_fit_partition='validation',vocabulary=['software'])
        def write_base(value):
            (assets/'model.json').write_text(json.dumps(value));h=hashlib.sha256((assets/'model.json').read_bytes()).hexdigest()
            (assets/'review.properties').write_text('algorithm=lr\nmodelVersion=expanded-20261005-lr-software\nreviewKind=automated-pattern-screen\nhumanReview=not_recorded\nreviewReference=expanded-comparison-20261005\nprotocolSha256='+protocol+'\nsha256='+h+'\n')
        write_base(baseline);check('lr')
        write_base({**baseline,'protocol_sha256':'0'*64});check('lr','Preliminary protocol/identity mismatch')
        write_base({**baseline,'calibration_fit_partition':'test'});check('lr','Preliminary protocol/identity mismatch')
        assets=project/'android/app/src/mbert/assets';assets.mkdir(parents=True)
        for name in ('model.onnx','vocab.txt','LICENSE.txt'):(assets/name).write_text('software-only fixture')
        h=hashlib.sha256((assets/'model.onnx').read_bytes()).hexdigest()
        bert=dict(schema_version=5,algorithm='mbert',base_model='google-bert/bert-base-multilingual-cased',revision='3f076fdb1ab68d5b2880cb87a0886f315b8146f8',
            model_sha256=h,vocab_sha256=h,synthetic=False,automatic_warnings_approved=False,evaluation_status='preliminary_retrospective',quantized=False,
            model_version='expanded-20261005-mbert-software',protocol_sha256=protocol,classes=['ham','smishing'],positive_class='smishing',
            threshold_comparison='greater_or_equal',score_transform='sigmoid_of_logit_difference',calibration={'fit_partition':'calibration'})
        (assets/'model.json').write_text(json.dumps(bert));check('mbert')
        (assets/'model.json').write_text(json.dumps({**bert,'classes':['smishing','ham']}));check('mbert','Expanded mBERT protocol/class/calibration mismatch')
        (assets/'model.json').write_text(json.dumps({**bert,'protocol_sha256':'0'*64}));check('mbert','Expanded mBERT protocol/class/calibration mismatch')

if __name__=='__main__':main()
