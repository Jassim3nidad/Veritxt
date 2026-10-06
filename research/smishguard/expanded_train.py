"""Train the expanded experiment with shared frozen partitions and resumable mBERT."""
import argparse
import json
import math
import os
from pathlib import Path
import pickle
import random
import time
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, f1_score
from . import fair_compare as fair
from .expanded_prepare import PROTOCOL, load
from .linear_export import export_linear
from .mbert_experiment import imports, BASE_ID, REVISION
from .train import write_json, margin
from .vocabulary_policy import screen

SEED=20261005

def checked(output):
    prep=load(output/'preparation.json')
    for file,key in ((output/'dataset.json','dataset_sha256'),(output/'splits.json','split_sha256'),(output/'case-view.json','case_view_sha256'),(PROTOCOL,'protocol_sha256')):
        if fair.digest(file)!=prep[key]:raise ValueError('Frozen data/split/protocol changed')
    if not (output/'exposure-summary.json').exists():raise ValueError('Complete exposure audit before training')
    return prep,load(output/'dataset.json'),load(output/'splits.json')

def peak_memory():
    # Windows process peak working set, not an inferred per-model GPU measurement.
    import ctypes
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[(k,ctypes.c_size_t) for k in ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
    c=Counters();c.cb=ctypes.sizeof(c)
    kernel=ctypes.windll.kernel32;psapi=ctypes.windll.psapi
    kernel.GetCurrentProcess.restype=wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes=[wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD]
    psapi.GetProcessMemoryInfo.restype=wintypes.BOOL
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(),ctypes.byref(c),c.cb):return None
    return int(c.PeakWorkingSetSize)

def threshold(y,p):
    return float(max(np.linspace(.05,.95,91),key=lambda t:(f1_score(y,p>=t),t)))

def baselines(output):
    prep,rows,m=checked(output);parts=m['partitions'];ids=parts['train']
    texts=[rows[i]['text_redacted'] for i in ids];y=np.array([rows[i]['label'] for i in ids])
    folds=[(np.array(f['train']),np.array(f['validation'])) for f in m['inner_folds']]
    results={};hashes={}
    for name in fair.NAMES:
        run=output/name
        if (run/'freeze.json').exists():
            frozen=load(run/'freeze.json')
            for f,h in frozen['files'].items():
                if fair.digest(run/f)!=h:raise ValueError('Completed model changed')
            results[name]=frozen['selection'];hashes.update({name+'/'+f:h for f,h in frozen['files'].items()});continue
        run.mkdir(exist_ok=True)
        started=time.perf_counter();cpu=time.process_time()
        pipe,trials,chosen=fair.tune(texts,y,folds,name);v=pipe['tfidf'];model=pipe['classifier']
        def part(key):
            ii=parts[key];return v.transform([rows[i]['text_redacted'] for i in ii]),np.array([rows[i]['label'] for i in ii])
        xc,yc=part('calibration');cal=LogisticRegression(random_state=fair.SEED).fit(margin(model,xc).reshape(-1,1),yc)
        xv,yv=part('validation');p=cal.predict_proba(margin(model,xv).reshape(-1,1))[:,1];t=threshold(yv,p)
        export=export_linear(v,model,cal,t,synthetic=False)
        export.update(model_version=f'expanded-20261005-{name}-{prep["dataset_sha256"][:8]}',evaluation_status='preliminary_retrospective',label_status='inherited_unconfirmed',
            protocol_sha256=prep['protocol_sha256'],dataset_sha256=prep['dataset_sha256'],split_sha256=prep['split_sha256'],
            positive_class='suspicious',threshold_comparison='greater_or_equal',score_transform='fitted_sigmoid',calibration_fit_partition='calibration',
            threshold_fit_partition='validation',automatic_warnings_approved=False,preprocessing=dict(version='sg-ascii-v1',ngram_range=[1,1],idf='training-only smooth IDF',normalization='l2'))
        if screen(export['vocabulary'])['identifier_pattern_features']:raise ValueError('Vocabulary screen failed')
        write_json(run/'model.json',export)
        (run/'research-model.pkl').write_bytes(pickle.dumps(dict(vectorizer=v,model=model,calibrator=cal,threshold=t,condition='deployment')))
        results[name]=dict(chosen_parameter=chosen,trials=trials,threshold=t,validation_f1=float(f1_score(yv,p>=t)),model_version=export['model_version'],
            seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu,process_peak_working_set_bytes=peak_memory(),resource_note='process cumulative peak working set; CPU fitting',human_review='pending')
        files={f:fair.digest(run/f) for f in ('model.json','research-model.pkl')};hashes.update({name+'/'+f:h for f,h in files.items()})
        write_json(run/'freeze.json',dict(files=files,selection=results[name],preparation_sha256=fair.digest(output/'preparation.json')))
        (run/'review.properties').write_text(f'algorithm={name}\nmodelVersion={export["model_version"]}\nsha256={files["model.json"]}\nreviewKind=automated-pattern-screen\nhumanReview=not_recorded\nreviewReference=expanded-comparison-20261005\nprotocolSha256={prep["protocol_sha256"]}\n')
        print(name,'frozen; training seconds',results[name]['seconds'],flush=True)
    write_json(output/'baseline-freeze.json',dict(validation=results,files=hashes,preparation=prep,test_opened=False))

