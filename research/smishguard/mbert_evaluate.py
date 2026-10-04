"""One retrospective mBERT test opening, paired supplement, and faithful ONNX export."""
import argparse
import json
from pathlib import Path
import pickle
import time
import numpy as np
from scipy.special import expit
from sklearn.metrics import f1_score
from . import fair_compare as fair
from .mbert_experiment import checked, imports, BASE_ID, REVISION
from .preliminary_compare import PROBES, deployment_metrics
from .deployment_policy import assessable
from .evaluate import metrics
from .uncertainty import cluster_intervals
from .train import write_json, margin


def paired(y,predictions,groups):
    names=list(predictions);keys=[(a,b) for j,a in enumerate(names) for b in names[j+1:]]
    if not fair.adequate_groups(y,groups):return {'status':'insufficient independent groups','intervals':None}
    rng=np.random.default_rng(fair.SEED);unique=np.unique(groups);samples={f'{a}-{b}':[] for a,b in keys}
    for _ in range(2000):
        idx=np.concatenate([np.flatnonzero(groups==g) for g in rng.choice(unique,len(unique),replace=True)])
        if len(np.unique(y[idx]))<2:continue
        scores={k:f1_score(y[idx],v[idx],zero_division=0) for k,v in predictions.items()}
        for a,b in keys:samples[f'{a}-{b}'].append(float(scores[a]-scores[b]))
    return dict(method='paired group bootstrap; 2000 common draws; conditional fixed-model marginal intervals',seed=fair.SEED,
        intervals={k:dict(low=float(np.quantile(v,.025)),high=float(np.quantile(v,.975)),valid_replicates=len(v)) for k,v in samples.items()},
        limitations='No fitting uncertainty, simultaneous multiplicity correction, independent labels or prospective population claim')


