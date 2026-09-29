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


if __name__ == "__main__":
    main()
