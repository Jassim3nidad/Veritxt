"""Verify and package the actual private mBERT APK without replacing prior artifacts."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import zipfile
from audit_apk_layout import audit as audit_layout

ROOT = Path(__file__).resolve().parents[1]


def digest(stream):
    return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    destination = args.output_dir.resolve()
    if not destination.is_relative_to((ROOT/'deliverables').resolve()):
        raise ValueError('Private APK destination must be beneath deliverables')
    source = ROOT/'android/app/build/outputs/apk/mbert/app-mbert.apk'
    layout = audit_layout(source)
    if layout['gap_bytes'] > 1024*1024:
        raise ValueError('Excess unreferenced APK space: preserve the APK and packageMbert incremental state, then rebuild a fresh package')
    assets = ROOT/'android/app/src/mbert/assets'
    metadata = json.loads((assets/'model.json').read_text(encoding='utf-8'))
    assert metadata['schema_version'] == 5 and metadata['algorithm'] == 'mbert'
    assert metadata['base_model'] == 'google-bert/bert-base-multilingual-cased'
    assert metadata['revision'] == '3f076fdb1ab68d5b2880cb87a0886f315b8146f8'
    assert not metadata['synthetic'] and not metadata['automatic_warnings_approved'] and not metadata['quantized']
    assert metadata['classes'] == ['ham','smishing'] and metadata['threshold_comparison'] == 'greater_or_equal'
    version = metadata['model_version']
    assert re.fullmatch(r'[A-Za-z0-9._-]+',version)
    asset_hashes = {}
    with zipfile.ZipFile(source) as archive:
        assert sorted(n for n in archive.namelist() if n.startswith('assets/')) == [
            'assets/LICENSE.txt','assets/model.json','assets/model.onnx','assets/vocab.txt']
        for name in ('LICENSE.txt','model.json','model.onnx','vocab.txt'):
            with archive.open('assets/'+name) as stream: bundled = digest(stream)
            with (assets/name).open('rb') as stream: local = digest(stream)
            assert bundled == local
            asset_hashes[name] = local
        assert asset_hashes['model.onnx'] == metadata['model_sha256']
        assert asset_hashes['vocab.txt'] == metadata['vocab_sha256']
        assert archive.getinfo('assets/model.onnx').compress_type == zipfile.ZIP_STORED
        assert not any(n.endswith(('.csv','.pkl','.joblib','.safetensors')) or 'private-cases' in n for n in archive.namelist())
    sdk = Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/build-tools/35.0.0'
    badging = subprocess.check_output([str(sdk/'aapt.exe'),'dump','badging',str(source)],text=True)
    package = 'ph.smishguard.mbert'
    assert f"package: name='{package}'" in badging and "sdkVersion:'26'" in badging
    permissions = re.findall(r"uses-permission: name='([^']+)'",badging)
    assert set(permissions) <= {'android.permission.RECEIVE_SMS','android.permission.POST_NOTIFICATIONS',
                                package+'.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION'}
    subprocess.run([str(sdk/'apksigner.bat'),'verify','--verbose',str(source)],check=True,capture_output=True)
    with source.open('rb') as stream: checksum = digest(stream)
    destination.mkdir(parents=True,exist_ok=True)
    output = destination/f'SmishGuard-{version}-experimental-debug.apk'
    if output.exists():
        with output.open('rb') as stream:
            if digest(stream) != checksum:raise ValueError('Preserve prior APK; choose a new directory')
    else:shutil.copyfile(source,output)
    record = dict(filename=output.name,sha256=checksum,apk_bytes=output.stat().st_size,
        algorithm='mbert',model_version=version,application_id=package,asset_sha256=asset_hashes,
        onnx_bytes=(assets/'model.onnx').stat().st_size,permissions=permissions,signature_verified=True,
        precision='float32',quantized=False,minimum_android='8.0 / API 26',
        research_status='preliminary retrospective; source/rule labels; not independent validation',
        unreferenced_zip_bytes=layout['gap_bytes'])
    (destination/'mbert-apk-manifest.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(json.dumps(record,indent=2))


if __name__ == '__main__':main()
