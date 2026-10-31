"""Pin the old APK's exact binary model and copy its existing parity evidence."""
from pathlib import Path
import hashlib
import io
import json
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'research/runs/old-binary-svm-20261020'

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    RUN.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(Path.home()/'Downloads/Veritxt-0.3.0-Updated.zip') as outer:
        names = [n for n in outer.namelist() if n.lower().endswith('.apk')]
        assert len(names)==1
        payload = outer.read(names[0])
    with zipfile.ZipFile(io.BytesIO(payload)) as apk:
        original = apk.read('assets/model.json')
    local = ROOT/'android/app/src/selectedSvm/assets/model.json'
    assert local.read_bytes()==original
    model = json.loads(original)
    assert model['classes']==['ham','smishing'] and len(model['vocabulary'])==18473
    parity = RUN/'parity'
    shutil.copytree(ROOT/'research/runs/bantaytext-20261013/raw-sms-v2/parity', parity)
    assert (parity/'selected-model.json').read_bytes()==original
    identity = dict(old_apk_sha256=hashlib.sha256(payload).hexdigest(),model_sha256=digest(local),
        adapter_sha256=digest(ROOT/'android/app/src/selectedSvm/assets/raw-sms-adapter.json'),
        classes=model['classes'],features=len(model['vocabulary']),threshold=model['threshold'],
        no_retraining=True)
    (RUN/'model-identity.json').write_text(json.dumps(identity,indent=2),encoding='utf-8')
    preserved = {}
    for folder in ['deliverables','docs/cashback-review-20261020','research/runs/multiclass-20261020/run-v1']:
        for p in (ROOT/folder).rglob('*'):
            if p.is_file(): preserved[p.relative_to(ROOT).as_posix()]=digest(p)
    (RUN/'preservation-before.json').write_text(json.dumps(preserved,indent=2),encoding='utf-8')
    print(json.dumps(identity,indent=2))

if __name__=='__main__':main()
