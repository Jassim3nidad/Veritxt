"""Matched character-feature diagnostic on validation only; cannot change selection."""
import argparse
import pickle
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits
from smishguard import retraining as r


def main():
    p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('output',type=Path);args=p.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    selected=r.load(args.run/'selection.json');c=selected['family_winners']['C']
    rows=r.load(args.run/'dataset.json');split=r.load(args.run/'splits.json');groups=np.asarray(split['groups']);split=split['partitions']
    matched=dict(c['spec'],combined=False,id='matched-word-only-C-control')
    r.save(args.output/'protocol.json',dict(reference=c['id'],word_control=matched,
        changed_factor='Remove char_wb block only; preserve C/class weight/word ngrams/min_df/feature cap/calibration mode/fold seed',
        membership='Original training and validation only; no holdout read or fit',
        threshold='Original validation operating policy, diagnostic only; never reselect production/research candidate',
        interpretation='Post-selection matched development diagnostic, not independent confirmation'))
    reference=pickle.loads((args.run/c['fit_id']/'pipeline.pkl').read_bytes())
    with threadpool_limits(limits=1):
        control=r.fit(rows,groups,split['train'],matched,42)
    (args.output/'word-control.pkl').write_bytes(pickle.dumps(control,protocol=5))
    ids=split['validation'];y=[rows[i]['label'] for i in ids];texts=[rows[i]['text'] for i in ids]
    results={}
    for name,a in [('combined',reference),('word_only',control)]:
        scores=r.score(a,texts,c['mode']);op=r.choose_threshold(y,scores,True)
        results[name]=dict(default=r.metrics(y,scores,.5,True),operating_point=op,
            feature_count=a['feature_count'],training_seconds=a['training_seconds'])
        r.save(args.output/(name+'-predictions.json'),dict(indices=ids,labels=y,scores=scores.tolist()))
    r.save(args.output/'aggregate.json',results)
    print({name:dict(AP=item['default']['average_precision'],operating_recall=item['operating_point']['metrics']['recall']) for name,item in results.items()})


if __name__=='__main__':main()
