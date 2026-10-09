"""Private, non-overwriting APK handoff with frozen-asset and signature evidence."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import zipfile

from audit_apk_layout import audit

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def command(*args):
    return subprocess.check_output(args, cwd=ROOT, text=True, stderr=subprocess.STDOUT)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--previous-build', type=Path, required=True)
    args = parser.parse_args()
    destination = args.output_dir.resolve()
    assert destination.is_relative_to((ROOT / 'deliverables').resolve())
    assert not (destination / 'APK-MANIFEST.json').exists(), 'Use a new handoff directory'
    assert not command('git', 'diff', 'HEAD', '--', 'android/app').strip(), 'Commit exact app source first'
    source = command('git', 'rev-parse', 'HEAD').strip()
    freeze = json.loads((ROOT / 'docs/validation-stage-verification-20261006.json').read_text())['model_freeze']
    sdk = Path(os.environ['LOCALAPPDATA']) / 'Android/Sdk/build-tools/35.0.0'
    records = []
    for variant in ['lr', 'nb', 'svm', 'mbert']:
        apk = ROOT / f'android/app/build/outputs/apk/{variant}/app-{variant}.apk'
        old = args.previous_build / f'outputs/apk/{variant}/app-{variant}.apk'
        asset_dir = ROOT / f'android/app/src/{variant}/assets'
        metadata = json.loads((asset_dir / 'model.json').read_text(encoding='utf-8'))
        frozen = freeze['models'][variant]
        assert metadata['model_version'] == frozen['model_version']
        assert metadata['threshold'] == frozen['threshold']
        asset_hashes = {}
        with zipfile.ZipFile(apk) as archive:
            actual = sorted(n for n in archive.namelist() if n.startswith('assets/') and not n.endswith('/'))
            assert actual == sorted('assets/' + p.name for p in asset_dir.iterdir())
            for path in asset_dir.iterdir():
                with archive.open('assets/' + path.name) as stream:
                    bundled = hashlib.file_digest(stream, 'sha256').hexdigest()
                expected = frozen['assets'][path.relative_to(ROOT).as_posix()]
                assert sha(path) == bundled == expected
                asset_hashes[path.name] = bundled
            abis = sorted({n.split('/')[1] for n in archive.namelist() if n.startswith('lib/') and n.endswith('.so')})
            assert not any(n.endswith(('.csv', '.pkl', '.joblib', '.safetensors')) or 'private-cases' in n for n in archive.namelist())
        layout = audit(apk)
        assert layout['gap_bytes'] <= 1024 * 1024
        badging = command(str(sdk / 'aapt.exe'), 'dump', 'badging', str(apk))
        identity = re.search(r"package: name='([^']+)' versionCode='([^']+)' versionName='([^']+)'", badging)
        package, code, version = identity.groups()
        assert package == 'ph.smishguard.' + variant and code == '3'
        assert "sdkVersion:'26'" in badging
        permissions = re.findall(r"uses-permission: name='([^']+)'", badging)
        assert set(permissions) <= {'android.permission.RECEIVE_SMS', 'android.permission.POST_NOTIFICATIONS', package + '.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION'}
        signature = command(str(sdk / 'apksigner.bat'), 'verify', '--verbose', '--print-certs', str(apk))
        previous = command(str(sdk / 'apksigner.bat'), 'verify', '--print-certs', str(old))
        cert = re.search(r'Signer #1 certificate SHA-256 digest: ([0-9a-f]+)', signature).group(1)
        assert cert == re.search(r'Signer #1 certificate SHA-256 digest: ([0-9a-f]+)', previous).group(1)
        name = f'SmishGuard-0.3.0-{variant}-{metadata["model_version"]}-experimental.apk'
        output = destination / name
        assert not output.exists(), 'Never overwrite an APK'
        destination.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(apk, output)
        digest = sha(apk)
        assert sha(output) == digest
        records.append(dict(filename=name, absolute_path=str(output), source_commit=source,
            application_id=package, version_code=int(code), version_name=version,
            algorithm={'lr': 'Logistic Regression', 'nb': 'Multinomial Naive Bayes', 'svm': 'Linear SVM', 'mbert': 'float32 mBERT'}[variant],
            variant=variant, model_identifier=metadata['model_version'], asset_sha256=asset_hashes,
            threshold=metadata['threshold'], comparator=frozen['threshold_comparison'],
            apk_bytes=output.stat().st_size, apk_sha256=digest, signature_verified=True,
            signer_certificate_sha256=cert, previous_signature_compatible=True,
            minimum_android='8.0 / API 26', supported_abis=abis, permissions=permissions,
            internet_permission_absent=True, unreferenced_zip_bytes=layout['gap_bytes'],
            emulator_evidence='See docs/audit-fixes-20261009-evidence.json for actual API checks and limitations',
            physical_device_status='Pending; no physical device tested'))
    (destination / 'APK-MANIFEST.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
    (destination / 'SHA256SUMS.txt').write_text(''.join(r['apk_sha256'] + '  ' + r['filename'] + '\n' for r in records), encoding='utf-8')
    print(json.dumps([dict(variant=r['variant'], sha256=r['apk_sha256'], bytes=r['apk_bytes']) for r in records], indent=2))


if __name__ == '__main__':
    main()
