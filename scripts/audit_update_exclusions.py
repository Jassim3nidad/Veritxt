"""Private included/excluded near-overlap and stale-review coverage audit."""
import argparse
from collections import Counter,defaultdict
from difflib import SequenceMatcher
from pathlib import Path
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research'))
from smishguard.new_dataset_compare import read_csv,template_key
from smishguard.expanded_prepare import clean
from smishguard.mbert_experiment import redacted_case_view
from smishguard.preprocessing import normalize
from smishguard.train import write_json


def audit(package,output):
    included=read_csv(package/'smishguard_dataset.csv')
    excluded=read_csv(package/'smishguard_excluded.csv')
    index=defaultdict(set)
    for i,r in enumerate(included):
        index[normalize(redacted_case_view(clean(r['text'])))].add(i)
    texts=sorted(index)
    lengths=np.array([len(t) for t in texts])
    chars=' abcdefghijklmnopqrstuvwxyz'
    hist=np.array([[t.count(c) for c in chars] for t in texts],dtype=np.int32)
    templates=defaultdict(set)
    for i,r in enumerate(included):
        templates[r['template_group']].add(i)
    ledger=[]
    for n,r in enumerate(excluded):
        text=normalize(redacted_case_view(clean(r['text'])))
        exact=index.get(text,set())
        supplied=templates.get(template_key(r['text']),set())
        near=set()
        by_label={}
        vector=np.array([text.count(c) for c in chars])
        bounds=2*np.minimum(hist,vector).sum(axis=1)/np.maximum(1,lengths+len(text))
        for i in np.flatnonzero(bounds>=.85):
            labels={included[j]['label'] for j in index[texts[i]]}
            if labels<=set(by_label):
                continue
            if SequenceMatcher(None,text,texts[i],autojunk=False).ratio()>=.85:
                near.update(index[texts[i]])
                for j in index[texts[i]]:
                    by_label.setdefault(included[j]['label'],j)
        ledger.append(dict(excluded_position=n,excluded_label=r['excluded_as'],normalized_exact_indices=sorted(exact),
            same_template_indices=sorted(supplied),direct_near_witness_by_included_label=by_label))
        if (n+1)%300==0:
            print('Included/excluded near audit',n+1,'/',len(excluded),flush=True)
    write_json(output/'excluded-overlap-ledger.json',ledger)
    summary=dict(excluded_records=len(excluded),included_records=len(included),
        normalized_exact_overlap_records=sum(bool(r['normalized_exact_indices']) for r in ledger),
        same_template_overlap_records=sum(bool(r['same_template_indices']) for r in ledger),
        direct_near_overlap_records=sum(bool(r['direct_near_witness_by_included_label']) for r in ledger),
        direct_near_by_included_label={label:sum(label in r['direct_near_witness_by_included_label'] for r in ledger) for label in ('ham','smishing','gambling_ad')},
        near_method='SequenceMatcher >=0.85, lossless multiset bound; one direct witness per included label, not an exhaustive pair listing',
        interpretation='Excluded records remain excluded. Template/near overlap is not proof of a wrong label; flagged for scope review, never mapped to ham.',
        excluded_classes=dict(Counter(r['excluded_as'] for r in excluded)))
    write_json(output/'excluded-overlap-summary.json',summary)
    print('Excluded overlap audit saved; no labels or fitting corpus changed.',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('package',type=Path)
    p.add_argument('output',type=Path)
    a=p.parse_args()
    audit(a.package,a.output)
