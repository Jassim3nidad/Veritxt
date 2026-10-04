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
    parser.add_argument("algorithm", choices=["lr", "nb", "svm", "lrCalibrated4"])
    parser.add_argument("--output-dir", type=Path, help="New private directory beneath deliverables; preserves prior APKs")
    args = parser.parse_args()
    name = args.algorithm
    folded = name == "lrCalibrated4"
    algorithm = "lr" if folded else name
    package = "ph.smishguard.lr.calibrated4" if folded else f"ph.smishguard.{name}"
    source = ROOT / f"android/app/build/outputs/apk/{name}/app-{name}.apk"
    asset = ROOT / f"android/app/src/{name}/assets/model.json"
    review_path = asset.with_name("review.properties")
    review = dict(line.split("=", 1) for line in review_path.read_text(encoding="utf-8").splitlines() if line and not line.startswith("#"))
    model_hash = hashlib.sha256(asset.read_bytes()).hexdigest()
    assert review["algorithm"] == algorithm and review["sha256"] == model_hash
    if folded:
        assert review["reviewKind"] == "automated-pattern-screen" and review["humanReview"] == "not_recorded"
        content = json.loads(asset.read_text(encoding="utf-8"))
        assert content["schema_version"] == 4 and content["calibration_encoding"] == "folded_into_parameters"
        assert "calibration" not in content and review["modelVersion"] == "lr-calibrated-4"
    elif review.get("reviewReference") in ("preliminary-comparison-20261001", "expanded-comparison-20261005"):
        assert review["reviewKind"] == "automated-pattern-screen" and review["humanReview"] == "not_recorded"
        content = json.loads(asset.read_text(encoding="utf-8"))
        assert content["algorithm"] == algorithm and content["schema_version"] == 1
        assert content["model_version"] == review["modelVersion"] and content["evaluation_status"] == "preliminary_retrospective"
        assert content["protocol_sha256"] == review["protocolSha256"]
        protocol = ('expanded-comparison-protocol-20261005.md' if review['reviewReference']=='expanded-comparison-20261005'
                    else 'preliminary-comparison-protocol-20261001.md')
        assert content["protocol_sha256"] == hashlib.sha256((ROOT/'docs'/protocol).read_bytes()).hexdigest()
    else:
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
    assert f"package: name='{package}'" in badging
    assert "sdkVersion:'26'" in badging
    permissions = re.findall(r"uses-permission: name='([^']+)'", badging)
    assert "android.permission.INTERNET" not in permissions
    assert set(permissions) <= {"android.permission.RECEIVE_SMS", "android.permission.POST_NOTIFICATIONS",
                                f"{package}.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"}
    subprocess.run([str(sdk / "apksigner.bat"), "verify", "--verbose", str(source)], check=True, capture_output=True)
    target = ROOT / ("deliverables/lr-calibrated-4-20261001" if folded else "deliverables/algorithm-comparison-20260929")
    if args.output_dir:
        target = args.output_dir.resolve()
        assert target.is_relative_to((ROOT/'deliverables').resolve()), "APK destination must stay private"
    target.mkdir(parents=True, exist_ok=True)
    output = target / (f"SmishGuard-{version}-experimental-debug.apk" if folded else
                       f"SmishGuard-{name}-{version}-experimental-debug.apk")
    if output.exists() and output.read_bytes() != source.read_bytes():
        raise ValueError("Preserve existing candidate deliverable; choose a new versioned destination")
    shutil.copyfile(source, output)
    record = dict(filename=output.name, algorithm=algorithm, model_version=version,
                  sha256=hashlib.sha256(output.read_bytes()).hexdigest(), apk_bytes=output.stat().st_size,
                  model_sha256=model_hash, model_bytes=asset.stat().st_size, minimum_android="8.0 / API 26",
                  application_id=package, model_included=True, experimental=True,
                  checks="APK assets, model/review hashes, package ID, min SDK, permissions and APK signature passed",
                  research_status=("historical artifact; not a newly trained fair-comparison model; no thesis accuracy claim"
                      if json.loads(asset.read_text(encoding="utf-8"))["schema_version"] == 2 else
                      "research metrics and review evidence must be supplied separately; build checks do not establish accuracy"))
    (target / f"{name}-apk-manifest.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
