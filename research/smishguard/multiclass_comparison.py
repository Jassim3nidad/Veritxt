"""Controlled three-class 60/20/20 versus 80/20 experiment; no Android writes.

Stages seal input, membership and selections before exclusive final evaluation.
Private row ledgers/models stay under research/runs; report exports aggregates.
"""
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
import argparse
import importlib.metadata
import json
import pickle
import platform
import shutil
import sys
import warnings

import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
from threadpoolctl import threadpool_limits

from . import nb_comparison as legacy

SEED = 42
LABELS = {'ham': 0, 'smishing': 1, 'gambling_ad': 2}
NAMES = ['Ham', 'Smishing', 'Gambling']
GRID = {'svm': [.001, .01, .1, 1., 10., 100., 1000.],
        'nb': [.001, .01, .1, .5, 1., 2., 10.]}
ROOT = Path(__file__).resolve().parents[2]
SOURCE_FILES = [Path(__file__), Path(legacy.__file__)]
POLICY = dict(seed=SEED, labels=LABELS, grid=GRID, primary_metric='macro F1',
    tie_break='smaller C or alpha if selection macro F1 is exactly tied',
    eligible_sources=list(legacy.SOURCES), review_flagged='exclude, no relabeling',
    grouping='Unchanged nb_comparison.group_rows: supplied template_group, source-scoped sender/campaign/conversation, URL/number-stripped Unicode SequenceMatcher >=0.85 connected components',
    allocation='Joint 60/20/20 integer allocation; exact rounded row counts; class counts within one of target; minimize class-group count deviations, fixed seed tie-break',
    cv='5 deterministic StratifiedGroupKFold folds, shuffle=False; saved memberships; each fold fits a fresh full pipeline',
    tuning60='Single 20% validation portion, no refit on validation; CV not applicable',
    tuning80='Mean of five fold macro F1 scores; refit on all 80% after selection',
    features='Unchanged legacy.vectorizer: word TF-IDF 1-2 grams, lowercase, conservative English stopwords, raw TF, smooth IDF, L2',
    imbalance='No resampling or class weighting; NB empirical priors; both classifiers receive identical features',
    prediction='Native three-class argmax; no threshold tuning or calibration',
    history='Historically exposed corpus; held out within this run only, retrospective',
    interpretation='Size comparison also changes tuning procedure; cannot attribute all change solely to sample size',
    android_integration=False)


def save(path, obj):
    legacy.save(path, obj)


def load(path):
    return legacy.load(path)


def hashes(paths):
    return {str(p.resolve()): legacy.digest(p) for p in paths}


