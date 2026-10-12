"""Fixed-setting retrospective baselines, equal voting and strictly OOF stacking.

Run audit, train, freeze, then evaluate. All private artifacts live in a new run.
Historical artifacts are read-only; no tuning functions are called.
"""
import argparse
from collections import Counter
from itertools import combinations
import json
from pathlib import Path
import pickle
import platform
import shutil
import subprocess
import time

import numpy as np
import scipy
from scipy.special import softmax
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.pipeline import Pipeline

from . import fair_compare as fair
from . import ensemble_mbert as bert
from .evaluate import metrics
from .expanded_train import checked
from .preprocessing import normalize
from .train import margin, write_json

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT/'docs/ensemble-comparison-protocol-20261011.md'
NAMES = ('lr', 'svm', 'nb', 'mbert')
STACKS = (('lr','svm','nb'), ('mbert','svm','nb'))


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def dump(path, obj):
    path.write_bytes(pickle.dumps(obj))


def unpickle(path):
    # Only locally generated artifacts with hashes verified by this experiment.
    return pickle.loads(path.read_bytes())


def probability(values, n=None):
    p = np.asarray(values, dtype=float)
    if p.ndim != 2 or p.shape[1] != 2 or (n is not None and len(p) != n):
        raise ValueError('Expected two probability columns on identical records')
    if not np.isfinite(p).all() or ((p < 0)|(p > 1)).any() or not np.allclose(p.sum(axis=1),1,rtol=0,atol=1e-6):
        raise ValueError('Invalid class probabilities')
    return p


def predict_probability(model, x):
    if list(model.classes_) != [0,1]:
        raise ValueError('Class probability orientation must be ham=0, smishing=1')
    return probability(model.predict_proba(x), len(x) if isinstance(x,list) else x.shape[0])


def vote(probabilities=None, predictions=None):
    if probabilities is not None:
        arrays = [probability(p) for p in probabilities]
        if not arrays or any(p.shape != arrays[0].shape for p in arrays):
            raise ValueError('Voting requires aligned probabilities')
        p = np.mean(arrays,axis=0)[:,1]
        return p, (p > .5).astype(int), 'soft'
    values = np.asarray(predictions)
    if values.ndim != 2 or not len(values) or not np.isin(values,[0,1]).all():
        raise ValueError('Hard voting requires binary predictions')
    p = np.mean(values,axis=0)
    return p, (p > .5).astype(int), 'hard'


def measure(y, p, threshold=.5, strict=True):
    # nextafter implements the documented equality-to-ham rule using shared >= metrics.
    threshold = float(np.nextafter(threshold,1)) if strict else threshold
    result = metrics(y,p,threshold)
    result['macro_f1'] = float(f1_score(y,np.asarray(p)>=threshold,labels=[0,1],average='macro',zero_division=0))
    return result


def validate_folds(folds, y, groups):
    covered = np.zeros(len(y),dtype=int)
    universe = set(range(len(y)))
    for a,b in folds:
        if len(a)!=len(set(a)) or len(b)!=len(set(b)) or set(a)&set(b) or set(a)|set(b)!=universe:
            raise ValueError('Fold indices must be a disjoint complete partition')
        if set(groups[a])&set(groups[b]):
            raise ValueError('Fold group leakage')
        if any(set(y[ii])!={0,1} for ii in (a,b)):
            raise ValueError('Both labels required in each fold')
        covered[b] += 1
    if not np.all(covered == 1):
        raise ValueError('Every OOF row must be predicted exactly once')


def make_pipe(name, value):
    return Pipeline([('tfidf',fair.vectorizer()),('classifier',fair.classifier(name,value))])


def fit_svm_calibrator(texts, y, groups, value, folds=None):
    """Every sigmoid-fitting margin is OOF, including TF-IDF fitting."""
    folds = fair.training_folds(y,groups) if folds is None else folds
    validate_folds(folds,y,groups)
    raw = np.full(len(y),np.nan)
    fits = []
    for a,b in folds:
        pipe = make_pipe('svm',value).fit([texts[i] for i in a],y[a])
        raw[b] = pipe.decision_function([texts[i] for i in b])
        fits.append(dict(train=a.tolist(),validation=b.tolist(),pipeline=pipe))
    calibrator = LogisticRegression(random_state=fair.SEED).fit(raw.reshape(-1,1),y)
    return calibrator, raw, fits


