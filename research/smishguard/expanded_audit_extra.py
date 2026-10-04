"""Additional private exact-content and historical-label evidence, without predictions."""
import argparse
from collections import Counter, defaultdict
import csv
from pathlib import Path
import zipfile
from .expanded_prepare import load, clean
from .source_matching import SOURCES, parse_member
from .train import write_json

def run(output):
    intake=load(output/'private-intake-ledger.json');rows=load(output/'dataset.json');ids={r['id'] for r in rows}
    root=Path('research/data');prior=root/'comparison-20261001/experiment-v1'
    old=load(prior/'dataset.json');parts=load(prior/'splits.json')['partitions'];sources={}
    for name in ('tagalog','marketing'):
        spec=SOURCES[name]
        with zipfile.ZipFile(root/'source-evidence-pinned'/(name+'.zip')) as z:sources[name]=parse_member(z.read(spec['member']),spec['member'])
    index=defaultdict(list)
    for part,indices in parts.items():
        for i in indices:
            r=old[i];source=next(iter(r['source_matches']));number=r['source_matches'][source]['candidate_rows'][0]-2
            index[clean(sources[source][number]['text']).lower()].append((part,int(r['label'])))
    ledger=[]
    for r in intake:
        matches=index.get(clean(r['text']).lower(),[])
        ledger.append(dict(id=r['id'],eligible=r['id'] in ids,previous_partitions=sorted({p for p,_ in matches}),
            old_label_conflicts=any(label!=int(r['label']=='smishing') for _,label in matches)))
    write_json(output/'original-exact-exposure-ledger.json',ledger)
    selected=[r for r in intake if r['id'] in ids]
    summary=dict(exact_definition='Case-insensitive whitespace/placeholder-cleaned source text; URLs and digits retained for equality; identifiers never used for correspondence',
        previous_exact={p:sum(r['eligible'] and p in r['previous_partitions'] for r in ledger) for p in parts},
        historical_label_changes=sum(r['eligible'] and r['old_label_conflicts'] for r in ledger),
        eligible_source_counts={s:dict(Counter(r['label'] for r in selected if r['source_match']['source']==s)) for s in SOURCES},
        eligible_pending_package_flags=sum(r['needs_review']=='True' for r in selected),
        excluded_duplicate_overlap=0)
    package=root/'expanded-20261005/original/smishguard_dataset_2026-10-04'
    excluded=list(csv.DictReader((package/'smishguard_excluded.csv').open(encoding='utf-8-sig')))
    kept={clean(r['text']).lower() for r in intake}
    summary['excluded_duplicate_overlap']=sum(clean(r['text']).lower() in kept for r in excluded)
    write_json(output/'extra-audit.json',summary);print(summary,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);run(p.parse_args().output)