def clean(records):
    """Preserve recent source/review exclusions; admit all three explicit labels."""
    if len({r['id'] for r in records}) != len(records) or any(not r['id'] for r in records):
        raise ValueError('Missing or duplicate record IDs')
    buckets = defaultdict(list)
    for r in records:
        buckets[legacy.normalize(r['text']).casefold()].append(r)
    conflicts = {k for k, rr in buckets.items() if len({r['label'] for r in rr}) > 1}
    kept, ledger, seen = [], [], set()
    for r in records:
        text = legacy.normalize(r['text']); key = text.casefold(); reasons = []
        if r['label'] not in LABELS:
            raise ValueError('Unsupported class: '+r['label'])
        if r['needs_review'].lower() not in ('true', 'false'):
            raise ValueError('Unknown review flag')
        if r['source'] not in legacy.SOURCES:
            reasons.append('existing_source_scope_hold')
        if r['needs_review'].lower() == 'true':
            reasons.append('flagged_for_label_review')
        if not text or '\x00' in text or '\ufffd' in text or len(text) > 10000:
            reasons.append('empty_malformed_or_overlong')
        if key in conflicts:
            reasons.append('conflicting_normalized_labels')
        if not reasons:
            if key in seen:
                reasons.append('duplicate_normalized_text')
            else:
                kept.append(dict(r, text=text, original_label=r['label'], label=LABELS[r['label']]))
                seen.add(key)
        ledger.append(dict(id=r['id'], original_label=r['label'], reasons=reasons))
    if {r['label'] for r in kept} != set(range(3)):
        raise ValueError('All three classes must survive cleaning')
    audit = dict(input_records=len(records), retained_records=len(kept),
        raw_labels=dict(Counter(r['label'] for r in records)),
        retained_labels={NAMES[c]: sum(r['label'] == c for r in kept) for c in range(3)},
        raw_exact_duplicate_extra_rows=len(records)-len({r['text'] for r in records}),
        normalized_duplicate_extra_rows=len(records)-len(buckets), conflicting_normalized_groups=len(conflicts),
        exclusion_reason_counts=dict(Counter(v for r in ledger for v in r['reasons'])),
        excluded_records=sum(bool(r['reasons']) for r in ledger),
        missing_fields={k:sum(not str(r[k]).strip() for r in records) for k in records[0]},
        sources_after=dict(Counter(r['source'] for r in kept)),
        languages_after=dict(Counter(r['language'] for r in kept)),
        label_status='Inherited source/rule labels; not independently adjudicated',
        source_status='Retains existing three-source scope; does not certify source licensing or privacy')
    return kept, ledger, audit


def allocate(y, groups):
    """Balance class-associated group counts, without accessing text/model scores.

    Rounded row and class constraints are hard. No permissive fallback/seed search.
    Soft balancing avoids the historical objective that favored few giant groups.
    """
    unique = np.unique(groups); g = len(unique); n = len(y)
    members = [np.flatnonzero(groups == v) for v in unique]
    counts = np.array([[sum(y[ii] == c) for c in range(3)] for ii in members])
    presence = (counts > 0).astype(int)
    sizes = counts.sum(axis=1)
    held = int(np.ceil(n*.2)); targets = np.array([n-2*held, held, held])
    fractions = targets/n
    # Three assignment blocks, plus nine absolute deviations in class-group counts.
    nv = 3*g+9; rows = []; lo = []; hi = []
    def constraint(entries, lower, upper):
        rows.append(entries); lo.append(lower); hi.append(upper)
    for j in range(g):
        constraint({p*g+j:1 for p in range(3)}, 1, 1)
    for p in range(3):
        constraint({p*g+j:int(sizes[j]) for j in range(g)}, targets[p], targets[p])
        for c in range(3):
            target = fractions[p]*sum(y == c)
            constraint({p*g+j:int(counts[j,c]) for j in range(g)}, np.floor(target), np.ceil(target))
            # Enough independent class-bearing groups for subsequent CV.
            constraint({p*g+j:int(presence[j,c]) for j in range(g)}, 6 if p == 0 else 2, np.inf)
            desired = fractions[p]*presence[:,c].sum(); d = 3*g+p*3+c
            entries = {p*g+j:int(presence[j,c]) for j in range(g)}
            constraint(entries | {d:-1}, -np.inf, desired)
            constraint({k:-v for k,v in entries.items()} | {d:-1}, -np.inf, -desired)
    a = lil_matrix((len(rows), nv))
    for i, rr in enumerate(rows):
        for j,v in rr.items(): a[i,j] = v
    objective = np.zeros(nv)
    objective[:3*g] = np.random.default_rng(SEED).random(3*g)*1e-8/g
    for p in range(3):
        for c in range(3): objective[3*g+p*3+c] = 1/presence[:,c].sum()
    upper = np.r_[np.ones(3*g), np.full(9, np.inf)]
    result = milp(objective, integrality=np.r_[np.ones(3*g), np.zeros(9)],
        bounds=Bounds(np.zeros(nv), upper), constraints=LinearConstraint(a.tocsr(),lo,hi),
        options=dict(time_limit=120, mip_rel_gap=.001))
    if not result.success:
        raise ValueError('Grouped allocation infeasible or unproven within time limit; no fallback: '+result.message)
    assignment = np.rint(result.x[:3*g]).reshape(3,g)
    parts = {name:np.flatnonzero(np.isin(groups, unique[assignment[p].astype(bool)])).tolist()
        for p,name in enumerate(['train60','validation20','test20'])}
    return parts, dict(message=result.message, objective=float(result.fun),
        mip_gap=float(result.mip_gap), targets=targets.tolist(), class_tolerance='floor/ceil of proportional count')