def audit(source, output, base):
    prep, rows, manifest = checked(source)
    freeze = load(source/'baseline-freeze.json')
    for file,h in freeze['files'].items():
        if fair.digest(source/file)!=h:
            raise ValueError('Historical baseline artifact changed')
    mf = load(source/'mbert/freeze.json')
    for file,h in mf['files'].items():
        if fair.digest(source/'mbert'/file)!=h:
            raise ValueError('Historical mBERT artifact changed')
    if fair.digest(base/'model.safetensors') != '876f584f15ebf14887dec17539c114bb99a032e96b9e72507a51c41e205337fc':
        raise ValueError('mBERT base weights changed')
    if fair.digest(base/'vocab.txt') != 'fe0fda7c425b48c516fc8f160d594c8022a0808447475c1a7c6d6479763f310c':
        raise ValueError('mBERT tokenizer changed')
    parts, groups = manifest['partitions'],np.array(manifest['groups'])
    ids = [i for indices in parts.values() for i in indices]
    if len(ids)!=len(rows) or set(ids)!=set(range(len(rows))) or len({r['id'] for r in rows})!=len(rows):
        raise ValueError('Partition coverage or ID uniqueness failure')
    overlap = {}
    exact = {}
    for a,b in combinations(parts,2):
        overlap[a+'-'+b] = len(set(groups[parts[a]])&set(groups[parts[b]]))
        exact[a+'-'+b] = len({rows[i]['text_redacted'] for i in parts[a]}&{rows[i]['text_redacted'] for i in parts[b]})
    if any(overlap.values()) or any(exact.values()):
        raise ValueError('Cross-partition group or normalized text overlap')
    case = load(source/'case-view.json')
    if len(case)!=len(rows) or any(r['label'] not in (0,1) or normalize(r['text'])!=r['text_redacted'] or
            (r['id'],r['text'],r['label'])!=(c['id'],c['text'],c['label']) for r,c in zip(rows,case)):
        raise ValueError('Case view, label, or normalization mismatch')
    train = parts['train']
    y = np.array([rows[i]['label'] for i in train])
    folds = [(np.array(f['train']),np.array(f['validation'])) for f in manifest['inner_folds']]
    validate_folds(folds,y,groups[train])
    labels_by_text = {}
    for r in rows:
        labels_by_text.setdefault(r['text_redacted'],set()).add(r['label'])
    if any(len(v)>1 for v in labels_by_text.values()):
        raise ValueError('Conflicting normalized labels')
    texts = [rows[i]['text_redacted'] for i in train]
    fresh = fair.vectorizer().fit(texts)
    fitted_audit = {}
    for name in fair.NAMES:
        old = unpickle(source/name/'research-model.pkl')
        v, model = old['vectorizer'],old['model']
        x = v.transform(texts)
        if list(model.classes_) != [0,1] or list(old['calibrator'].classes_) != [0,1]:
            raise ValueError('Reversed labels')
        if v.vocabulary_!=fresh.vocabulary_ or not np.array_equal(v.idf_,fresh.idf_):
            raise ValueError('Historical vocabulary or IDF does not match training-only fit')
        if x.data.min()<0:
            raise ValueError('Negative NB input')
        fitted_audit[name] = dict(classes=model.classes_.tolist(),training_only_vocabulary_exact=True,
            training_only_idf_exact=True,feature_count=len(v.vocabulary_),nonnegative=True,
            chosen_parameter=freeze['validation'][name]['chosen_parameter'],threshold=old['threshold'])
    # No test predictions or metrics accessed during audit/selection.
    output.mkdir(parents=True,exist_ok=False)
    for name in ('dataset.json','case-view.json','splits.json','preparation.json','exposure-summary.json'):
        shutil.copy2(source/name,output/name)
    shutil.copy2(PROTOCOL,output/'protocol.md')
    code = output/'code'
    code.mkdir()
    for path in Path(__file__).parent.glob('*.py'):
        shutil.copy2(path,code/path.name)
    snapshots = {str(p.relative_to(output)):fair.digest(p) for p in code.iterdir()}
    config = dict(source=str(source.resolve()),base=str(base.resolve()),primary_metric='smishing_f1',
        protocol_sha256=fair.digest(PROTOCOL),dataset_sha256=prep['dataset_sha256'],split_sha256=prep['split_sha256'],
        baseline_parameters={n:freeze['validation'][n]['chosen_parameter'] for n in fair.NAMES},
        baseline_thresholds={n:freeze['validation'][n]['threshold'] for n in fair.NAMES},
        mbert_threshold=mf['threshold'],baseline_seed=fair.SEED,mbert_seed=bert.SEED,
        ensemble_threshold=.5,tie_class=0,weights='equal',meta=dict(C=1.,solver='lbfgs',max_iter=2000,random_state=fair.SEED),
        source_freeze_sha256=fair.digest(source/'baseline-freeze.json'),source_mbert_freeze_sha256=fair.digest(source/'mbert/freeze.json'),
        code_sha256=snapshots,versions=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,sklearn=sklearn.__version__),
        prior_test_opened=(source/'internal-test-started.json').exists(),status='retrospective; inherited unconfirmed labels')
    write_json(output/'configuration.json',config)
    write_json(output/'audit.json',dict(records=len(rows),partitions=prep['partition_support'],group_overlap=overlap,
        normalized_text_overlap=exact,normalized_label_conflicts=0,view_identity=True,folds_valid=True,
        baselines=fitted_audit,exposure=load(source/'exposure-summary.json'),
        confirmed_current_classification_bugs=[],historical_issue='Pre-vectorized CV in supplied model_evidence; current pipeline already fits TF-IDF within folds'))
    write_json(output/'split-identifiers.json',{k:[rows[i]['id'] for i in ii] for k,ii in parts.items()})
    (output/'environment.txt').write_text(subprocess.check_output([__import__('sys').executable,'-m','pip','freeze'],text=True),encoding='utf-8')
    write_json(output/'preflight-seal.json',dict(files={str(p.relative_to(output)):fair.digest(p) for p in output.rglob('*') if p.is_file()}))
    print('Audit passed; fixed protocol and inputs sealed before refitting.',flush=True)