def run(output, export_only=False):
    c,rows,m=checked(output);torch,Model,Tokenizer,_=imports()
    freeze=json.loads((output/'freeze.json').read_text(encoding='utf-8'))
    if freeze['configuration'] != c:raise ValueError('Configuration differs from frozen pipeline')
    for file,digest in freeze['files'].items():
        if fair.digest(output/file)!=digest:raise ValueError('Selected pipeline changed after freeze')
    if not json.loads((output/'training-summary.json').read_text())['complete']:raise ValueError('Training incomplete')
    baseline=Path(c['baseline'])
    for file,key in (('dataset.json','dataset_sha256'),('splits.json','split_sha256')):
        if fair.digest(baseline/file)!=c[key]:raise ValueError('Baseline data or partitions changed')
    base_rows=json.loads((baseline/'dataset.json').read_text(encoding='utf-8'))
    if any(r['id']!=b['id'] or r['label']!=int(b['label']) for r,b in zip(rows,base_rows)) or len(rows)!=len(base_rows):
        raise ValueError('Paired message IDs or labels changed')
    if export_only:
        recorded=json.loads((output/'four-model-aggregate.json').read_text(encoding='utf-8'))
        if recorded['mbert_freeze_sha256']!=fair.digest(output/'freeze.json'):raise ValueError('Evaluation freeze mismatch')
        if (output/'export-aggregate.json').exists():raise ValueError('Preserve completed export')
    else:
        with (output/'internal-test-started.json').open('x') as f:json.dump({'freeze_sha256':fair.digest(output/'freeze.json')},f)
    torch.set_num_threads(4);length=freeze['max_length']
    model=Model.from_pretrained(output/'selected',local_files_only=True,attn_implementation='eager').cpu().eval()
    tokenizer=Tokenizer.from_pretrained(output/'selected',local_files_only=True)
    test_ids=m['partitions']['test'];texts=[rows[i]['text'] for i in test_ids];y=np.array([rows[i]['label'] for i in test_ids]);groups=np.array(m['groups'])[test_ids]
    def encode(texts):return tokenizer(texts,truncation=True,max_length=length,padding='max_length',return_tensors='pt')
    def infer(texts):
        if model.training:raise ValueError('Parity reference must remain in evaluation mode; dropout is not inference')
        with torch.no_grad():return np.concatenate([model(**encode([t])).logits.numpy() for t in texts])
    vocab=json.loads((baseline/'lr/model.json').read_text())['vocabulary']
    if export_only:
        export_pipeline(output,c,freeze,torch,model,encode,infer,texts,vocab)
        return
    started=time.perf_counter();logits=infer(texts);elapsed=time.perf_counter()-started
    scores=expit(freeze['calibration']['a']*(logits[:,1]-logits[:,0])+freeze['calibration']['b']);threshold=freeze['threshold']
    basefreeze=json.loads((baseline/'freeze.json').read_text())
    baseline_results=json.loads((baseline/'comparison-aggregate.json').read_text())
    results={};predictions={};all_scores={}
    for name in fair.NAMES:
        path=baseline/name/'research-model.pkl'
        if fair.digest(path)!=basefreeze['files'][f'{name}/research-model.pkl']:raise ValueError('Baseline model changed')
        artifact=pickle.loads(path.read_bytes())
        x=artifact['vectorizer'].transform([base_rows[i]['text_redacted'] for i in test_ids])
        p=artifact['calibrator'].predict_proba(margin(artifact['model'],x).reshape(-1,1))[:,1]
        pred=p>=artifact['threshold'];predictions[name]=pred;all_scores[name]=p
        result=metrics(y,p,artifact['threshold'])
        for key in ('f1','precision','recall','confusion','false_positive_rate'):
            if result[key]!=baseline_results['results'][name][key]:raise ValueError('Prior baseline result changed')
        result['macro_f1']=float(f1_score(y,pred,average='macro',zero_division=0));result['class_support']={'ham':int((y==0).sum()),'smishing':int((y==1).sum())}
        result['confidence_intervals']=baseline_results['results'][name]['confidence_intervals']
        results[name]=result
    predictions['mbert']=scores>=threshold;all_scores['mbert']=scores
    result=metrics(y,scores,threshold);result['macro_f1']=float(f1_score(y,scores>=threshold,average='macro',zero_division=0))
    result.update(class_support={'ham':int((y==0).sum()),'smishing':int((y==1).sum())},
        confidence_intervals=cluster_intervals(y,scores,groups,threshold,seed=fair.SEED,repetitions=2000),
        raw_softmax_diagnostics=metrics(y,expit(logits[:,1]-logits[:,0]),.5),
        host_cpu_test_seconds=elapsed,host_cpu_records=len(texts),model_safetensors_bytes=(output/'selected/model.safetensors').stat().st_size)
    result['deployment']=deployment_metrics(texts,y,scores,threshold,set(vocab))
    results['mbert']=result
    write_json(output/'paired-predictions.json',dict(ids=[rows[i]['id'] for i in test_ids],labels=y.tolist(),groups=groups.tolist(),
        scores={k:v.tolist() for k,v in all_scores.items()},predictions={k:v.tolist() for k,v in predictions.items()},mbert_logits=logits.tolist()))
    write_json(output/'four-model-aggregate.json',dict(results=results,paired_f1=paired(y,predictions,groups),
        test_records=len(y),test_groups=len(set(groups)),dataset_sha256=c['dataset_sha256'],split_sha256=c['split_sha256'],
        case_view_sha256=c['case_view_sha256'],mbert_freeze_sha256=fair.digest(output/'freeze.json'),
        model_id=BASE_ID,revision=REVISION,status='mBERT later-added exploratory; exposed internal evaluation; inherited labels unconfirmed'))
    export_pipeline(output,c,freeze,torch,model,encode,infer,texts,vocab)