def validate(y, texts, groups, parts, complete=True):
    flat = [i for ii in parts.values() for i in ii]
    if len(flat) != len(set(flat)) or (complete and set(flat) != set(range(len(y)))):
        raise ValueError('Partitions must be a disjoint complete cover')
    for name, ii in parts.items():
        if set(y[ii]) != {0,1,2}:
            raise ValueError('Partition lacks a class: '+name)
    overlaps = {}
    for (a, ii), (b, jj) in combinations(parts.items(), 2):
        entry = dict(records=len(set(ii)&set(jj)), groups=len(set(groups[ii])&set(groups[jj])),
            normalized_text=len({texts[i].casefold() for i in ii}&{texts[i].casefold() for i in jj}))
        if any(entry.values()): raise ValueError('Leakage: '+a+'/'+b)
        overlaps[a+'/'+b] = entry
    return overlaps


def folds_for(y, texts, groups, ids):
    ids = np.array(ids); folds = []
    for a,b in StratifiedGroupKFold(5, shuffle=False).split(ids, y[ids], groups[ids]):
        fold = dict(train=ids[a].tolist(), validation=ids[b].tolist())
        validate(y,texts,groups,fold,complete=False)
        folds.append(fold)
    coverage = Counter(i for f in folds for i in f['validation'])
    if set(coverage) != set(ids) or any(v != 1 for v in coverage.values()):
        raise ValueError('Incomplete CV validation coverage')
    return folds


def metrics(y, pred):
    report = classification_report(y,pred,labels=[0,1,2],target_names=NAMES,output_dict=True,zero_division=0)
    cm = confusion_matrix(y,pred,labels=[0,1,2])
    return dict(accuracy=float(accuracy_score(y,pred)), macro_precision=report['macro avg']['precision'],
        macro_recall=report['macro avg']['recall'], macro_f1=report['macro avg']['f1-score'],
        weighted_f1=report['weighted avg']['f1-score'], correct=int(np.trace(cm)),
        misclassified=int(cm.sum()-np.trace(cm)), smishing_as_ham=int(cm[1,0]),
        gambling_as_ham=int(cm[2,0]), ham_as_smishing=int(cm[0,1]), ham_as_gambling=int(cm[0,2]),
        confusion_matrix=cm.tolist(), per_class={name:report[name] for name in NAMES})


def pipeline(algorithm, value):
    model = LinearSVC(C=value,dual='auto',random_state=SEED,max_iter=20000) if algorithm == 'svm' else MultinomialNB(alpha=value)
    return Pipeline([('tfidf',legacy.vectorizer()),('classifier',model)])


def fit(algorithm,value,texts,y,ids):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        model = pipeline(algorithm,value).fit([texts[i] for i in ids],y[ids])
    if caught: raise ValueError('Fitting warnings: '+'; '.join(str(w.message) for w in caught))
    if model.classes_.tolist() != [0,1,2]: raise ValueError('Class mapping changed')
    return model


def seal(output,name):
    files = [p for p in output.rglob('*') if p.is_file() and p.name not in ('prepare-seal.json','training-seal.json')]
    save(output/name, dict(files={p.relative_to(output).as_posix():legacy.digest(p) for p in files},
        sources=hashes(SOURCE_FILES)))