def context(output):
    for file,h in load(output/'preflight-seal.json')['files'].items():
        if fair.digest(output/file)!=h:
            raise ValueError('Sealed preparation changed: '+file)
    cfg = load(output/'configuration.json')
    for name,h in cfg['code_sha256'].items():
        if fair.digest(Path(__file__).parent/Path(name).name)!=h:
            raise ValueError('Training code changed after protocol seal: '+name)
    return cfg,load(output/'dataset.json'),load(output/'splits.json')


def train_classical(output):
    cfg,rows,m = context(output)
    parts = m['partitions']
    train = parts['train']
    texts = [rows[i]['text_redacted'] for i in train]
    y = np.array([rows[i]['label'] for i in train])
    groups = np.array(m['groups'])[train]
    folds = [(np.array(f['train']),np.array(f['validation'])) for f in m['inner_folds']]
    folder = output/'classical'
    folder.mkdir(exist_ok=False)
    baselines, timings, diagnostics, native_times = {},{},{},{}
    def part(key):
        return [rows[i]['text_redacted'] for i in parts[key]],np.array([rows[i]['label'] for i in parts[key]])
    xc,yc = part('calibration')
    xv,yv = part('validation')
    for name in fair.NAMES:
        start = time.perf_counter()
        pipe = make_pipe(name,cfg['baseline_parameters'][name]).fit(texts,y)
        native_times[name] = time.perf_counter()-start
        cal = LogisticRegression(random_state=fair.SEED).fit(pipe_margin(pipe,xc).reshape(-1,1),yc)
        timings[name] = time.perf_counter()-start
        baselines[name] = dict(pipeline=pipe,calibrator=cal,threshold=cfg['baseline_thresholds'][name])
        dump(folder/(name+'.pkl'),baselines[name])
        p = predict_probability(cal,pipe_margin(pipe,xv).reshape(-1,1))[:,1]
        old = unpickle(Path(cfg['source'])/name/'research-model.pkl')
        oldp = predict_probability(old['calibrator'],margin(old['model'],old['vectorizer'].transform(xv)).reshape(-1,1))[:,1]
        diagnostics[name] = dict(preserved_threshold=measure(yv,p,baselines[name]['threshold'],False),
            calibrated_fixed_half=measure(yv,p,.5,False),max_validation_probability_difference_from_original=float(np.max(abs(p-oldp))),
            raw_margin_average_precision=float(__import__('sklearn.metrics',fromlist=['average_precision_score']).average_precision_score(yv,pipe_margin(pipe,xv))))
        if name!='svm':
            diagnostics[name]['native_fixed_half'] = measure(yv,predict_probability(pipe,xv)[:,1],.5,False)
        print('Refitted baseline',name,'seconds',timings[name],flush=True)
    write_json(folder/'baseline-timing.json',timings)
    write_json(folder/'native-timing.json',native_times)
    write_json(output/'validation-diagnostics.json',diagnostics)
    oof = {n:np.full(len(y),np.nan) for n in fair.NAMES}
    raw_svm = np.full(len(y),np.nan)
    costs = {n:0. for n in fair.NAMES}
    calibration_seconds = 0.
    for k,(a,b) in enumerate(folds):
        fit_texts = [texts[i] for i in a]
        held_texts = [texts[i] for i in b]
        artifacts = {}
        for name in fair.NAMES:
            start = time.perf_counter()
            pipe = make_pipe(name,cfg['baseline_parameters'][name]).fit(fit_texts,y[a])
            if name=='svm':
                raw_svm[b] = pipe.decision_function(held_texts)
                calibration_seconds += time.perf_counter()-start
                cal,raw,nested = fit_svm_calibrator(fit_texts,y[a],groups[a],cfg['baseline_parameters'][name])
                oof[name][b] = predict_probability(cal,raw_svm[b].reshape(-1,1))[:,1]
                artifacts[name] = dict(pipeline=pipe,calibrator=cal,nested_fits=nested,calibration_oof_margins=raw)
            else:
                oof[name][b] = predict_probability(pipe,held_texts)[:,1]
                artifacts[name] = dict(pipeline=pipe)
            costs[name] += time.perf_counter()-start
        dump(folder/f'fold-{k}.pkl',dict(train=a,validation=b,components=artifacts))
    start = time.perf_counter()
    cal = LogisticRegression(random_state=fair.SEED).fit(raw_svm.reshape(-1,1),y)
    dump(folder/'svm-ensemble-calibrator.pkl',cal)
    sigmoid_seconds = time.perf_counter()-start
    # Reuse the outer fitted SVMs/margins; their fit/predict times above exclude
    # the nested sigmoid work required only by stacking.
    calibration_seconds += sigmoid_seconds
    if any(not np.isfinite(v).all() for v in oof.values()):
        raise ValueError('Incomplete OOF matrix')
    np.savez(output/'classical-oof.npz',**oof,raw_svm=raw_svm,labels=y,train_indices=np.array(train))
    write_json(folder/'oof-timing.json',dict(by_component=costs,svm_voting_calibration_seconds=calibration_seconds,final_sigmoid_seconds=sigmoid_seconds))
    print('Classical OOF and nested SVM calibration completed.',flush=True)


