"""Read only reviewed aggregate evidence; optionally recheck the named shareable ZIP.

Never extracts, imports supplied code, opens message files outside the ZIP, or
accepts a private archive. Diagnostics contain counts and status, never values.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'research'))
from smishguard.candidate_evidence import review  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path)
    args = parser.parse_args()
    directory = ROOT/'research/candidate_review'
    manifest = json.loads((directory/'archive_review.json').read_text(encoding='utf-8'))
    for record in manifest['files']:
        if record['decision'] == 'accepted unchanged':
            data = (directory/Path(record['member']).name).read_bytes()
            if hashlib.sha256(data).hexdigest() != record['sha256']:
                raise ValueError('Accepted aggregate hash changed')
    result = review(directory)
    saved = json.loads((directory/'aggregate_check.json').read_text(encoding='utf-8'))
    if json.loads(json.dumps(result)) != saved:
        raise ValueError('Saved arithmetic report differs from recomputation')
    print(f"Aggregate checks passed: {result['metric_rows']} metric rows, {result['reliability_rows']} reliability rows")
    if args.archive is None:
        print('Archive recheck not requested; no archive opened')
        return
    # Check the name and link target before opening any archive bytes.
    if args.archive.name != 'smishguard_repo_update.zip' or args.archive.is_symlink():
        raise ValueError('Only the named shareable archive is allowed')
    path = args.archive.resolve(strict=True)
    if path.name != 'smishguard_repo_update.zip' or path.stat().st_size > 2_000_000:
        raise ValueError('Archive path or size rejected')
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest['archive_sha256']:
        raise ValueError('Archive differs from reviewed bytes; manual review required')
    mobile = rb'(?<![\w.])(?:\+?63|0)[ -]?9(?:[ -]?\d){9}(?!\d)'
    credentials = rb'gh[pousr]_[A-Za-z0-9]{30,}|-----BEGIN .*PRIVATE KEY|AKIA[A-Z0-9]{16}'
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        expected = {'smishguard_repo_update/'+r['member']: r for r in manifest['files']}
        if len(infos) != len(expected) or {i.filename for i in infos} != set(expected):
            raise ValueError('Archive membership differs')
        parsed = 0
        for info in infos:
            name = PurePosixPath(info.filename)
            if (name.is_absolute() or '..' in name.parts or '\\' in info.filename
                    or ':' in info.filename or (info.external_attr >> 16) & 0o170000 == 0o120000
                    or info.flag_bits & 1 or info.file_size > 100_000):
                raise ValueError('Unsafe archive member')
            data = archive.read(info)  # CRC verified by zipfile; no extraction.
            record = expected[info.filename]
            if len(data) != record['size'] or hashlib.sha256(data).hexdigest() != record['sha256']:
                raise ValueError('Member differs from reviewed bytes')
            if b'\0' in data:
                raise ValueError('Unexpected binary member')
            source = data.decode('utf-8-sig')
            if len(re.findall(mobile, data)) != record['mobile_pattern_count'] or re.search(credentials, data):
                raise ValueError('Privacy signal differs from review')
            if name.suffix == '.py':
                ast.parse(source); parsed += 1
        if parsed != manifest['python_syntax_passed']:
            raise ValueError('Syntax count differs')
    print(f'Archive checks passed: {len(infos)} members, {parsed} syntax parses; no supplied code executed')
    print('Message-bearing members remain excluded; pattern checks do not grant publication permission')


if __name__ == '__main__':
    main()