def verify(output,name):
    data = load(output/name)
    if data['sources'] != hashes(SOURCE_FILES): raise ValueError('Implementation changed')
    for path,sha in data['files'].items():
        if legacy.digest(output/path) != sha: raise ValueError('Frozen file changed: '+path)
    config = load(output/'configuration.json')
    if legacy.digest(config['dataset']) != config['input_identity']['zip_sha256']:
        raise ValueError('Original dataset changed')


def prepare(dataset, output):
    output = Path(output)
    if output.exists(): raise FileExistsError('Use a new private run directory')
    records,identity = legacy.read_dataset(dataset)
    rows,ledger,audit = clean(records)
    print('Dataset',audit['retained_labels'],'; computing near-template components...',flush=True)
    groups = legacy.group_rows(rows)
    texts = [r['text'] for r in rows]; y = np.array([r['label'] for r in rows])
    parts,allocation = allocate(y,groups)
    overlaps = validate(y,texts,groups,parts)
    training = sorted(parts['train60']+parts['validation20'])
    folds = folds_for(y,texts,groups,training)
    audit.update(groups=len(set(groups)), largest_group_sizes=sorted(Counter(groups).values(),reverse=True)[:10],
        class_bearing_groups={NAMES[c]:len(set(groups[y==c])) for c in range(3)},
        mixed_label_groups=sum(len(set(y[groups==g]))>1 for g in set(groups)),
        overlap_checks=overlaps, allocation=allocation,
        template_group_blank=sum(not r['template_group'] for r in rows),
        supplied_template_groups=len({r['template_group'] for r in rows}),
        multirow_components=sum(v>1 for v in Counter(groups).values()))
    allparts=dict(parts,train80=training)
    audit['partitions']={k:dict(records=len(ii),fraction=len(ii)/len(rows),groups=len(set(groups[ii])),
        **{NAMES[c]:int(sum(y[ii]==c)) for c in range(3)}) for k,ii in allparts.items()}
    audit['cv_folds']=[{k:dict(records=len(ii),groups=len(set(groups[ii])),
        **{NAMES[c]:int(sum(y[ii]==c)) for c in range(3)}) for k,ii in f.items()} for f in folds]
    output.mkdir(parents=True)
    (output/'code').mkdir()
    for source in SOURCE_FILES: shutil.copyfile(source,output/'code'/source.name)
    save(output/'dataset.json',rows); save(output/'cleaning-ledger.json',ledger)
    save(output/'audit.json',audit)
    save(output/'splits.json',dict(partitions=allparts,groups=groups.tolist(),cv=folds,seed=SEED))
    save(output/'configuration.json',dict(policy=POLICY,dataset=str(Path(dataset).resolve()),input_identity=identity,
        vectorizer=legacy.vectorizer().get_params() | {'dtype':'float64'},sources=hashes(SOURCE_FILES)))
    save(output/'environment.json',dict(python=sys.version,platform=platform.platform(),
        packages={p:importlib.metadata.version(p) for p in ['numpy','scipy','scikit-learn','pandas','matplotlib','joblib','threadpoolctl']}))
    seal(output,'prepare-seal.json')
    print('Frozen partitions:',audit['partitions'],flush=True)