def pipe_margin(pipe,texts):
    return margin(pipe['classifier'],pipe['tfidf'].transform(texts))


def train_mbert(output):
    cfg,rows,m = context(output)
    parts = m['partitions']
    folder = output/'mbert'
    result = bert.fit(Path(cfg['base']),rows,parts['train'],folder,parts['validation'])
    start = time.perf_counter()
    logits,_ = bert.logits(folder/result['selected_path'],[rows[i]['text'] for i in parts['calibration']],result['max_length'],'cuda')
    cal = LogisticRegression(random_state=bert.SEED).fit((logits[:,1]-logits[:,0]).reshape(-1,1),[rows[i]['label'] for i in parts['calibration']])
    dump(folder/'calibrator.pkl',cal)
    write_json(folder/'calibration-timing.json',dict(seconds=time.perf_counter()-start))


def train_mbert_oof(output):
    cfg,rows,m = context(output)
    train = np.array(m['partitions']['train'])
    p = np.full(len(train),np.nan)
    timings = []
    for k,fold in enumerate(m['inner_folds']):
        a,b = train[fold['train']],train[fold['validation']]
        folder = output/f'mbert-oof-{k}'
        result = bert.fit(Path(cfg['base']),rows,a,folder)
        raw,seconds = bert.logits(folder/result['final_path'],[rows[i]['text'] for i in b],result['max_length'],'cuda')
        values = probability(softmax(raw,axis=1))[:,1]
        p[fold['validation']] = values
        np.savez(folder/'oof.npz',positions=np.array(fold['validation']),indices=b,probabilities=values)
        timings.append(dict(fit_seconds=result['seconds'],oof_prediction_seconds=seconds))
    if not np.isfinite(p).all():
        raise ValueError('Incomplete mBERT OOF matrix')
    np.savez(output/'mbert-oof.npz',mbert=p,train_indices=train)
    write_json(output/'mbert-oof-timing.json',dict(folds=timings,seconds=sum(t['fit_seconds']+t['oof_prediction_seconds'] for t in timings)))


