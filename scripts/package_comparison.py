"""Inspect and privately package an already-built reviewed comparison APK."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("algorithm", choices=["lr", "nb", "svm"])
    args = parser.parse_args()
    name = args.algorithm
    source = ROOT / f"android/app/build/outputs/apk/{name}/app-{name}.apk"
    asset = ROOT / f"android/app/src/{name}/assets/model.json"
    review_path = asset.with_name("review.properties")
    review = dict(line.split("=", 1) for line in review_path.read_text(encoding="utf-8").splitlines() if line and not line.startswith("#"))
    model_hash = hashlib.sha256(asset.read_bytes()).hexdigest()
    assert review["algorithm"] == name and review["sha256"] == model_hash
    assert review["manualReview"] == "accepted-experimental"
    version = review["modelVersion"]
    assert re.fullmatch(r"[A-Za-z0-9._-]+", version), "Unsafe model version filename"
    with zipfile.ZipFile(source) as archive:
        assets = sorted(path for path in archive.namelist() if path.startswith("assets/"))
        assert assets == ["assets/model.json", "assets/review.properties"], "Unexpected bundled assets"
        assert hashlib.sha256(archive.read("assets/model.json")).hexdigest() == model_hash
        assert archive.read("assets/review.properties") == review_path.read_bytes()
        assert not any(path.endswith((".csv", ".pkl", ".joblib")) or "/software/" in path for path in archive.namelist())
    sdk = Path(os.environ["LOCALAPPDATA"]) / "Android/Sdk/build-tools/35.0.0"
    badging = subprocess.check_output([str(sdk / "aapt.exe"), "dump", "badging", str(source)], text=True)
    assert f"package: name='ph.smishguard.{name}'" in badging
    assert "sdkVersion:'26'" in badging
    permissions = re.findall(r"uses-permission: name='([^']+)'", badging)
    assert "android.permission.INTERNET" not in permissions
    assert set(permissions) <= {"android.permission.RECEIVE_SMS", "android.permission.POST_NOTIFICATIONS",
                                f"ph.smishguard.{name}.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"}
    subprocess.run([str(sdk / "apksigner.bat"), "verify", "--verbose", str(source)], check=True, capture_output=True)
    target = ROOT / "deliverables/algorithm-comparison-20260929"
    target.mkdir(parents=True, exist_ok=True)
    output = target / f"SmishGuard-{name}-{version}-experimental-debug.apk"
    shutil.copyfile(source, output)
    record = dict(filename=output.name, algorithm=name, model_version=version,
                  sha256=hashlib.sha256(output.read_bytes()).hexdigest(), apk_bytes=output.stat().st_size,
                  model_sha256=model_hash, model_bytes=asset.stat().st_size, minimum_android="8.0 / API 26",
                  application_id=f"ph.smishguard.{name}", model_included=True, experimental=True,
                  checks="APK assets, model/review hashes, package ID, min SDK, permissions and APK signature passed",
                  research_status=("historical artifact; not a newly trained fair-comparison model; no thesis accuracy claim"
                      if json.loads(asset.read_text(encoding="utf-8"))["schema_version"] == 2 else
                      "research metrics and review evidence must be supplied separately; build checks do not establish accuracy"))
    (target / f"{name}-apk-manifest.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