def train(output):
    output = Path(output); verify(output,'prepare-seal.json')
    if (output/'selection.json').exists(): raise FileExistsError('Selection already exists')
    rows = load(output/'dataset.json'); split = load(output/'splits.json')
    texts = [r['text'] for r in rows]; y = np.array([r['label'] for r in rows])
    candidates = []; selections = []
    with threadpool_limits(limits=1):
        for size in (60,80):
            for algorithm,grid in GRID.items():
                scores = []
                for value in grid:
                    trials = split['cv'] if size == 80 else [dict(train=split['partitions']['train60'],validation=split['partitions']['validation20'])]
                    fold_scores = []
                    for fold in trials:
                        model = fit(algorithm,value,texts,y,fold['train'])
                        pred = model.predict([texts[i] for i in fold['validation']])
                        fold_scores.append(float(f1_score(y[fold['validation']],pred,labels=[0,1,2],average='macro',zero_division=0)))
                    item = dict(size=size,algorithm=algorithm,parameter='C' if algorithm=='svm' else 'alpha',value=value,
                        selection_macro_f1=float(np.mean(fold_scores)),fold_scores=fold_scores,
                        cv_mean=float(np.mean(fold_scores)) if size==80 else None,
                        cv_std=float(np.std(fold_scores,ddof=0)) if size==80 else None,
                        validation_macro_f1=fold_scores[0] if size==60 else None)
                    scores.append(item); candidates.append(item)
                best = sorted(scores,key=lambda r:(-r['selection_macro_f1'],r['value']))[0]
                ids = split['partitions']['train'+str(size)]
                model = fit(algorithm,best['value'],texts,y,ids)
                name = algorithm+'-'+str(size)
                (output/(name+'.pkl')).write_bytes(pickle.dumps(model,protocol=5))
                selected = dict(best,id=name,training_records=len(ids),features=len(model['tfidf'].vocabulary_))
                selections.append(selected)
                print('Selected',name,best['parameter'],best['value'],'selection macro F1',best['selection_macro_f1'],flush=True)
    save(output/'tuning-results.json',candidates)
    save(output/'selection.json',selections)
    verify(output,'prepare-seal.json'); seal(output,'training-seal.json')
    print('All four models frozen. Test text has not been transformed.',flush=True)


def cluster_difference(y, first, second, groups, repetitions=2000):
    """Paired, whole-group bootstrap; fixed predictions, no refitting/retuning.

    Only replicates retaining all three true classes contribute. This is a
    conditional descriptive interval, not a prospective significance claim.
    """
    unique = np.unique(groups)
    tables = []
    for g in unique:
        ii = np.flatnonzero(groups==g)
        tables.append([confusion_matrix(y[ii],pred[ii],labels=[0,1,2]) for pred in (first,second)])
    tables = np.asarray(tables)
    rng = np.random.default_rng(SEED); differences = []
    def macro(cm):
        denom = cm.sum(axis=0)+cm.sum(axis=1)
        return np.divide(2*np.diag(cm),denom,out=np.zeros(3,dtype=float),where=denom!=0).mean()
    for _ in range(repetitions):
        cm = tables[rng.integers(0,len(unique),len(unique))].sum(axis=0)
        if np.all(cm[0].sum(axis=1)>0): differences.append(macro(cm[0])-macro(cm[1]))
    return dict(difference=float(f1_score(y,first,average='macro')-f1_score(y,second,average='macro')),
        percentile_95=np.quantile(differences,[.025,.975]).tolist() if differences else None,
        valid_replicates=len(differences),requested_replicates=repetitions,groups=len(unique),
        interpretation='Conditional paired cluster bootstrap; shared fixed fits, inherited labels, one split; excludes replicates missing a true class')


def evaluate(output):
    output = Path(output); verify(output,'training-seal.json')
    with (output/'evaluation-started.json').open('x',encoding='utf-8') as f:
        json.dump(dict(selection_sha256=legacy.digest(output/'selection.json')),f)
    rows = load(output/'dataset.json'); split = load(output/'splits.json')
    ids = split['partitions']['test20']; y = np.array([rows[i]['label'] for i in ids])
    results = []; predictions = {}
    for selection in load(output/'selection.json'):
        name = selection['id']
        model = pickle.loads((output/(name+'.pkl')).read_bytes())
        pred = model.predict([rows[i]['text'] for i in ids])
        predictions[name] = pred
        save(output/(name+'-predictions.json'),dict(indices=ids,labels=y.tolist(),predictions=pred.tolist()))
        results.append(dict(selection,test=metrics(y,pred)))
        print(name,'test macro F1',results[-1]['test']['macro_f1'],flush=True)
    groups = np.array(split['groups'])[ids]
    uncertainty = {a+' minus '+b:cluster_difference(y,predictions[a],predictions[b],groups)
        for a,b in [('svm-80','nb-80'),('svm-60','nb-60'),('svm-80','svm-60'),('nb-80','nb-60')]}
    save(output/'test-results.json',dict(results=results,uncertainty=uncertainty))
    verify(output,'training-seal.json')