def record_failure(output,experiment,error):
    path=output/'failures.json'
    records=load(path) if path.exists() else []
    records.append(dict(experiment=experiment,status='failed',error_type=type(error).__name__,reason=str(error)))
    write_json(path,records)
    print('FAILED',experiment,type(error).__name__,str(error),flush=True)


def train(output):
    context(output)
    with (output/'training-started.json').open('x') as f:
        json.dump(dict(started=time.time()),f)
    train_classical(output)
    try:
        train_mbert(output)
    except (RuntimeError,ImportError,ValueError,MemoryError) as error:
        record_failure(output,'mbert',error)
        return
    try:
        train_mbert_oof(output)
    except (RuntimeError,ImportError,ValueError,MemoryError) as error:
        record_failure(output,'mbert_stacking',error)


def infer_components(output, rows, indices):
    cfg=load(output/'configuration.json')
    texts=[rows[i]['text_redacted'] for i in indices]
    basep,ensemblep,elapsed={}, {}, {}
    for name in fair.NAMES:
        artifact=unpickle(output/'classical'/(name+'.pkl'))
        pipe=artifact['pipeline']
        start=time.perf_counter()
        x=pipe['tfidf'].transform(texts)
        raw=margin(pipe['classifier'],x)
        transform_seconds=time.perf_counter()-start
        start=time.perf_counter()
        basep[name]=predict_probability(artifact['calibrator'],raw.reshape(-1,1))[:,1]
        elapsed[name+'_baseline']=transform_seconds+time.perf_counter()-start
        if name=='svm':
            cal=unpickle(output/'classical/svm-ensemble-calibrator.pkl')
        start=time.perf_counter()
        if name=='svm':
            ensemblep[name]=predict_probability(cal,raw.reshape(-1,1))
        else:
            ensemblep[name]=predict_probability(pipe['classifier'],x)
        elapsed[name]=transform_seconds+time.perf_counter()-start
    if (output/'mbert/calibrator.pkl').exists():
        summary=load(output/'mbert/training-summary.json')
        raw,seconds=bert.logits(output/'mbert'/summary['selected_path'],[rows[i]['text'] for i in indices],summary['max_length'])
        cal=unpickle(output/'mbert/calibrator.pkl')
        start=time.perf_counter()
        basep['mbert']=predict_probability(cal,(raw[:,1]-raw[:,0]).reshape(-1,1))[:,1]
        elapsed['mbert_baseline']=seconds+time.perf_counter()-start
        start=time.perf_counter()
        ensemblep['mbert']=probability(softmax(raw,axis=1))
        elapsed['mbert']=seconds+time.perf_counter()-start
        if summary['final_path']!=summary['selected_path']:
            raw,seconds=bert.logits(output/'mbert'/summary['final_path'],[rows[i]['text'] for i in indices],summary['max_length'])
            ensemblep['mbert_stack']=probability(softmax(raw,axis=1))
            elapsed['mbert_stack']=seconds
        else:
            ensemblep['mbert_stack']=ensemblep['mbert']
            elapsed['mbert_stack']=elapsed['mbert']
    return basep,ensemblep,elapsed


