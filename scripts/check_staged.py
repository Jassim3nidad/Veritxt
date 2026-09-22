"""Read-only public-sharing checks on the Git index; never prints secret/message values."""
from pathlib import Path
import csv
import json
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
    raw = Path('research/data/package-audit/original/smishguard_dataset.csv')
    messages = []
    if raw.exists():
        with raw.open(encoding='utf-8-sig',newline='') as f:
            messages = [r['message_text'].encode('utf-8') for r in csv.DictReader(f) if len(r['message_text']) >= 30]
    private_model = Path('android/app/src/development/assets/model.json')
    numeric_terms = []
    if private_model.exists():
        model = json.loads(private_model.read_text(encoding='utf-8'))
        numeric_terms = [t.encode('utf-8') for t in model['vocabulary'] if re.search(r'\d{7,}', t)]
    findings = []
    for name in names:
        path = Path(name)
        if (name.startswith(('research/data/', 'research/runs/', 'deliverables/'))
            or any(p in {'.venv','.idea','.gradle','build','__pycache__'} for p in path.parts)
            or path.suffix.lower() in {'.apk','.zip','.docx','.jpg','.jpeg','.xlsx','.pkl','.jks','.keystore','.pem','.key'}
            or (path.name.startswith('.env') and path.name != '.env.example')
            or name.endswith('/assets/model.json') or path.name == 'local.properties'):
            findings.append((name, 'private/generated path'))
            continue
        data = git('show', ':'+name)
        if any(re.search(pattern, data) for pattern in secret_patterns): findings.append((name,'credential pattern'))
        if any(message in data for message in messages): findings.append((name,'raw message exact match'))
        if any(term in data for term in numeric_terms): findings.append((name,'unreviewed learned numeric term'))
    if findings:
        for name, reason in findings: print(f'{name}: {reason}')
        raise SystemExit('Staged sharing review failed; values intentionally withheld')
    print(f'Passed: {len(names)} staged files; private/generated paths, credential patterns and available raw-message/model-token matches checked.')
    print('Bounded checks complement manual diff review; they are not a complete privacy detector.')


if __name__ == '__main__': main()