def report(output,destination):
    output, destination = Path(output),Path(destination)
    verify(output,'training-seal.json')
    data = load(output/'test-results.json'); audit = load(output/'audit.json')
    split = load(output/'splits.json'); rows = load(output/'dataset.json')
    for r in data['results']:
        pred = load(output/(r['id']+'-predictions.json'))
        if pred['indices'] != split['partitions']['test20'] or pred['labels'] != [rows[i]['label'] for i in pred['indices']]:
            raise ValueError('Test records changed')
        if metrics(pred['labels'],pred['predictions']) != r['test']: raise ValueError('Metric recomputation failed')
    destination.mkdir(parents=True,exist_ok=True)
    save(destination/'results.json',dict(data,audit=audit,configuration=load(output/'configuration.json'),
        environment=load(output/'environment.json'),training_seal_sha256=legacy.digest(output/'training-seal.json')))
    dist = []
    for name,counts in [('raw',audit['raw_labels']),('eligible',audit['retained_labels'])]:
        for c,label in enumerate(NAMES):
            count = counts[list(LABELS)[c]] if name=='raw' else counts[label]
            dist.append(dict(partition=name,label=label,records=count,fraction=count/(audit['input_records'] if name=='raw' else audit['retained_records'])))
    for name,p in audit['partitions'].items():
        for label in NAMES: dist.append(dict(partition=name,label=label,records=p[label],fraction=p[label]/p['records']))
    pd.DataFrame(dist).to_csv(destination/'dataset-distribution.csv',index=False)
    pd.DataFrame([dict(partition=k,**v) for k,v in audit['partitions'].items()]).to_csv(destination/'partitions.csv',index=False)
    records = []; perclass = []
    for r in data['results']:
        records.append(dict(id=r['id'],training_percent=r['size'],algorithm=r['algorithm'],parameter=r['parameter'],value=r['value'],
            cv_mean=r['cv_mean'],cv_std=r['cv_std'],validation_macro_f1=r['validation_macro_f1'],
            **{k:v for k,v in r['test'].items() if k not in ('per_class','confusion_matrix')}))
        for name,v in r['test']['per_class'].items(): perclass.append(dict(id=r['id'],label=name,**v))
        pd.DataFrame(r['test']['confusion_matrix'],index=NAMES,columns=NAMES).rename_axis('Actual / Predicted').to_csv(destination/('confusion-'+r['id']+'.csv'))
    frame = pd.DataFrame(records); frame.to_csv(destination/'comparison-all.csv',index=False)
    for size in (60,80): frame[frame.training_percent==size].to_csv(destination/('comparison-'+str(size)+'.csv'),index=False)
    pd.DataFrame(perclass).to_csv(destination/'per-class.csv',index=False)
    tuning = load(output/'tuning-results.json')
    pd.DataFrame([{k:v for k,v in r.items() if k!='fold_scores'} | {'fold_'+str(i+1):v for i,v in enumerate(r['fold_scores'])} for r in tuning]).to_csv(destination/'tuning-all.csv',index=False)
    pd.DataFrame([dict(algorithm=r['algorithm'],parameter=r['parameter'],value=r['value'],mean=r['cv_mean'],std_population=r['cv_std'],
        **{'fold_'+str(i+1):v for i,v in enumerate(r['fold_scores'])}) for r in tuning if r['size']==80]).to_csv(destination/'cross-validation.csv',index=False)
    save(destination/'uncertainty.json',data['uncertainty'])
    plots(destination,data['results'])
    save(output/'verification.json',dict(all_test_metrics_recomputed=True,shared_test_membership=True,
        source_and_training_hashes_verified=True,report_hashes={p.name:legacy.digest(p) for p in destination.iterdir() if p.is_file()}))
    print(frame.to_string(index=False),flush=True)


