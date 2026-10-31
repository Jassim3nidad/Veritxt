"""Replay the preserved fitted historical baselines, without fitting or selection."""
import argparse
import pickle
from pathlib import Path
import numpy as np
from smishguard import bantaytext_workflow as w


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,default=Path('research/runs/bantaytext-20261013/notebook-run-v3'))
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    if args.output.exists():raise ValueError('Baseline replay requires a new output file')
    rows=w.load(args.run/'dataset.json');results=[]
    for name in ['svm-C-10.0','lr-C-10.0','nb-word1-english']:
        folder=args.run/'grouped'/name
        # Only previously fitted trusted local research artifacts, not external pickles.
        a=pickle.loads((folder/'pipeline.pkl').read_bytes());p=w.load(folder/'test-predictions.json')
        s=w.score(a,[rows[i]['text'] for i in p['indices']]);error=float(np.max(np.abs(s-p['scores'])))
        if error>1e-12:raise ValueError('Frozen historical predictions changed')
        results.append(dict(id=name,max_score_error=error,metrics=w.calculate_metrics(p['labels'],s,a['threshold'],a['probability']),
            pipeline_sha256=w.digest(folder/'pipeline.pkl')))
    args.output.parent.mkdir(parents=True,exist_ok=True);w.save(args.output,results)
    print('Three historical baseline score/metric replays completed; max error',max(x['max_score_error'] for x in results))


if __name__=='__main__':main()
