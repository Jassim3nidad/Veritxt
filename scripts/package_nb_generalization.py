"""Package only the checked native NB APK and sanitized provenance, never test SMS."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_MODEL = '7cd219db2c9c4559aec60fdea2558821e48cc73085455a9c9caf0b5465d9df5c'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package(export, emulator_evidence, destination):
    export, emulator_evidence, destination = Path(export), Path(emulator_evidence), Path(destination).resolve()
    if not destination.is_relative_to((ROOT/'deliverables').resolve()):
        raise ValueError('Use an ignored deliverables directory')
    manifest = json.loads((export/'export-manifest.json').read_text(encoding='utf-8'))
    host = json.loads((export/'nb-jvm-parity.json').read_text(encoding='utf-8'))
    emulator = json.loads(emulator_evidence.read_text(encoding='utf-8'))
    assert emulator['variant'] == 'nbGeneralization' and emulator['status'] == 'passed'
    device = emulator['nb_native_parity']
    for result in (host, device):
        assert result['cases'] == manifest['cases'] and result['held_out_cases'] == 684
        assert result['maximum_score_error'] <= 1e-10 and result['maximum_feature_error'] <= 1e-10
    apk = ROOT/'android/app/build/outputs/apk/nbGeneralization/app-nbGeneralization.apk'
    assert emulator['apk_sha256'] == digest(apk), 'APK changed after emulator validation'
    with zipfile.ZipFile(apk) as archive:
        names = archive.namelist()
        assert not any(n.endswith(('.csv', '.pkl', '.pickle', '.tsv')) or 'parity' in n.lower() or 'cases.json' in n for n in names)
        assets = [n for n in names if n.startswith('assets/')]
        assert assets == ['assets/model.json']
        assert not any('raw-sms-adapter' in n or 'nb-generalization-cases' in n for n in assets)
        model_bytes = archive.read('assets/model.json')
        assert hashlib.sha256(model_bytes).hexdigest() == EXPECTED_MODEL == manifest['model_sha256']
        model = json.loads(model_bytes)
        assert model['schema_version'] == 9 and model['input_view'] == 'raw_sms' and model['threshold'] == .5
        assert model['provenance']['pipeline_sha256'] == manifest['source_pipeline_sha256']
    destination.mkdir(parents=True, exist_ok=True)
    target = destination/'Veritxt-0.3.0-Retrained-NB-80-20.apk'
    shutil.copy2(apk, target)
    delivery = dict(apk=target.name, apk_sha256=digest(target), apk_bytes=target.stat().st_size,
        application_id='ph.smishguard.nb.generalization', min_android='8.0 (API 26)',
        app_label='Veritxt · Retrained NB', version_name='0.3.0-nb-generalization-experimental',
        signing='Android debug key; experimental local build',
        model=manifest, jvm_parity=host, android_parity=device,
        emulator_status=emulator['status'], physical_device_tested=False,
        research_limits='Retrospective inherited labels; source-held-out performance is weak. Scores are uncalibrated.',
        ui_score='Existing evidence-index-v1 risk score combines model signal with visible indicators; it is not NB accuracy or probability.')
    (destination/'build-manifest.json').write_text(json.dumps(delivery, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    (destination/'SHA256SUMS.txt').write_text(delivery['apk_sha256']+'  '+target.name+'\n', encoding='ascii')
    shutil.copy2(emulator_evidence, destination/'emulator-verification.json')
    print(json.dumps(dict(apk=str(target), sha256=delivery['apk_sha256'], bytes=delivery['apk_bytes']), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--export', required=True)
    parser.add_argument('--emulator-evidence', required=True)
    parser.add_argument('--destination', default=str(ROOT/'deliverables/Veritxt-Retrained-NB-20261020'))
    args = parser.parse_args()
    package(args.export, args.emulator_evidence, args.destination)