def plots(destination,results):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    titles = [r['algorithm'].upper()+' '+str(r['size'])+'%' for r in results]
    colors = ['#236484','#d77932','#236484','#d77932']
    for metric in ('accuracy','macro_f1'):
        fig,ax = plt.subplots(figsize=(8,5),layout='constrained')
        bars = ax.bar(titles,[r['test'][metric]*100 for r in results],color=colors)
        ax.bar_label(bars,fmt='%.2f%%',padding=4); ax.set_ylim(0,110)
        ax.set_ylabel(metric.replace('_',' ').title()+' (%)'); ax.set_title('VeriTxt: shared held-out three-class test')
        fig.savefig(destination/(metric+'.png'),dpi=180); plt.close(fig)
    fig,ax = plt.subplots(figsize=(10,5),layout='constrained'); x = np.arange(3); width=.2
    for i,r in enumerate(results):
        bars=ax.bar(x+(i-1.5)*width,[r['test']['per_class'][c]['f1-score']*100 for c in NAMES],width,label=titles[i])
        ax.bar_label(bars,fmt='%.1f',fontsize=8,padding=3)
    ax.set_xticks(x,NAMES); ax.set_ylim(0,114); ax.set_ylabel('F1-score (%)'); ax.legend(ncols=4,loc='upper center')
    ax.set_title('Per-class F1: identical test records'); fig.savefig(destination/'per-class-f1.png',dpi=180); plt.close(fig)
    fig,axs=plt.subplots(2,2,figsize=(11,9),layout='constrained')
    for ax,r,title in zip(axs.flat,results,titles):
        cm=np.array(r['test']['confusion_matrix']); ax.imshow(cm,cmap='Blues',vmin=0,vmax=max(cm.max(),1))
        for i in range(3):
            for j in range(3): ax.text(j,i,str(cm[i,j]),ha='center',va='center',color='white' if cm[i,j]>cm.max()/2 else 'black')
        ax.set_xticks(range(3),NAMES); ax.set_yticks(range(3),NAMES); ax.set_xlabel('Predicted'); ax.set_ylabel('Actual'); ax.set_title(title)
    fig.savefig(destination/'confusion-matrices.png',dpi=180); plt.close(fig)
    for r,title in zip(results,titles):
        fig,ax=plt.subplots(figsize=(5,4),layout='constrained'); cm=np.array(r['test']['confusion_matrix'])
        ax.imshow(cm,cmap='Blues')
        for i in range(3):
            for j in range(3): ax.text(j,i,str(cm[i,j]),ha='center',va='center',color='white' if cm[i,j]>cm.max()/2 else 'black')
        ax.set_xticks(range(3),NAMES); ax.set_yticks(range(3),NAMES); ax.set_xlabel('Predicted'); ax.set_ylabel('Actual'); ax.set_title(title)
        fig.savefig(destination/('confusion-'+r['id']+'.png'),dpi=180); plt.close(fig)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['prepare','train','evaluate','report','run'])
    parser.add_argument('output',type=Path)
    parser.add_argument('--dataset',type=Path)
    parser.add_argument('--report-dir',type=Path)
    args=parser.parse_args()
    if args.stage in ('prepare','run'):
        if args.dataset is None: parser.error('--dataset required')
        prepare(args.dataset,args.output)
    if args.stage in ('train','run'): train(args.output)
    if args.stage in ('evaluate','run'): evaluate(args.output)
    if args.stage in ('report','run'):
        if args.report_dir is None: parser.error('--report-dir required')
        report(args.output,args.report_dir)


if __name__=='__main__': main()