def export_pipeline(output,c,freeze,torch,model,encode,infer,texts,vocab):
    # Export selected weights unchanged. No quantization and no retuning on export/test differences.
    length=freeze['max_length'];threshold=freeze['threshold']
    assets=output/'app-assets';assets.mkdir(exist_ok=True)
    class Wrapper(torch.nn.Module):
        def __init__(self,model):super().__init__();self.model=model
        def forward(self,input_ids,attention_mask,token_type_ids):
            return self.model(input_ids=input_ids,attention_mask=attention_mask,token_type_ids=token_type_ids).logits
    probe=encode(['Hello po'])
    # Export restores the wrapper's prior training flag recursively. Set the
    # wrapper to eval too, so restoration cannot reactivate the child's dropout.
    torch.onnx.export(Wrapper(model).eval(),(probe['input_ids'],probe['attention_mask'],probe['token_type_ids']),str(assets/'model.onnx'),
        input_names=['input_ids','attention_mask','token_type_ids'],output_names=['logits'],opset_version=17,dynamo=False,external_data=False)
    (assets/'vocab.txt').write_bytes((output/'selected/vocab.txt').read_bytes())
    metadata=dict(schema_version=5,algorithm='mbert',model_version='mbert-exploratory-20261002',base_model=BASE_ID,revision=REVISION,
        max_length=length,classes=['ham','smishing'],positive_class='smishing',threshold=threshold,threshold_comparison='greater_or_equal',
        calibration=freeze['calibration'],score_transform='sigmoid_of_logit_difference',precision='float32',quantized=False,
        synthetic=False,automatic_warnings_approved=False,evaluation_status='preliminary_retrospective',label_status='inherited_unconfirmed',
        tokenizer=dict(type='BertWordPiece',lowercase=False,strip_accents=False,clean_text=True,handle_chinese_chars=True,max_chars_per_word=100),
        redaction='case-preserving URL/email/digit placeholders before native tokenization',assessability_vocabulary=vocab,
        dataset_sha256=c['dataset_sha256'],split_sha256=c['split_sha256'],protocol_sha256=c['protocol_sha256'],
        model_sha256=fair.digest(assets/'model.onnx'),vocab_sha256=fair.digest(assets/'vocab.txt'))
    write_json(assets/'model.json',metadata)
    import onnxruntime as ort
    options=ort.SessionOptions();options.intra_op_num_threads=4;options.inter_op_num_threads=1
    session=ort.InferenceSession(str(assets/'model.onnx'),options,providers=['CPUExecutionProvider'])
    probes=PROBES+['Hello HELLO hello','Kumusta po, bayad na ang utang.','你好，账户信息。','नमस्ते','é ñ İ 😀','[CLS] [MASK] [SEP]','hello '*300]
    alltexts=probes+texts;cases=[];errors=[];margin_errors=[];score_errors=[];near=0;flips=0
    for i,text in enumerate(alltexts):
        from .mbert_experiment import redacted_case_view
        # Test text is already redacted; invented raw probes use the deployed transform.
        text=redacted_case_view(text)
        inputs=encode([text]);ref=infer([text])[0]
        got=session.run(None,{k:v.numpy() for k,v in inputs.items()})[0][0]
        a=metadata['calibration']['a'];b=metadata['calibration']['b'];refscore=float(expit(a*(ref[1]-ref[0])+b));score=float(expit(a*(got[1]-got[0])+b))
        error=float(np.max(np.abs(got-ref)));merror=abs(float(got[1]-got[0])-float(ref[1]-ref[0]));serror=abs(score-refscore)
        errors.append(error);margin_errors.append(merror);score_errors.append(serror)
        near+=abs(refscore-threshold)<=1e-5;flips+=(score>=threshold)!=(refscore>=threshold)
        if error>1e-4 or merror>1e-4 or serror>1e-5 or ((score>=threshold)!=(refscore>=threshold) and abs(refscore-threshold)>1e-5):
            write_json(output/'export-parity-failure.json',dict(private_case_index=i,logit_error=error,margin_error=merror,score_error=serror,
                reference_logits=ref.tolist(),runtime_logits=got.tolist(),reference_score=refscore,runtime_score=score))
            raise ValueError('ONNX parity exceeds declared tolerance; numeric diagnostic retained privately')
        cases.append(dict(text=text,input_ids=inputs['input_ids'][0].tolist(),attention_mask=inputs['attention_mask'][0].tolist(),
            token_type_ids=inputs['token_type_ids'][0].tolist(),logits=ref.tolist(),score=refscore,suspicious=refscore>=threshold,assessable=assessable(text,vocab)))
    parity=output/'android-test-assets';parity.mkdir(exist_ok=True);write_json(parity/'mbert-private-cases.json',cases)
    write_json(output/'threshold-parity-indices.json',dict(indices=sorted(range(len(cases)),key=lambda i:abs(cases[i]['score']-threshold))[:10]))
    write_json(output/'export-aggregate.json',dict(cases=len(cases),max_logit_error=max(errors),max_score_error=max(score_errors),
        max_margin_error=max(margin_errors),nearest_threshold_distance=min(abs(v['score']-threshold) for v in cases),
        near_threshold_cases=near,class_changes=flips,onnx_bytes=(assets/'model.onnx').stat().st_size,
        model_sha256=metadata['model_sha256'],metadata_sha256=fair.digest(assets/'model.json'),cases_sha256=fair.digest(parity/'mbert-private-cases.json'),
        quantized=False,onnxruntime=ort.__version__,providers=session.get_providers()))
    print('Four-model supplement and float32 ONNX parity completed; private predictions retained.',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path)
    p.add_argument('--export-only',action='store_true',help='Recover a failed export of the same frozen checkpoint without rewriting research results')
    args=p.parse_args();run(args.output,args.export_only)
