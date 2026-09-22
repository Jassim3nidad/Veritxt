"""Package portable source and an already-built development/debug APK. Does not build or sign."""
from pathlib import Path
import hashlib
import shutil
import zipfile
import argparse
import json
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("--variant", choices=["debug", "development"], default="development")
parser.add_argument("--output-dir", type=Path, default=Path("deliverables"))
args = parser.parse_args()

root = Path(__file__).resolve().parents[1]
output = (root / args.output_dir).resolve()
if not output.is_relative_to((root / 'deliverables').resolve()):
    raise SystemExit('Packages must remain in ignored deliverables/')
output.mkdir(parents=True, exist_ok=True)
apk = root / f"android/app/build/outputs/apk/{args.variant}/app-{args.variant}.apk"
if not apk.is_file():
    raise SystemExit("Build the APK before packaging.")
with zipfile.ZipFile(apk) as packaged:
    names = packaged.namelist()
    if any(n.endswith(".csv") or "dataset" in n.lower() or "supplied-parity" in n for n in names):
        raise SystemExit("Unexpected dataset/test data in APK")
    if args.variant == "development":
        model_bytes = packaged.read("assets/model.json")
        model = json.loads(model_bytes)
        assert model["intended_use"] == "manual_development" and not model["automatic_warnings_approved"]
        assert model["evaluation_status"] == "unverified" and not model["synthetic"]
        conversion = json.loads((root / "docs/model-conversion.json").read_text(encoding="utf-8"))
        assert hashlib.sha256(model_bytes).hexdigest() == conversion["converted_sha256"]
    else:
        assert "assets/model.json" not in names
    for name in names:
        if name.endswith(".dex"):
            content = packaged.read(name)
            assert b"Lph/smishguard/SoftwareTestApp;" not in content
            assert b"Lph/smishguard/SoftwareTestRunner;" not in content
filename = "SmishGuard-0.2.0-dev.apk" if args.variant == "development" else "SmishGuard-0.2.0-debug.apk"
target = output / filename
shutil.copyfile(apk, target)
# Only reviewed version-controlled files, never incidental files in source folders.
names = subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0')
files = [root/name for name in names if name and (root/name).is_file()]
for path in files:
    relative=path.relative_to(root)
    if (set(relative.parts)&{'build','.venv','__pycache__','data','runs','deliverables','.idea','.gradle'}
        or path.name in {'local.properties','model.json'}
        or path.suffix.lower() in {'.apk','.zip','.docx','.xlsx','.pem','.key','.jks','.keystore','.pkl'}
        or path.name.startswith('.env')):
        raise SystemExit('Unsafe tracked source archive member; review index before packaging')
archive = output / "SmishGuard-source.zip"
with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as z:
    for path in sorted(files):
        name = path.relative_to(root).as_posix()
        member = zipfile.ZipInfo(name)  # Stable timestamps for reproducible source ZIPs.
        member.compress_type = zipfile.ZIP_DEFLATED
        member.external_attr = (0o755 if name == 'gradlew' else 0o644) << 16
        z.writestr(member, subprocess.check_output(['git','show',':'+name],cwd=root))
(output / "SHA256SUMS.txt").write_text("".join(
    hashlib.sha256(p.read_bytes()).hexdigest() + "  " + p.name + "\n" for p in (target, archive)), encoding="utf-8")
print(f"Packaged APK and {len(files)} portable source files.")
(output/'SHARING-NOTICE.txt').write_text('Development APK contains a supplied experimental model. Local authorized testing only; model redistribution/privacy review unresolved. Source archive excludes model and private research data. No GitHub release is authorized by packaging.\n',encoding='utf-8')
