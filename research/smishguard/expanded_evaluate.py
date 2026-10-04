"""One shared final opening after four pipeline freezes, followed by faithful exports."""
import argparse
import json
from pathlib import Path
import pickle
import time
import numpy as np
from scipy.special import expit
from sklearn.metrics import f1_score, log_loss, brier_score_loss
from . import fair_compare as fair
from .expanded_prepare import load, counts
from .expanded_train import checked
from .evaluate import metrics
from .deployment_policy import assessable
from .mbert_experiment import imports
from .mbert_evaluate import paired, export_pipeline
from .preliminary_compare import PROBES
from .preprocessing import normalize
from .parity import predict
from .train import margin, write_json
from .uncertainty import cluster_intervals

def verify_files(root,files):
    for path,h in files.items():
        if fair.digest(root/path)!=h:raise ValueError('Frozen selected pipeline changed')

def deployment(texts,y,p,t,vocab):
    mask=np.array([assessable(text,vocab) for text in texts])
    return dict(records=len(y),scored=int(mask.sum()),abstained=int((~mask).sum()),coverage=float(mask.mean()),
        abstained_labels=dict(ham=int(((~mask)&(y==0)).sum()),smishing=int(((~mask)&(y==1)).sum())),
        conditional_metrics=metrics(y[mask],p[mask],t) if mask.any() else None,interpretation='Abstentions excluded, never scored as correct negatives')

def complete_intervals(y,p,groups,t):
    result=cluster_intervals(y,p,groups,t,seed=fair.SEED,repetitions=2000)
    rng=np.random.default_rng(fair.SEED);unique=np.unique(groups)
    extra={key:[] for key in ('macro_f1','brier','log_loss')}
    for _ in range(2000):
        ii=np.concatenate([np.flatnonzero(groups==g) for g in rng.choice(unique,len(unique),replace=True)])
        extra['macro_f1'].append(float(f1_score(y[ii],p[ii]>=t,labels=[0,1],average='macro',zero_division=0)))
        extra['brier'].append(float(brier_score_loss(y[ii],p[ii])))
        extra['log_loss'].append(float(log_loss(y[ii],p[ii],labels=[0,1])))
    result['intervals'].update({k:dict(valid_replicates=len(v),low=float(np.quantile(v,.025)),high=float(np.quantile(v,.975))) for k,v in extra.items()})
    return result

