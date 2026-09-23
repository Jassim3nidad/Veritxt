"""Read-only public-sharing checks on the Git index; never prints secret/message values."""
from pathlib import Path
import re
import subprocess


def git(*args):
    return subprocess.run(['git', *args], check=True, capture_output=True).stdout


def main():
    names = git('diff', '--cached', '--name-only', '--diff-filter=ACMR', '-z').decode().split('\0')
    names = [n for n in names if n]
    secret_patterns = [rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
                       rb'gh[pousr]_[A-Za-z0-9]{30,}', rb'github_pat_[A-Za-z0-9_]{40,}',
                       rb'AKIA[A-Z0-9]{16}']
    # Inspect only index bytes. Do not open private datasets/models to build a scanner.
    mobile_pattern = rb'(?<![\w.])(?:\+?63|0)[ -]?9(?:[ -]?\d){9}(?!\d)'
    findings = []
    for name in names:
        path = Path(name)
        if (name.startswith(('research/data/', 'research/runs/', 'deliverables/'))
            or any(p in {'.venv','.idea','.gradle','build','__pycache__'} for p in path.parts)
            or path.suffix.lower() in {'.apk','.zip','.docx','.jpg','.jpeg','.xlsx','.pkl','.joblib','.jks','.keystore','.pem','.key','.db','.sqlite','.sqlite3'}
            or path.name in {'smishguard_dataset.csv','model_export_final.json','model_export_v2.json'}
            or path.name.endswith(('.db-journal', '.db-wal', '.db-shm'))
            or (path.name.startswith('.env') and path.name != '.env.example')
            or name.endswith('/assets/model.json') or path.name == 'local.properties'):
            findings.append((name, 'private/generated path'))
            continue
        data = git('show', ':'+name)
        if any(re.search(pattern, data) for pattern in secret_patterns): findings.append((name,'credential pattern'))
        if re.search(mobile_pattern, data): findings.append((name,'mobile-number-like literal'))
    if findings:
        for name, reason in findings: print(f'{name}: {reason}')
        raise SystemExit('Staged sharing review failed; values intentionally withheld')
    print(f'Passed: {len(names)} staged files; private/generated paths, credential patterns and mobile-number-like literals checked without reading private artifacts.')
    print('Bounded checks complement manual diff review; they are not a complete privacy detector.')


if __name__ == '__main__': main()
