"""Package portable source and an already-built development/debug APK. Does not build or sign."""
from pathlib import Path
import hashlib
import shutil
import zipfile
import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument("--variant", choices=["debug", "development"], default="development")
args = parser.parse_args()

root = Path(__file__).resolve().parents[1]
output = root / "deliverables"
output.mkdir(exist_ok=True)
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
top = ["README.md", ".gitignore", ".gitattributes", "settings.gradle.kts", "build.gradle.kts", "gradle.properties", "gradlew", "gradlew.bat"]
files = [root / name for name in top]
for name in ["android", "research", "docs", "backend", "scripts", "gradle"]:
    files.extend(p for p in (root/name).rglob("*") if p.is_file()
                 and not {"build", ".venv", "__pycache__", "data", "runs"}.intersection(p.relative_to(root/name).parts)
                 and p.relative_to(root).as_posix() not in {
                     "android/app/src/development/assets/model.json", "android/app/src/main/assets/model.json"})
archive = output / "SmishGuard-source.zip"
with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as z:
    for path in sorted(files):
        z.write(path, path.relative_to(root).as_posix())
(output / "SHA256SUMS.txt").write_text("".join(
    hashlib.sha256(p.read_bytes()).hexdigest() + "  " + p.name + "\n" for p in (target, archive)), encoding="utf-8")
print(f"Packaged APK and {len(files)} portable source files.")