def run(output,export_only=False):
    prep,rows,m=checked(output);basefreeze=load(output/'baseline-freeze.json');run=output/'mbert';freeze=load(run/'freeze.json')
    verify_files(output,basefreeze['files']);verify_files(run,freeze['files'])
    if not load(run/'training-summary.json')['complete']:raise ValueError('Incomplete mBERT')
    freezehashes={'baseline':fair.digest(output/'baseline-freeze.json'),'mbert':fair.digest(run/'freeze.json')}
    if export_only:
        if load(output/'four-model-aggregate.json')['freeze_sha256']!=freezehashes:raise ValueError('Evaluation identity changed')
    else:
        with (output/'internal-test-started.json').open('x') as f:json.dump(freezehashes,f)
    torch,Model,Tokenizer,_=imports();torch.set_num_threads(4)
    model=Model.from_pretrained(run/'selected',local_files_only=True,attn_implementation='eager').cpu().eval()
    tokenizer=Tokenizer.from_pretrained(run/'selected',local_files_only=True);length=freeze['max_length']
    def encode(texts):return tokenizer(texts,max_length=length,truncation=True,padding='max_length',return_tensors='pt')
    def infer(texts):
        if model.training:raise ValueError('Dropout enabled during inference')
        with torch.no_grad():return np.concatenate([model(**encode([t])).logits.numpy() for t in texts])
    ids=m['partitions']['test'];texts=[rows[i]['text'] for i in ids];y=np.array([rows[i]['label'] for i in ids]);groups=np.array(m['groups'])[ids]
    vocab=load(output/'lr/model.json')['vocabulary'];preds={};scores={};results={}
    if not export_only:
        for name in (*fair.NAMES,'mbert'):
            started=time.perf_counter()
            if name=='mbert':
                logits=infer(texts);raw=logits[:,1]-logits[:,0];p=expit(freeze['calibration']['a']*raw+freeze['calibration']['b']);t=freeze['threshold']
                size=(run/'selected/model.safetensors').stat().st_size
            else:
                artifact=pickle.loads((output/name/'research-model.pkl').read_bytes());v=artifact['vectorizer'];classifier=artifact['model'];cal=artifact['calibrator'];t=artifact['threshold']
                raw=margin(classifier,v.transform([rows[i]['text_redacted'] for i in ids]));p=cal.predict_proba(raw.reshape(-1,1))[:,1]
                size=(output/name/'research-model.pkl').stat().st_size
            infer_seconds=time.perf_counter()-started;scores[name]=p;preds[name]=p>=t
            result=metrics(y,p,t);result.update(macro_f1=float(f1_score(y,p>=t,average='macro')),threshold=t,support=counts([rows[i] for i in ids],groups),
                model_bytes=size,host_cpu_inference_seconds=infer_seconds,deployment=deployment(texts,y,p,t,vocab),
                confidence_intervals=complete_intervals(y,p,groups,t))
            for field in ('language','category','source'):
                result['by_'+field]={}
                for value in sorted({rows[i][field] for i in ids}):
                    ii=[j for j,i in enumerate(ids) if rows[i][field]==value];labels=y[ii];adequate=len(ii)>=20 and min(sum(labels==0),sum(labels==1))>=5
                    result['by_'+field][value]=dict(support=counts([rows[ids[j]] for j in ii],groups[ii]),metrics=metrics(labels,p[ii],t) if adequate else None,
                        note='descriptive only' if adequate else 'Insufficient support: require >=20 records and >=5 per class')
            results[name]=result
            write_json(output/f'{name}/test-predictions.json',dict(ids=[rows[i]['id'] for i in ids],scores=p.tolist(),predictions=(p>=t).tolist(),margin=raw.tolist()))
            print(name,'final evaluation recorded, F1',result['f1'],flush=True)
        exposure={r['id']:r for r in load(output/'exposure-ledger.json')}
        exposure_support=dict(records=len(ids),known_overlap=sum(bool(exposure[rows[i]['id']]['normalized_exact'] or exposure[rows[i]['id']]['near_only']) for i in ids))
        write_json(output/'paired-predictions.json',dict(ids=[rows[i]['id'] for i in ids],labels=y.tolist(),groups=groups.tolist(),scores={k:v.tolist() for k,v in scores.items()},predictions={k:v.tolist() for k,v in preds.items()},mbert_logits=logits.tolist()))
        write_json(output/'four-model-aggregate.json',dict(results=results,paired_f1=paired(y,preds,groups),freeze_sha256=freezehashes,preparation=prep,
            exposure_summary=load(output/'exposure-summary.json'),test_exposure=exposure_support,
            status='preliminary source/rule labels; retrospective development; no independently verified labels or prospective claims'))
    for name in fair.NAMES:
        target=output/name;artifact=pickle.loads((target/'research-model.pkl').read_bytes());export=load(target/'model.json');alltexts=PROBES+texts
        raw=margin(artifact['model'],artifact['vectorizer'].transform([normalize(t) for t in alltexts]));p=artifact['calibrator'].predict_proba(raw.reshape(-1,1))[:,1]
        cases=[]
        for text,score,rawmargin in zip(alltexts,p,raw):
            got,label=predict(export,text)
            if abs(got-score)>1e-10:raise ValueError('Python fitted export parity failed')
            cases.append(dict(text=text,normalized=normalize(text),score=float(score),margin=float(rawmargin),suspicious=label,assessable=assessable(text,export['vocabulary'])))
        parity=target/'parity';parity.mkdir(exist_ok=True);(parity/'model.json').write_bytes((target/'model.json').read_bytes());write_json(parity/'cases.json',cases)
        assets=parity/'android-test-assets';assets.mkdir(exist_ok=True);write_json(assets/'comparison-private-cases.json',cases)
        write_json(target/'parity-summary.json',dict(cases=len(cases),python_max_error=max(abs(predict(export,t)[0]-s) for t,s in zip(alltexts,p)),model_sha256=fair.digest(target/'model.json')))
    if not (run/'export-aggregate.json').exists():
        export_pipeline(run,freeze['configuration'],freeze,torch,model,encode,infer,texts,vocab)
        metadata=load(run/'app-assets/model.json');metadata['model_version']=freeze['configuration']['model_version'];write_json(run/'app-assets/model.json',metadata)
        summary=load(run/'export-aggregate.json');summary['metadata_sha256']=fair.digest(run/'app-assets/model.json');write_json(run/'export-aggregate.json',summary)
        licensepath=Path('research/data/mbert-20261002/experiment-v2/app-assets/LICENSE.txt')
        if not licensepath.exists():licensepath=Path('android/app/src/mbert/assets/LICENSE.txt')
        (run/'app-assets/LICENSE.txt').write_bytes(licensepath.read_bytes())
    print('Four-model evaluation and export completed; no test-based retuning.',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--export-only',action='store_true');a=p.parse_args();run(a.output,a.export_only)