def configurations(output):
    cfg=load(output/'configuration.json')
    available=list(fair.NAMES)
    if (output/'mbert/calibrator.pkl').exists():
        available.append('mbert')
    entries={}
    for name in NAMES:
        entries['standalone_'+name]=dict(family='standalone',components=[name],threshold=cfg['mbert_threshold'] if name=='mbert' else cfg['baseline_thresholds'][name],
            status='ready' if name in available else 'unavailable')
    for count in (2,3,4):
        for combo in combinations(NAMES,count):
            entries['voting_'+'_'.join(combo)]=dict(family='voting',components=list(combo),threshold=.5,weights=[1/count]*count,
                voting='soft',status='ready' if set(combo)<=set(available) else 'unavailable')
    for combo in STACKS:
        ready=set(combo)<=set(available) and ('mbert' not in combo or (output/'mbert-oof.npz').exists())
        entries['stacking_'+'_'.join(combo)]=dict(family='stacking',components=list(combo),threshold=.5,
            status='ready' if ready else 'unavailable')
    for entry in entries.values():
        if entry['status']!='ready':
            entry['reason']='Required component or leakage-free OOF fit unavailable; see failures.json'
    return entries


def evaluate_entries(output,entries,y,basep,ensemblep,timings):
    results,predictions={},{}
    for key,entry in entries.items():
        if entry['status']!='ready':
            continue
        combo=entry['components']
        start=time.perf_counter()
        if entry['family']=='standalone':
            p=basep[combo[0]]
            seconds=timings[combo[0]+'_baseline']
        elif entry['family']=='voting':
            p,_,_=vote([ensemblep[n] for n in combo])
            seconds=sum(timings[n] for n in combo)+time.perf_counter()-start
        else:
            meta=unpickle(output/(key+'.pkl'))
            start=time.perf_counter()
            x=np.column_stack([ensemblep['mbert_stack' if n=='mbert' else n][:,1] for n in combo])
            p=predict_probability(meta,x)[:,1]
            seconds=sum(timings['mbert_stack' if n=='mbert' else n] for n in combo)+time.perf_counter()-start
        result=measure(y,p,entry['threshold'],entry['family']!='standalone')
        result.update(inference_seconds=seconds,records=len(y),inference_ms_per_record=1000*seconds/len(y))
        results[key]=result
        predictions[key]=dict(scores=p.tolist(),predictions=((p>=entry['threshold']) if entry['family']=='standalone' else (p>entry['threshold'])).astype(int).tolist())
    return results,predictions


def training_costs(output,entries,meta_times):
    base=load(output/'classical/baseline-timing.json')
    native=load(output/'classical/native-timing.json')
    oof=load(output/'classical/oof-timing.json')
    if (output/'mbert/calibrator.pkl').exists():
        base['mbert']=load(output/'mbert/training-summary.json')['seconds']+load(output/'mbert/calibration-timing.json')['seconds']
        native['mbert']=load(output/'mbert/training-summary.json')['seconds']
    costs={}
    for key,entry in entries.items():
        if entry['status']!='ready':
            continue
        combo=entry['components']
        seconds=sum((base if entry['family']=='standalone' else native)[n] for n in combo)
        if entry['family']=='voting' and 'svm' in combo:
            seconds+=oof['svm_voting_calibration_seconds']
        if entry['family']=='stacking':
            seconds+=sum(oof['by_component'][n] for n in combo if n!='mbert')
            seconds+=oof['final_sigmoid_seconds']+meta_times[key]
            if 'mbert' in combo:
                seconds+=load(output/'mbert-oof-timing.json')['seconds']
        costs[key]=seconds
    return costs


