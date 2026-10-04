"""Private historical exact/near-copy exposure ledger, independent of model scores."""
import argparse
from collections import defaultdict
import csv
from difflib import SequenceMatcher
from pathlib import Path
import numpy as np
from .expanded_prepare import load, clean
from .preprocessing import normalize
from .mbert_experiment import redacted_case_view
from .train import write_json
from . import fair_compare as fair

def audit(output):
    rows=load(output/'dataset.json');root=Path('research/data')
    old=root/'comparison-20261001/experiment-v1';oldrows=load(old/'dataset.json');splits=load(old/'splits.json')['partitions']
    history=defaultdict(set);original=defaultdict(set);files={}
    for part,ids in splits.items():
        for i in ids:history[oldrows[i]['text_redacted']].add('previous_'+part)
    paths=[root/'supplied-original/smishguard_dataset.csv',
        root/'mark-complete-20260929/extracted/SMISHGUARD/3_training/smishguard_dataset_v2_2521rows.csv',
        root/'mark-complete-20260929/extracted/SMISHGUARD/2_backend_dashboard/data/smishguard_dataset_v2.csv',
        root/'comparison-20261001/extracted/smishguard_PRIVATE_data/data/sources/smishguard_dataset_v2_2521rows.csv',
        root/'mark-update-20261001/extracted/smishguard_repo_update/training/fresh_test_messages.csv',
        root/'mark-update-20261001/extracted/smishguard_repo_update/training/fresh_test_messages_v2.csv']
    for path in paths:
        if not path.exists():continue
        files[str(path.relative_to(root))]=fair.digest(path)
        for r in csv.DictReader(path.open(encoding='utf-8-sig',newline='')):
            text=r.get('text',r.get('message_text',r.get('message','')))
            if not text:continue
            kind='earlier_supplied_test' if 'fresh_test' in path.name else 'earlier_supplied_training'
            history[normalize(redacted_case_view(clean(text)))].add(kind)
            original[clean(text).lower()].add(kind)
    texts=list(history);categories=sorted(set.union(*history.values()));lens=np.array([len(t) for t in texts])
    # Exact vectorized multiset upper bound only prunes mathematically impossible pairs.
    chars=' abcdefghijklmnopqrstuvwxyz'
    hist=np.array([[t.count(c) for c in chars] for t in texts],dtype=np.int32)
    ledger=[]
    for n,r in enumerate(rows):
        text=r['text_redacted'];exact=history.get(text,set());near=set();matchers={}
        vector=np.array([text.count(c) for c in chars])
        bounds=2*np.minimum(hist,vector).sum(axis=1)/np.maximum(1,lens+len(text))
        for i in np.flatnonzero(bounds>=.85):
            needed=history[texts[i]]-exact-near
            if not needed:continue
            sm=SequenceMatcher(None,text,texts[i],autojunk=False)
            if sm.ratio()>=.85:
                near.update(needed)
                for c in needed:matchers[c]=int(i)
        ledger.append(dict(id=r['id'],normalized_exact=sorted(exact),near_only=sorted(near),historical_match_indices=matchers))
        if (n+1)%400==0:print('Exposure audited',n+1,'/',len(rows),flush=True)
    write_json(output/'exposure-ledger.json',ledger)
    summary=dict(records=len(rows),historical_unique_normalized_texts=len(texts),historical_files=files,
        by_history={c:dict(normalized_exact=sum(c in r['normalized_exact'] for r in ledger),near_only=sum(c in r['near_only'] for r in ledger)) for c in categories},
        any_known_overlap=sum(bool(r['normalized_exact'] or r['near_only']) for r in ledger),
        no_detected_overlap=sum(not(r['normalized_exact'] or r['near_only']) for r in ledger),
        method='Exact normalized text; direct SequenceMatcher >=0.85 with lossless character-multiset upper-bound pruning',
        limitations='Earlier supplied training membership/partitions are incomplete; absence of a detected match is not proof of unseen or prospective data. No historical identifiers are reused as content identity.')
    write_json(output/'exposure-summary.json',summary);print('Exposure summary',summary['by_history'],flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);audit(p.parse_args().output)
