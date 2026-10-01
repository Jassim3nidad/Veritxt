"""Real Gradle gates in an isolated project; never modifies working private models."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    env = os.environ.copy()
    env["JAVA_TOOL_OPTIONS"] = (env.get("JAVA_TOOL_OPTIONS", "") +
        " -Djdk.net.unixdomain.tmpdir=C:/sg-nonexistent-socket-dir").strip()
    with tempfile.TemporaryDirectory(prefix="smishguard-comparison-guards-") as directory:
        project = Path(directory)
        for name in ("settings.gradle.kts", "build.gradle.kts", "gradle.properties", "local.properties",
                     "android/app/build.gradle.kts", "android/app/src/main/AndroidManifest.xml"):
            target = project / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        def reject(name, expected):
            task = f":app:verify{name[0].upper() + name[1:]}Model"
            result = subprocess.run([str(ROOT / "gradlew.bat"), "-p", str(project), task, "--console=plain"],
                                    cwd=ROOT, env=env, capture_output=True, text=True, timeout=240)
            assert result.returncode != 0 and expected in result.stdout + result.stderr, f"Guard failed: {name} {expected}"
        for name in ("lr", "nb", "svm"):
            reject(name, "requires a privately reviewed model")
            print(f"PASS {name}: missing model rejected", flush=True)
            assets = project / f"android/app/src/{name}/assets"
            assets.mkdir(parents=True)
            model = assets / "model.json"
            model.write_text("{}")
            review = assets / "review.properties"
            prefix = f"algorithm={name}\nmodelVersion=software-guard-fixture\nmanualReview=accepted-experimental\n"
            review.write_text(prefix + "sha256=wrong\n")
            reject(name, "Model changed after review")
            print(f"PASS {name}: changed model rejected", flush=True)
            model.write_text(json.dumps(dict(schema_version=1, algorithm="wrong", synthetic=False,
                                            calibration_evaluated=False, calibration={"method": "sigmoid"})))
            review.write_text(prefix + f"sha256={hashlib.sha256(model.read_bytes()).hexdigest()}\n")
            reject(name, "Export algorithm does not match variant")
            print(f"PASS {name}: wrong algorithm rejected", flush=True)

        # Isolated software-only review fixtures, never an actual model acceptance.
        reject("lrCandidate", "LR candidate blocked")
        assets = project / "android/app/src/lrCandidate/assets"
        assets.mkdir(parents=True)
        model = assets / "model.json"
        model.write_text("{}")
        review = assets / "review.properties"
        review.write_text("algorithm=lr\ncontentReview=pending\n")
        reject("lrCandidate", "actual model-content evidence reference")
        prefix = "algorithm=lr\ncontentReview=documented\ncontentReviewReference=SOFTWARE_ONLY\nmodelVersion=software-guard\nsourceSha256=" + "0" * 64 + "\n"
        review.write_text(prefix + "sha256=wrong\n")
        reject("lrCandidate", "Candidate model changed")
        review.write_text(prefix + "sha256=" + hashlib.sha256(model.read_bytes()).hexdigest() + "\n")
        reject("lrCandidate", "Wrong candidate schema or policy")
        print("PASS lrCandidate: missing, pending, changed and invalid models rejected (4)", flush=True)

        # Again, synthetic isolated fixtures only: no human acceptance is generated.
        reject("lrCalibrated4", "requires private audited assets")
        assets = project / "android/app/src/lrCalibrated4/assets"
        assets.mkdir(parents=True)
        model = assets / "model.json"; review = assets / "review.properties"
        source_hash = "d91f010a004e1fcfef6e4567389007cb81d16e1f6d0f258c263483b2b60d0d77"
        fixture = dict(schema_version=4, algorithm="lr", model_version="lr-calibrated-4",
            calibration_encoding="folded_into_parameters", calibration_status="fitted_unvalidated",
            evaluation_status="unverified", threshold=.5, threshold_comparison="strict_greater",
            synthetic=False, automatic_warnings_approved=False,
            provenance=dict(source_sha256=source_hash), vocabulary=["software"])
        prefix = ("algorithm=lr\nmodelVersion=lr-calibrated-4\nreviewKind=automated-pattern-screen\n"
                  "humanReview=not_recorded\nreviewReference=lr-calibrated-4-audit-20261001\nsourceSha256=" + source_hash + "\n")
        def write_folded(value):
            model.write_text(json.dumps(value))
            review.write_text(prefix + "sha256=" + hashlib.sha256(model.read_bytes()).hexdigest() + "\n")
        write_folded({**fixture, "calibration": dict(a=2, b=0)})
        reject("lrCalibrated4", "schema/calibration policy mismatch")
        write_folded({**fixture, "vocabulary": ["ref" + "1" * 5]})
        reject("lrCalibrated4", "Identifier-pattern content check failed")
        write_folded({**fixture, "provenance": dict(source_sha256="0" * 64)})
        reject("lrCalibrated4", "Wrong folded candidate source")
        write_folded(fixture)
        model.write_text("{}")
        reject("lrCalibrated4", "Folded candidate identity mismatch")
        print("PASS lrCalibrated4: missing, double calibration, identifiers, wrong source and changed assets rejected (5)", flush=True)


if __name__ == "__main__":
    main()
