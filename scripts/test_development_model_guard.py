"""Exercise the real Gradle packaging gate in an isolated model-free project.

Never renames or changes the private asset in the working checkout.
Requires the project's configured Android SDK and Gradle dependencies.
"""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    env = os.environ.copy()
    env['JAVA_TOOL_OPTIONS'] = (env.get('JAVA_TOOL_OPTIONS', '') +
        ' -Djdk.net.unixdomain.tmpdir=C:/sg-nonexistent-socket-dir').strip()
    with tempfile.TemporaryDirectory(prefix='smishguard-model-guard-') as directory:
        project = Path(directory)
        for name in ('settings.gradle.kts', 'build.gradle.kts', 'gradle.properties',
                     'local.properties', 'android/app/build.gradle.kts',
                     'android/app/src/main/AndroidManifest.xml'):
            source = ROOT / name
            if source.exists():
                target = project / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)

        def run(task, expected=None):
            wrapper = ROOT / ('gradlew.bat' if os.name == 'nt' else 'gradlew')
            result = subprocess.run([str(wrapper), '-p', str(project), task,
                                     '--console=plain'], env=env, cwd=ROOT,
                                    capture_output=True, text=True, timeout=240)
            output = result.stdout + result.stderr
            if expected:
                assert result.returncode != 0 and expected in output, 'Expected model guard rejection'
                assert ':app:verifyDevelopmentModel FAILED' in output
            else:
                assert result.returncode == 0, 'Model-free debug prebuild failed'

        run(':app:assembleDevelopment', 'Development model missing:')
        print('PASS: development assembly rejects a missing asset')
        model = project / 'android/app/src/development/assets/model.json'
        model.parent.mkdir(parents=True, exist_ok=True)
        model.write_text('{}', encoding='utf-8')
        run(':app:mergeDevelopmentAssets', 'Development model differs')
        print('PASS: asset merge rejects an unapproved substitute')
        model.unlink()
        run(':app:preDebugBuild')
        print('PASS: model-free debug prebuild remains supported')


if __name__ == '__main__':
    main()