def freeze(output):
    cfg,rows,m=context(output)
    if (output/'selection.json').exists():
        raise ValueError('Selection already frozen')
    entries=configurations(output)
    oof=dict(np.load(output/'classical-oof.npz'))
    if (output/'mbert-oof.npz').exists():
        mb=dict(np.load(output/'mbert-oof.npz'))
        if not np.array_equal(mb['train_indices'],oof['train_indices']):
            raise ValueError('OOF record ordering mismatch')
        oof.update(mbert=mb['mbert'])
    expected=np.array([rows[i]['label'] for i in m['partitions']['train']])
    if not np.array_equal(oof['labels'],expected) or not np.array_equal(oof['train_indices'],m['partitions']['train']):
        raise ValueError('Meta-training rows must be the original training partition')
    meta_times={}
    for key,entry in entries.items():
        if entry['family']!='stacking' or entry['status']!='ready':
            continue
        x=np.column_stack([oof[n] for n in entry['components']])
        if not np.isfinite(x).all() or ((x<0)|(x>1)).any():
            raise ValueError('Invalid OOF meta features')
        start=time.perf_counter()
        meta=LogisticRegression(**cfg['meta']).fit(x,expected)
        meta_times[key]=time.perf_counter()-start
        dump(output/(key+'.pkl'),meta)
        np.savez(output/(key+'-meta-training.npz'),features=x,labels=expected,indices=oof['train_indices'])
    indices=m['partitions']['validation']
    basep,ensemblep,timings=infer_components(output,rows,indices)
    y=np.array([rows[i]['label'] for i in indices])
    results,predictions=evaluate_entries(output,entries,y,basep,ensemblep,timings)
    costs=training_costs(output,entries,meta_times)
    for key in results:
        results[key]['training_seconds']=costs[key]
    ranking=sorted(results,key=lambda key:(-results[key]['f1'],key))
    families={family:[k for k in ranking if entries[k]['family']==family] for family in ('standalone','voting','stacking')}
    write_json(output/'validation-results.json',results)
    write_json(output/'validation-predictions.json',dict(ids=[rows[i]['id'] for i in indices],labels=y.tolist(),predictions=predictions))
    write_json(output/'selection.json',dict(primary_metric='smishing_f1',entries=entries,ranking=ranking,
        by_family=families,selected=ranking[0],selected_by_family={k:v[0] if v else None for k,v in families.items()},
        training_seconds=costs,meta_training_seconds=meta_times,test_predictions_accessed=False,
        historical_test_already_exposed=cfg['prior_test_opened']))
    files={str(p.relative_to(output)):fair.digest(p) for p in output.rglob('*') if p.is_file() and p.name!='freeze.json'}
    write_json(output/'freeze.json',dict(files=files,selection_sha256=fair.digest(output/'selection.json')))
    print('All available configurations frozen. Validation selection:',ranking[0],flush=True)


def evaluate(output):
    context(output)
    for file,h in load(output/'freeze.json')['files'].items():
        if fair.digest(output/file)!=h:
            raise ValueError('Frozen model/configuration changed: '+file)
    with (output/'test-started.json').open('x') as f:
        json.dump(dict(freeze_sha256=fair.digest(output/'freeze.json')),f)
    rows,m=load(output/'dataset.json'),load(output/'splits.json')
    selection=load(output/'selection.json')
    indices=m['partitions']['test']
    basep,ensemblep,timings=infer_components(output,rows,indices)
    y=np.array([rows[i]['label'] for i in indices])
    results,predictions=evaluate_entries(output,selection['entries'],y,basep,ensemblep,timings)
    for key in results:
        results[key]['training_seconds']=selection['training_seconds'][key]
    write_json(output/'test-predictions.json',dict(ids=[rows[i]['id'] for i in indices],labels=y.tolist(),predictions=predictions))
    write_json(output/'test-results.json',dict(results=results,primary_metric='smishing_f1',selection=selection,
        descriptive_test_ranking=sorted(results,key=lambda k:(-results[k]['f1'],k)),
        status='Retrospective previously exposed test; no fitting or reselection using these results',
        dataset_sha256=fair.digest(output/'dataset.json'),split_sha256=fair.digest(output/'splits.json'),
        freeze_sha256=fair.digest(output/'freeze.json'),inference_device='CPU, torch threads=4; sequential batch, loading excluded'))
    print('Final retrospective test evaluation saved; no retuning.',flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['audit','train','freeze','evaluate'])
    p.add_argument('output',type=Path)
    p.add_argument('--source',type=Path)
    p.add_argument('--base',type=Path)
    a=p.parse_args()
    if a.command=='audit':
        audit(a.source,a.output,a.base)
    else:
        globals()[a.command](a.output)


if __name__=='__main__':
    main()
