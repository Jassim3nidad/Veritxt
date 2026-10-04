"""Later-added local mBERT run. Private records never sent to a model service."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import time
import zipfile

import numpy as np
from . import fair_compare as fair
from .preprocessing import normalize, URL, EMAIL
from .source_matching import SOURCES, parse_member
from .review_packets import private_output
from .train import write_json

ROOT=Path(__file__).resolve().parents[2]
BASE_ID='google-bert/bert-base-multilingual-cased'
REVISION='3f076fdb1ab68d5b2880cb87a0886f315b8146f8'
DATA_HASH='1d62dc1a25d86eeead92ec88109cfdd12d235edef596b51b969cb9a61f80a408'
SPLIT_HASH='12f62d292dc9b4948faa755eedb79fcc499ba32e69c700a38f39f4dfce16339d'
SEED=20261002
PROTOCOL=ROOT/'docs/mbert-exploratory-protocol-20261002.md'


def redacted_case_view(text):
    text=URL.sub(' zzurlzz ',text)
    text=EMAIL.sub(' zzemailzz ',text)
    return re.sub(r'[0-9]+',' zznumberzz ',text)


def prepare(baseline,source_snapshots,output):
    for p in (baseline,source_snapshots,output):private_output(p)
    if fair.digest(baseline/'dataset.json')!=DATA_HASH or fair.digest(baseline/'splits.json')!=SPLIT_HASH:
        raise ValueError('Frozen baseline fingerprints changed')
    if output.exists():raise ValueError('Preserve prior mBERT run')
    output.mkdir(parents=True)
    sources={}
    for name in ('tagalog','marketing'):
        spec=SOURCES[name]
        with zipfile.ZipFile(source_snapshots/(name+'.zip')) as z:data=z.read(spec['member'])
        if hashlib.sha256(data).hexdigest()!=spec['sha256']:raise ValueError('Source snapshot changed')
        sources[name]=parse_member(data,spec['member'])
    rows=json.loads((baseline/'dataset.json').read_text(encoding='utf-8'));view=[]
    for row in rows:
        name=next(iter(row['source_matches']));n=row['source_matches'][name]['candidate_rows'][0]-2
        text=redacted_case_view(str(sources[name][n]['text']))
        if normalize(text)!=row['text_redacted']:raise ValueError('Underlying message identity mismatch; contents withheld')
        view.append(dict(id=row['id'],text=text,label=int(row['label'])))
    write_json(output/'case-view.json',view)
    (output/'splits.json').write_bytes((baseline/'splits.json').read_bytes())
    write_json(output/'configuration.json',dict(model_id=BASE_ID,revision=REVISION,seed=SEED,epochs=2,wall_budget_seconds=2700,
        learning_rate=2e-5,optimizer='Adafactor',microbatch=1,gradient_accumulation=8,
        dataset_sha256=DATA_HASH,split_sha256=SPLIT_HASH,case_view_sha256=fair.digest(output/'case-view.json'),
        protocol_sha256=fair.digest(PROTOCOL),code_sha256=fair.digest(Path(__file__)),
        retrospective=True,later_added=True,independent_labels=False,baseline=str(baseline.resolve())))
    print('Case-preserving view reconciled to all 1068 frozen records; unchanged labels and split.',flush=True)


def imports():
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1',TOKENIZERS_PARALLELISM='false',CUBLAS_WORKSPACE_CONFIG=':4096:8')
    import torch
    from transformers import BertForSequenceClassification,BertTokenizerFast,Adafactor
    return torch,BertForSequenceClassification,BertTokenizerFast,Adafactor


def checked(output):
    private_output(output);c=json.loads((output/'configuration.json').read_text(encoding='utf-8'))
    for p,key in ((output/'case-view.json','case_view_sha256'),(output/'splits.json','split_sha256'),(PROTOCOL,'protocol_sha256'),(Path(__file__),'code_sha256')):
        if fair.digest(p)!=c[key]:raise ValueError('Frozen mBERT preparation changed')
    return c,json.loads((output/'case-view.json').read_text(encoding='utf-8')),json.loads((output/'splits.json').read_text(encoding='utf-8'))


def train(base,output):
    c,rows,m=checked(output);torch,Model,Tokenizer,Adafactor=imports()
    if not torch.cuda.is_available():raise ValueError('Configured CUDA training unavailable; no silent CPU budget change')
    random.seed(SEED);np.random.seed(SEED);torch.manual_seed(SEED);torch.cuda.manual_seed_all(SEED)
    torch.use_deterministic_algorithms(True);torch.set_num_threads(4)
    tokenizer=Tokenizer.from_pretrained(base,local_files_only=True,do_lower_case=False)
    assert not tokenizer.do_lower_case
    parts=m['partitions'];train_ids=parts['train']
    lengths=[len(tokenizer(rows[i]['text'],truncation=False)['input_ids']) for i in train_ids]
    length=min(128,max(64,int(math.ceil(float(np.percentile(lengths,95))/16)*16)))
    with (output/'training-started.json').open('x') as f:json.dump({'started':time.time(),'max_length':length},f)
    model=Model.from_pretrained(base,num_labels=2,id2label={0:'ham',1:'smishing'},label2id={'ham':0,'smishing':1},
        local_files_only=True,use_safetensors=True,attn_implementation='eager').cuda()
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})
    optimizer=Adafactor(model.parameters(),lr=c['learning_rate'],relative_step=False,scale_parameter=False,warmup_init=False,weight_decay=.01)
    scaler=torch.amp.GradScaler('cuda')
    def encode(ids):
        return {k:v.cuda() for k,v in tokenizer([rows[i]['text'] for i in ids],max_length=length,truncation=True,padding='max_length',return_tensors='pt').items()}
    def logits(ids):
        model.eval();out=[]
        with torch.no_grad():
            for i in ids:out.append(model(**encode([i])).logits.float().cpu().numpy()[0])
        return np.array(out)
    from sklearn.metrics import average_precision_score,f1_score
    started=time.monotonic();history=[];best=-1.;complete=True
    for epoch in range(2):
        order=np.random.default_rng(SEED+epoch).permutation(train_ids).tolist();model.train()
        losses=[]
        for start in range(0,len(order),8):
            if time.monotonic()-started>c['wall_budget_seconds']:complete=False;break
            chunk=order[start:start+8];optimizer.zero_grad(set_to_none=True)
            for i in chunk:
                with torch.autocast('cuda',dtype=torch.float16):
                    loss=model(**encode([i]),labels=torch.tensor([rows[i]['label']],device='cuda')).loss/len(chunk)
                scaler.scale(loss).backward();losses.append(float(loss.detach())*len(chunk))
            scaler.unscale_(optimizer);torch.nn.utils.clip_grad_norm_(model.parameters(),1.)
            scaler.step(optimizer);scaler.update()
            if start%80==0:print(f'Epoch {epoch+1}, training records {min(start+8,len(order))}/{len(order)}; no text logged.',flush=True)
        if not complete:break
        valid=logits(parts['validation']);yv=np.array([rows[i]['label'] for i in parts['validation']])
        ap=float(average_precision_score(yv,valid[:,1]-valid[:,0]));history.append(dict(epoch=epoch+1,validation_average_precision=ap,mean_training_loss=float(np.mean(losses))))
        if ap>best:
            best=ap;model.save_pretrained(output/'selected',safe_serialization=True);tokenizer.save_pretrained(output/'selected');selected_epoch=epoch+1
        print('Completed epoch',epoch+1,'validation AP',ap,flush=True)
    elapsed=time.monotonic()-started
    write_json(output/'training-summary.json',dict(complete=complete,epochs_completed=len(history),selected_epoch=locals().get('selected_epoch'),
        history=history,seconds=elapsed,max_length=length,train_length_p95=float(np.percentile(lengths,95)),
        train_truncated=sum(n>length for n in lengths),trainable_parameters=sum(p.numel() for p in model.parameters() if p.requires_grad),
        gpu=torch.cuda.get_device_name(),peak_cuda_bytes=torch.cuda.max_memory_allocated(),torch=torch.__version__))
    if not complete:raise ValueError('Bounded training budget exceeded; incomplete run recorded')
    del model,optimizer;torch.cuda.empty_cache()
    model=Model.from_pretrained(output/'selected',local_files_only=True,attn_implementation='eager').cuda()
    calibration=logits(parts['calibration']);yc=np.array([rows[i]['label'] for i in parts['calibration']])
    from sklearn.linear_model import LogisticRegression
    cal=LogisticRegression(random_state=SEED).fit((calibration[:,1]-calibration[:,0]).reshape(-1,1),yc)
    valid=logits(parts['validation']);p=cal.predict_proba((valid[:,1]-valid[:,0]).reshape(-1,1))[:,1]
    threshold=float(max(np.linspace(.05,.95,91),key=lambda t:(f1_score(yv,p>=t),t)))
    write_json(output/'freeze.json',dict(configuration=c,max_length=length,selected_epoch=selected_epoch,threshold=threshold,
        calibration=dict(method='sigmoid',a=float(cal.coef_[0,0]),b=float(cal.intercept_[0]),fit_partition='calibration',evaluated=False),
        files={str(f.relative_to(output)):fair.digest(f) for f in (output/'selected').iterdir() if f.is_file()},test_opened=False))
    print('Selected mBERT, calibration and threshold frozen before internal-test predictions.',flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='command',required=True)
    a=s.add_parser('prepare');a.add_argument('baseline',type=Path);a.add_argument('sources',type=Path);a.add_argument('output',type=Path)
    a=s.add_parser('train');a.add_argument('base',type=Path);a.add_argument('output',type=Path)
    a=p.parse_args()
    if a.command=='prepare':prepare(a.baseline,a.sources,a.output)
    else:train(a.base,a.output)

if __name__=='__main__':main()