def mbert(base,output):
    prep,rows,m=checked(output);run=output/'mbert';run.mkdir(exist_ok=True)
    if (run/'freeze.json').exists():raise ValueError('mBERT already frozen; preserve run')
    if fair.digest(base/'model.safetensors')!='876f584f15ebf14887dec17539c114bb99a032e96b9e72507a51c41e205337fc':raise ValueError('Base weights changed')
    if fair.digest(base/'vocab.txt')!='fe0fda7c425b48c516fc8f160d594c8022a0808447475c1a7c6d6479763f310c':raise ValueError('Tokenizer changed')
    torch,Model,Tokenizer,Adafactor=imports()
    if not torch.cuda.is_available():raise ValueError('CUDA unavailable')
    random.seed(SEED);np.random.seed(SEED);torch.manual_seed(SEED);torch.cuda.manual_seed_all(SEED)
    torch.use_deterministic_algorithms(True);torch.set_num_threads(4)
    tokenizer=Tokenizer.from_pretrained(base,local_files_only=True,do_lower_case=False)
    parts=m['partitions'];train_ids=parts['train']
    lengths=[len(tokenizer(rows[i]['text'],truncation=False)['input_ids']) for i in train_ids]
    length=min(256,max(64,int(math.ceil(float(np.percentile(lengths,95))/16)*16)))
    config=dict(model_id=BASE_ID,revision=REVISION,model_version=f'expanded-20261005-mbert-{prep["dataset_sha256"][:8]}',seed=SEED,epochs=2,wall_budget_seconds=2700,
        learning_rate=2e-5,optimizer='Adafactor',microbatch=1,gradient_accumulation=8,max_length=length,weight_decay=.01,
        dataset_sha256=prep['dataset_sha256'],split_sha256=prep['split_sha256'],case_view_sha256=prep['case_view_sha256'],protocol_sha256=prep['protocol_sha256'],
        code_sha256=fair.digest(Path(__file__)),dependency_lock_sha256=fair.digest(Path(__file__).parents[1]/'mbert-dependency-lock.txt'))
    if (run/'configuration.json').exists() and load(run/'configuration.json')!=config:raise ValueError('Resume configuration changed')
    write_json(run/'configuration.json',config)
    write_json(run/'length-audit.json',dict(records=len(lengths),p50=float(np.percentile(lengths,50)),p95=float(np.percentile(lengths,95)),maximum=max(lengths),
        selected_length=length,truncated_at_128=sum(n>128 for n in lengths),truncated_at_selected=sum(n>length for n in lengths)))
    model=Model.from_pretrained(base,num_labels=2,id2label={0:'ham',1:'smishing'},label2id={'ham':0,'smishing':1},local_files_only=True,use_safetensors=True,attn_implementation='eager').cuda()
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})
    optimizer=Adafactor(model.parameters(),lr=2e-5,relative_step=False,scale_parameter=False,warmup_init=False,weight_decay=.01)
    scaler=torch.amp.GradScaler('cuda');checkpoint=run/'resume.pt'
    epoch0=0;offset0=0;history=[];best=-1.;selected_epoch=None;elapsed_prior=0.
    if checkpoint.exists():
        state=torch.load(checkpoint,map_location='cpu',weights_only=False)
        model.load_state_dict(state['model']);optimizer.load_state_dict(state['optimizer']);scaler.load_state_dict(state['scaler'])
        for v in optimizer.state.values():
            for k,t in v.items():
                if torch.is_tensor(t):v[k]=t.cuda()
        torch.set_rng_state(state['rng']);torch.cuda.set_rng_state_all(state['cuda_rng'])
        epoch0=state['epoch'];offset0=state['offset'];history=state['history'];best=state['best'];selected_epoch=state['selected_epoch'];elapsed_prior=state['elapsed']
        del state
    started=time.monotonic()
    def encode(ids):
        return {k:v.cuda() for k,v in tokenizer([rows[i]['text'] for i in ids],max_length=length,truncation=True,padding='max_length',return_tensors='pt').items()}
    def logits(ids):
        model.eval();out=[]
        with torch.no_grad():
            for i in ids:out.append(model(**encode([i])).logits.float().cpu().numpy()[0])
        return np.array(out)
    def save(epoch,offset):
        pending=run/'resume.pending.pt'
        torch.save(dict(model=model.state_dict(),optimizer=optimizer.state_dict(),scaler=scaler.state_dict(),rng=torch.get_rng_state(),cuda_rng=torch.cuda.get_rng_state_all(),
            epoch=epoch,offset=offset,history=history,best=best,selected_epoch=selected_epoch,elapsed=elapsed_prior+time.monotonic()-started),pending)
        os.replace(pending,checkpoint)
    for epoch in range(epoch0,2):
        order=np.random.default_rng(SEED+epoch).permutation(train_ids).tolist();model.train();losses=[]
        for start in range(offset0 if epoch==epoch0 else 0,len(order),8):
            if elapsed_prior+time.monotonic()-started>2700:
                save(epoch,start);raise ValueError('Training budget exhausted; resumable state preserved')
            chunk=order[start:start+8];optimizer.zero_grad(set_to_none=True)
            for i in chunk:
                with torch.autocast('cuda',dtype=torch.float16):loss=model(**encode([i]),labels=torch.tensor([rows[i]['label']],device='cuda')).loss/len(chunk)
                scaler.scale(loss).backward();losses.append(float(loss.detach())*len(chunk))
            scaler.unscale_(optimizer);torch.nn.utils.clip_grad_norm_(model.parameters(),1.);scaler.step(optimizer);scaler.update()
            if (start+8)%200==0:
                save(epoch,start+8);print('mBERT epoch',epoch+1,'records',start+8,'/',len(order),flush=True)
        val=logits(parts['validation']);yv=np.array([rows[i]['label'] for i in parts['validation']]);ap=float(average_precision_score(yv,val[:,1]-val[:,0]))
        history.append(dict(epoch=epoch+1,validation_average_precision=ap,mean_training_loss=float(np.mean(losses)) if losses else None))
        if ap>best:
            best=ap;selected_epoch=epoch+1;model.save_pretrained(run/'selected',safe_serialization=True);tokenizer.save_pretrained(run/'selected')
        save(epoch+1,0);print('mBERT epoch',epoch+1,'validation AP',ap,flush=True)
    summary=dict(complete=True,epochs_completed=len(history),selected_epoch=selected_epoch,history=history,seconds=elapsed_prior+time.monotonic()-started,
        max_length=length,train_truncated=sum(n>length for n in lengths),trainable_parameters=sum(p.numel() for p in model.parameters() if p.requires_grad),
        gpu=torch.cuda.get_device_name(),peak_cuda_bytes=torch.cuda.max_memory_allocated(),peak_cuda_reserved_bytes=torch.cuda.max_memory_reserved(),process_peak_working_set_bytes=peak_memory(),torch=torch.__version__)
    write_json(run/'training-summary.json',summary)
    del model,optimizer;torch.cuda.empty_cache()
    model=Model.from_pretrained(run/'selected',local_files_only=True,attn_implementation='eager').cuda()
    xc=logits(parts['calibration']);yc=np.array([rows[i]['label'] for i in parts['calibration']])
    cal=LogisticRegression(random_state=SEED).fit((xc[:,1]-xc[:,0]).reshape(-1,1),yc)
    xv=logits(parts['validation']);yv=np.array([rows[i]['label'] for i in parts['validation']]);p=cal.predict_proba((xv[:,1]-xv[:,0]).reshape(-1,1))[:,1]
    write_json(run/'freeze.json',dict(configuration=config,max_length=length,selected_epoch=selected_epoch,threshold=threshold(yv,p),
        calibration=dict(method='sigmoid',a=float(cal.coef_[0,0]),b=float(cal.intercept_[0]),fit_partition='calibration',evaluated=False),
        files={str(f.relative_to(run)):fair.digest(f) for f in (run/'selected').iterdir() if f.is_file()},test_opened=False))
    print('mBERT frozen; seconds',summary['seconds'],flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['baselines','mbert']);p.add_argument('output',type=Path);p.add_argument('--base',type=Path)
    a=p.parse_args();baselines(a.output) if a.command=='baselines' else mbert(a.base,a.output)
