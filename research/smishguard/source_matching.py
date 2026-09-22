"""Reproduce conservative content-overlap evidence; never infer licensing or labels."""
import argparse
from collections import defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from .review_packets import private_output

SOURCES = {
    'tagalog': dict(ref='onzero0/tagalog-sms', version=1, member='tagalog-sms.xlsx',
        sha256='7757fb9cf70b9c1e0101e384886706da52110f6c17aeafef10a104e38fdfc0a7',
        author='ZERO (onzero0)', license='CC0 1.0'),
    'marketing': dict(ref='scottleechua/ph-spam-marketing-sms-w-timestamps', version=15, member='text-messages.csv',
        sha256='a3724dca065ee8ed23eb18fb6382657e2559f2b0c0364aaf9c14277af1974e32',
        author='Scott Lee Chua', license='CC BY 4.0'),
    'bwandowando': dict(ref='bwandowando/philippine-spam-sms-messages', version=49, member='SPAM_SMS.csv',
        sha256='3012700e9f774f87b6922cd88e41155b41d0bf9923f04af456683f2859941d5f',
        author='BwandoWando', license='CC BY-NC-SA 4.0'),
}


def parse_member(data, name):
    if name.endswith('.csv'):
        return list(csv.DictReader(io.StringIO(data.decode('utf-8-sig'))))
    ns = {'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        shared = [''.join(t.text or '' for t in si.findall('.//s:t', ns))
                  for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si', ns)] if 'xl/sharedStrings.xml' in z.namelist() else []
        values = []
        for row in ET.fromstring(z.read('xl/worksheets/sheet1.xml')).findall('.//s:row', ns):
            cells = {}
            for cell in row.findall('s:c', ns):
                v = cell.find('s:v', ns)
                text = v.text if v is not None else ''.join(t.text or '' for t in cell.findall('.//s:t', ns))
                cells[re.sub(r'\d', '', cell.get('r'))] = shared[int(text)] if cell.get('t') == 's' else text
            values.append(cells)
    header = values[0]
    return [{header[k]:v for k,v in row.items() if k in header} for row in values[1:]]


def indexes(rows):
    exact, whitespace = defaultdict(list), defaultdict(list)
    for i, row in enumerate(rows, start=2):
        text = str(row.get('text', ''))
        if text.strip():
            exact[text].append(i); whitespace[' '.join(text.split())].append(i)
    return exact, whitespace


def match(text, index):
    exact, whitespace = index
    if text in exact: return dict(kind='exact', candidate_rows=exact[text])
    key = ' '.join(text.split())
    if key in whitespace: return dict(kind='whitespace_only', candidate_rows=whitespace[key])
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('packet', type=Path)
    parser.add_argument('--downloads', type=Path, default=Path('research/data/source-evidence'))
    parser.add_argument('--download', action='store_true')
    parser.add_argument('--report', type=Path, default=Path('docs/source-match-summary.json'))
    args = parser.parse_args(); private_output(args.downloads); private_output(args.packet)
    args.downloads.mkdir(parents=True, exist_ok=True)
    maps = json.loads((args.packet/'coordinator/mapping.json').read_text(encoding='utf-8'))
    catalog, indices = {}, {}
    for name, spec in SOURCES.items():
        url = f"https://www.kaggle.com/api/v1/datasets/download/{spec['ref']}?datasetVersionNumber={spec['version']}"
        path = args.downloads/(name+'.zip')
        if args.download and not path.exists():
            with urllib.request.urlopen(url, timeout=60) as response: payload = response.read()
            path.write_bytes(payload)
        with zipfile.ZipFile(path) as z: data = z.read(spec['member'])
        if hashlib.sha256(data).hexdigest() != spec['sha256']:
            raise ValueError(f'{name} content differs from inspected snapshot; review version before matching')
        rows = parse_member(data, spec['member']); indices[name] = indexes(rows)
        catalog[name] = dict(spec, rows=len(rows), download_url=url,
            page_url='https://www.kaggle.com/datasets/'+spec['ref'],
            archive_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    groups = {}; ledger = []
    for item in maps:
        row = item['original']; source = row['source']
        group = groups.setdefault(source, dict(rows=0, any_match=0, multiple_candidates=0,
            candidates={name:dict(exact=0, whitespace_only=0) for name in SOURCES}))
        group['rows'] += 1; hits = {}
        for name, index in indices.items():
            result = match(row['message_text'], index)
            if result:
                hits[name] = result; group['candidates'][name][result['kind']] += 1
        group['any_match'] += bool(hits); group['multiple_candidates'] += len(hits) > 1
        ledger.append(dict(id=item['anonymous_id'], matches=hits,
            status='content_overlap_only_not_confirmed_acquisition_or_license'))
    (args.packet/'coordinator/source-matches.json').write_text(json.dumps(ledger), encoding='utf-8')
    report = dict(snapshots=catalog, by_supplied_source=groups,
        method='Exact Unicode text first, then whitespace collapse only; no case/URL/number/template normalization',
        limits='Content overlap is not acquisition-chain proof, individual license assignment, label validation or receipt-time verification. No raw examples in public report.',
        uci='Official page and CC BY 4.0 observed; direct official ZIP download failed TLS validation; no row match claimed')
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print('Aggregate source matches saved; row ledger private; no eligibility or labels inferred.')


if __name__ == '__main__': main()
