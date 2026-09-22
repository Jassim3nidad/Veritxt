"""Freeze private anonymous membership and publish only aggregate audit supplements."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
import numpy as np
from .review_packets import private_output


def freeze(source, ledger, output, summary):
    private_output(output)
    with source.open(encoding='utf-8-sig',newline='') as stream: rows=list(csv.DictReader(stream))
    with ledger.open(encoding='utf-8-sig',newline='') as stream: group_rows=list(csv.DictReader(stream))
    groups={r['id']:r['template_group'] for r in group_rows}
    excluded={r['id'] for r in group_rows if r.get('explicit_other_sector','').lower()=='true'}
    if len(groups)!=len(group_rows): raise ValueError('Duplicate audit ledger IDs')
    if len({r['id'] for r in rows})!=len(rows) or set(groups)!={r['id'] for r in rows}:
        raise ValueError('Source and reviewed audit ledger IDs must match exactly')
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    records=[]
    for r in rows:
        records.append(dict(anonymous_id=hashlib.sha256((digest+':'+r['id']).encode()).hexdigest(),
            record_sha256=hashlib.sha256(json.dumps(r,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),
            group_id=groups[r['id']],source_group=hashlib.sha256(r['source'].encode()).hexdigest(),
            status='excluded_primary_nonfinancial' if r['id'] in excluded else 'held_pending_permission_redaction_independent_labels',
            proposed_role='supplementary' if 'uci sms spam' in r['source'].lower() else 'unverified'))
    manifest=dict(schema_version=1,dataset_sha256=digest,group_ledger_sha256=hashlib.sha256(ledger.read_bytes()).hexdigest(),
        status='Frozen supplied bytes and heuristic groups; not an eligible training dataset',records=records)
    with output.open('x',encoding='utf-8') as stream: json.dump(manifest,stream,indent=2)
    lengths=[len(r['message_text']) for r in rows]
    patterns=dict(url=r'https?://|www\.',phone_like=r'\d(?:[ ()+.-]*\d){6,}',
        financial_keyword=r'\b(?:bank|account|wallet|payment|bayad|pera|loan|otp|gcash|maya|bpi|bdo|remittance)\b')
    report=dict(dataset_sha256=digest,manifest_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),rows=len(rows),
        message_length_characters={k:float(v) for k,v in zip(['min','p25','median','p75','p95','max'],np.percentile(lengths,[0,25,50,75,95,100]))},
        mean_length_characters=float(np.mean(lengths)),indicators={k:sum(bool(re.search(p,r['message_text'],re.I)) for r in rows) for k,p in patterns.items()},
        indicator_patterns=patterns,note='Overlapping lexical indicators, not verified phone numbers, financial scope or privacy clearance. Language counts remain supplied labels, not independent language identification.',
        sources=dict(Counter(r['source'] for r in rows)),eligibility='No records cleared by this operation; all held for review. See dataset-audit.json for exclusions and proposed roles.')
    with summary.open('x',encoding='utf-8') as stream: json.dump(report,stream,indent=2)
    return report


def main():
    p=argparse.ArgumentParser()
    p.add_argument('source',type=Path);p.add_argument('ledger',type=Path)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--summary',type=Path,required=True)
    a=p.parse_args();freeze(a.source,a.ledger,a.output,a.summary)
    print('Private manifest and aggregate summary saved; no eligibility inferred.')


if __name__=='__main__':main()
