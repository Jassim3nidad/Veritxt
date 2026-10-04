"""Private audit and frozen preparation of the 2026-10-04 supplied package."""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re
import zipfile
import numpy as np
from . import fair_compare as fair
from .data import template_groups, split_rows
from .mbert_experiment import redacted_case_view
from .preliminary_compare import PERSON, OBFUSCATED
from .preprocessing import normalize
from .review_packets import private_output
from .source_matching import SOURCES, parse_member
from .train import write_json

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT/'docs/expanded-comparison-protocol-20261005.md'
PLACEHOLDER = re.compile(r'<(?:REAL NAME|NAME|REDACTED|BLANK|n)>|\[name redacted\]|\(full name\)|\[my name\]', re.I)
ADDRESS = re.compile(r'\b(?:address|residing at|street|barangay|brgy\.?|unit|room)\s*[:#]?\s*\d',re.I)

def clean(text):
    return re.sub(r'\s+',' ',PLACEHOLDER.sub(' ',str(text))).strip(' ,')

def fingerprint(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def load(path):
    return json.loads(path.read_text(encoding='utf-8'))

def counts(rows,groups=None):
    y=[int(r['label']) for r in rows]
    result=dict(records=len(rows),ham=y.count(0),smishing=y.count(1))
    if groups is not None:
        result.update(groups=len(set(groups)),positive_groups=len({g for g,v in zip(groups,y) if v}),negative_groups=len({g for g,v in zip(groups,y) if not v}))
    return result

def prepare(package,snapshots,output):
    private_output(output)
    if output.exists():raise ValueError('Preserve existing experiment; use a fresh directory')
    output.mkdir(parents=True)
    rows=list(csv.DictReader((package/'smishguard_dataset.csv').open(encoding='utf-8-sig',newline='')))
    excluded=list(csv.DictReader((package/'smishguard_excluded.csv').open(encoding='utf-8-sig',newline='')))
    required={'id','text','label','category','language','source','source_category','sender','date','template_group','label_method','confidence','needs_review'}
    if set(rows[0])!=required:raise ValueError('Unexpected schema')
    source_indexes={}
    for name,spec in SOURCES.items():
        with zipfile.ZipFile(snapshots/(name+'.zip')) as z:data=z.read(spec['member'])
        if hashlib.sha256(data).hexdigest()!=spec['sha256']:raise ValueError('Pinned source changed')
        index=defaultdict(list)
        for i,row in enumerate(parse_member(data,spec['member'])):
            text=clean(row.get('text',''));index[text.lower()].append((i,text))
        source_indexes[name]=index
    exact=defaultdict(list);normalized=defaultdict(list);supplied=defaultdict(list)
    for r in rows:
        exact[clean(r['text']).lower()].append(r)
        normalized[normalize(redacted_case_view(r['text']))].append(r)
        supplied[r['template_group']].append(r)
    conflict_keys={k for k,v in normalized.items() if len({r['label'] for r in v})>1}
    # Audit the supplied rule definitions after source inspection; never execute I/O.
    if fair.digest(package/'build_dataset.py')!='1cd28600de4bb750cb195fc9de1faaf40e40bf2d132ee6bc1e5927fdf83a41dd':
        raise ValueError('Unreviewed builder bytes; inspect code before accepting another package')
    code=(package/'build_dataset.py').read_text(encoding='utf-8')
    definitions=code.split('# ---------------- load sources ----------------')[0].replace('import pandas as pd','')
    ns={};exec(compile(definitions,'<audited package pure definitions>','exec'),ns)
    scope_flags=[]
    for i,r in enumerate(excluded):
        text=r['text']
        if r['excluded_as']=='FRAUD' and (ns['CRED'].search(text) or (ns['BRAND'].search(text) and ns['bad_links'](text,True)) or (ns['THREAT'].search(text) and ns['bad_links'](text,True))):
            scope_flags.append(dict(excluded_row=i,content_sha256=fingerprint(text),reason='excluded job/loan with possible phishing signals; human scope adjudication pending'))
    audit=dict(included_records=len(rows),labels=dict(Counter(r['label'] for r in rows)),template_groups=len(supplied),flagged_records=sum(r['needs_review']=='True' for r in rows),
        excluded_records=len(excluded),excluded_labels=dict(Counter(r['excluded_as'] for r in excluded)),missing={k:sum(not r[k].strip() for r in rows) for k in required},
        duplicate_ids=len(rows)-len({r['id'] for r in rows}),duplicate_exact_text=sum(len(v)-1 for v in exact.values()),
        normalized_conflict_groups=len(conflict_keys),normalized_conflict_records=sum(len(normalized[k]) for k in conflict_keys),
        supplied_mixed_label_groups=sum(len({r['label'] for r in v})>1 for v in supplied.values()),
        supplied_template_key_mismatches=sum(ns['template_key'](r['text'])!=r['template_group'] for r in rows),
        source_counts={s:dict(Counter(r['label'] for r in rows if r['source']==s)) for s in sorted({r['source'] for r in rows})},
        confidence=dict(Counter(r['confidence'] for r in rows)),label_methods=dict(Counter(r['label_method'] for r in rows)),
        excluded_possible_phishing=len(scope_flags),raw_build_reproduced=False,raw_build_reason='ZIP contains outputs and builder but no raw sources; only CSV/source-snapshot validation performed',
        files={p.name:fair.digest(p) for p in package.iterdir() if p.is_file()})
    assert (len(rows),audit['labels'],len(supplied),audit['flagged_records'],len(excluded))==(3552,{'smishing':468,'ham':3084},2594,71,2272)
    if audit['duplicate_ids']:raise ValueError('Duplicate IDs')
    held=Counter();ledger=[];usable=[]
    for r in rows:
        reason=None;matched=None;view=None
        if r['source'].startswith('GitHub'):reason='github_permission_unresolved'
        elif r['source'].startswith('Team'):reason='team_origin_consent_use_unresolved'
        else:
            preferred='tagalog' if 'Tagalog-SMS' in r['source'] else 'marketing' if 'Chua' in r['source'] else 'bwandowando'
            hits=source_indexes[preferred].get(clean(r['text']).lower(),[])
            if not hits:reason='no_cleaned_exact_pinned_source_match'
            else:
                matched=dict(source=preferred,source_row=hits[0][0]);text=hits[0][1]
                if PERSON.search(text) or OBFUSCATED.search(text) or ADDRESS.search(text):reason='automated_privacy_hold'
                view=redacted_case_view(text)
                if normalize(view) in conflict_keys:reason='conflicting_redacted_labels'
                if not normalize(view) or len(view)>10000:reason='empty_or_overlong'
        record={**r,'original_sha256':fingerprint(r['text']),'cleaned_sha256':fingerprint(clean(r['text']).lower()),'source_match':matched,'hold_reason':reason,
            'human_label_review':'pending','human_privacy_review':'pending'}
        if reason:held[reason]+=1
        else:
            record['redacted_sha256']=fingerprint(view)
            usable.append(dict(id=r['id'],text=view,text_redacted=normalize(view),label=int(r['label']=='smishing'),template_group=r['template_group'],
                source=matched['source'],language=r['language'],category=r['category'],needs_review=r['needs_review'],content_sha256=record['original_sha256']))
        ledger.append(record)
    write_json(output/'private-intake-ledger.json',ledger);write_json(output/'scope-review.json',scope_flags)
    write_json(output/'audit.json',audit)
    write_json(output/'dataset.json',usable)
    print('Audit and source joins complete:',len(usable),'eligible;',dict(held),'held. Grouping begins.',flush=True)
    groups=np.asarray(template_groups(usable));parts=split_rows(usable,groups,'group',fair.SEED)
    support={p:counts([usable[i] for i in ids],groups[ids]) for p,ids in parts.items()}
    if any(support[p]['smishing']<20 or support[p]['positive_groups']<10 for p in ('validation','calibration','test')):
        write_json(output/'support-failure.json',support);raise ValueError('Support requires pretraining CV amendment')
    train_ids=parts['train'];folds=fair.training_folds(np.array([usable[i]['label'] for i in train_ids]),groups[train_ids])
    write_json(output/'splits.json',dict(partitions=parts,groups=groups.tolist(),inner_folds=[dict(train=a.tolist(),validation=b.tolist()) for a,b in folds]))
    write_json(output/'membership.json',{p:[dict(id=usable[i]['id'],group=int(groups[i]),content_sha256=usable[i]['content_sha256']) for i in ids] for p,ids in parts.items()})
    write_json(output/'case-view.json',[dict(id=r['id'],text=r['text'],label=r['label']) for r in usable])
    write_json(output/'preparation.json',dict(audit=audit,held=dict(held),retained=counts(usable,groups),partition_support=support,source_credits=SOURCES,
        dataset_sha256=fair.digest(output/'dataset.json'),split_sha256=fair.digest(output/'splits.json'),case_view_sha256=fair.digest(output/'case-view.json'),
        protocol_sha256=fair.digest(PROTOCOL),preparation_code_sha256=fair.digest(Path(__file__)),seed=fair.SEED,
        merged_supplied_groups=len({r['template_group'] for r in usable})-len(set(groups)),group_overlap_pairs={a+'-'+b:len(set(groups[parts[a]])&set(groups[parts[b]])) for a in parts for b in parts if a<b},
        review_status='source/rule labels and automated redaction only; all independent human reviews pending',scope='supplied all-SMS-phishing expansion; adviser approval not independently verified'))
    print('Frozen support:',support,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('package',type=Path);p.add_argument('snapshots',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();prepare(a.package,a.snapshots,a.output)
