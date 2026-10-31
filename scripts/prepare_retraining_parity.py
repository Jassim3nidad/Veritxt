"""Prepare private candidate probes using actual fitted parameters; no app installation."""
import argparse
import pickle
import shutil
from pathlib import Path
from smishguard import retraining as r
from smishguard.raw_sms_validation import raw_view, adapter_contract, PROBES


def main():
    p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('--family',choices=list('ABCDE'))
    p.add_argument('--output',type=Path,required=True);p.add_argument('--legacy-parity',type=Path);args=p.parse_args()
    s=r.load(args.run/'selection.json');c=s['family_winners'][args.family] if args.family else s['selected']
    args.output.mkdir(parents=True,exist_ok=False)
    a=pickle.loads((args.run/c['fit_id']/'pipeline.pkl').read_bytes());r.export_candidate(a,c,args.output)
    r.save(args.output/'raw-sms-adapter.json',adapter_contract())
    # Unpaired surrogates/oversized probes are handled by detector tests; not scoreable UTF-8 strings.
    texts=[t for t in PROBES if not any(0xd800<=ord(ch)<=0xdfff for ch in t) and len(t)<=10000]
    views=[raw_view(t) for t in texts];scores=r.score(a,views,c['mode'])
    r.save(args.output/'research-raw-cases.json',dict(synthetic=True,cases=[dict(raw=t,view=v,score=float(s)) for t,v,s in zip(texts,views,scores)]))
    assets=args.output/'android-test-assets';assets.mkdir()
    for name in ['candidate-model.json','candidate-cases.json','raw-sms-adapter.json','research-raw-cases.json']:
        shutil.copyfile(args.output/name,assets/name)
    # Reuse already locked predictions, with no new tuning/scoring pass. Private
    # SMS remain only in ignored test fixtures/APKs, never notebook/public logs.
    pred=r.load(args.run/f'holdout-{c["family"]}-predictions.json');rows=r.load(args.run/'dataset.json')
    r.save(args.output/'research-evaluation-cases.json',dict(synthetic=False,history='previously_used',
        cases=[dict(text=rows[i]['text'],label=y,score=score) for i,y,score in zip(pred['indices'],pred['labels'],pred['scores'])]))
    shutil.copyfile(args.output/'research-evaluation-cases.json',assets/'research-evaluation-cases.json')
    if args.legacy_parity:
        for name in ['model.json','cases.json','active-model.json','active-cases.json']:
            shutil.copyfile(args.legacy_parity/name,args.output/name)
    r.save(args.output/'parity-manifest.json',dict(family=c['family'],selected_id=c['id'],
        fitting_sha256=r.digest(args.run/c['fit_id']/'pipeline.pkl'),synthetic_raw_probes=len(texts),
        synthetic_masked_probes=len(r.load(args.output/'candidate-cases.json')['cases']),
        real_masked_evaluation_cases=len(pred['indices']),
        files={name:r.digest(args.output/name) for name in ['candidate-model.json','candidate-cases.json','raw-sms-adapter.json','research-raw-cases.json','research-evaluation-cases.json']},
        intended_use='Private offline candidate validation, production assets unchanged'))
    print('Prepared actual',c['family'],'export and',len(texts),'synthetic raw SMS probes')


if __name__=='__main__':main()
