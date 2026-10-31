"""NB memorization/shortcut audit with balanced group CV and purged sources.

Kept outside smishguard/ so its addition preserves the old all-module source
inventory. Never overwrites historical runs or installs an Android model.
"""
from collections import Counter
from pathlib import Path
import argparse
import importlib.metadata
import json
import pickle
import re
import shutil
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/'research'))
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score, accuracy_score
from sklearn.naive_bayes import MultinomialNB
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import Pipeline
from threadpoolctl import threadpool_limits
from smishguard import nb_comparison as n, holdout_8020 as h

SEED = 42
PROTOCOL = ROOT/'docs/nb-generalization-20261019/PROTOCOL.md'
SPECS = [dict(id='original-alpha-0.1', alpha=.1, reduced=False),
         dict(id='reduced-alpha-0.1', alpha=.1, reduced=True),
         dict(id='reduced-alpha-1', alpha=1., reduced=True)]
EMAIL = re.compile(r'(?iu)\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b')
NUMBER = re.compile(r'(?u)[₱$€£]?\s*\d+(?:[,.]\d+)*')


def reduced_text(text):
    text = EMAIL.sub(' ', n.URL.sub(' ', n.normalize(text)))
    return n.normalize(NUMBER.sub(' ', text)).lower()


def make_pipeline(spec):
    vec = n.vectorizer() if not spec['reduced'] else TfidfVectorizer(
        preprocessor=reduced_text, lowercase=False, token_pattern=r'(?u)\b\w+\b',
        stop_words=n.STOP_WORDS, ngram_range=(1,2), min_df=2, max_df=.95,
        max_features=20000, norm='l2', smooth_idf=True, sublinear_tf=False)
    return Pipeline([('tfidf',vec),('classifier',MultinomialNB(alpha=spec['alpha']))])


def measure(y, prediction, groups):
    y, prediction, groups = np.asarray(y), np.asarray(prediction), np.asarray(groups)
    tn,fp,fn,tp = [int(x) for x in confusion_matrix(y,prediction,labels=[0,1]).ravel()]
    counts = Counter(groups.tolist()); weights=np.array([1/counts[g] for g in groups])
    return dict(records=len(y),ham=tn+fp,smishing=fn+tp,groups=len(counts),
        accuracy=float(accuracy_score(y,prediction)),precision=float(precision_score(y,prediction,zero_division=0)),
        recall=float(recall_score(y,prediction,zero_division=0)),f1=float(f1_score(y,prediction,zero_division=0)),
        macro_f1=float(f1_score(y,prediction,labels=[0,1],average='macro',zero_division=0)),
        fpr=fp/(tn+fp) if tn+fp else None, fnr=fn/(fn+tp) if fn+tp else None,
        group_weighted_accuracy=float(accuracy_score(y,prediction,sample_weight=weights)),
        group_weighted_f1=float(f1_score(y,prediction,sample_weight=weights,zero_division=0)),
        confusion=dict(tn=tn,fp=fp,fn=fn,tp=tp),
        full_two_class_support=bool(tn+fp and fn+tp))


def balanced_folds(rows, groups, seed=SEED):
    """Five exact rounded 80/20 tests; hard group-count bounds, soft balance."""
    groups=np.asarray(groups); unique=np.unique(groups); k=5
    if len(unique)<25 or len(rows)!=len(groups):raise ValueError('Need at least 25 intact groups')
    y=np.array([r['label'] for r in rows])
    if set(y)!={0,1} or min(Counter(y).values())<k:raise ValueError('Need both classes in all folds')
    members=[np.flatnonzero(groups==g) for g in unique]
    size=np.array([len(ii) for ii in members]); pos=np.array([int(y[ii].sum()) for ii in members])
    target=np.full(k,len(rows)//k);target[:len(rows)%k]+=1
    ideal=target*y.mean();positive=np.floor(ideal).astype(int)
    for f in np.argsort(-(ideal-positive),kind='stable')[:int(y.sum()-positive.sum())]:positive[f]+=1
    metrics=[(size,target), (pos,positive)]
    source_metrics=[]
    for source in sorted({r['source'] for r in rows}):
        for label in (0,1):
            values=np.array([sum(rows[i]['source']==source and rows[i]['label']==label for i in ii) for ii in members])
            if values.sum():source_metrics.append((values,values.sum()/k))
    assignments=len(unique)*k;deviations=k+len(source_metrics)*k;variables=assignments+deviations
    records=[];lower=[];upper=[]
    def add(indices, values, lo, hi):
        records.append((indices,values));lower.append(lo);upper.append(hi)
    for g in range(len(unique)):add([g*k+f for f in range(k)],[1]*k,1,1)
    for values,targets in metrics:
        for f in range(k):add([g*k+f for g in range(len(unique))],values.tolist(),int(targets[f]),int(targets[f]))
    desired=len(unique)/k;min_groups=max(5,int(np.floor(desired*.8)));max_groups=int(np.ceil(desired*1.2))
    costs=np.zeros(variables);costs[:assignments]=np.random.default_rng(seed).random(assignments)*1e-6
    for f in range(k):
        cols=[g*k+f for g in range(len(unique))]
        add(cols,[1]*len(unique),min_groups,max_groups)
        d=assignments+f;costs[d]=100
        add(cols+[d],[1]*len(unique)+[-1],-np.inf,desired)
        add(cols+[d],[-1]*len(unique)+[-1],-np.inf,-desired)
    for j,(values,desired_source) in enumerate(source_metrics):
        for f in range(k):
            cols=[g*k+f for g in range(len(unique))];d=assignments+k+j*k+f;costs[d]=1/max(1,desired_source)
            add(cols+[d],values.tolist()+[-1],-np.inf,desired_source)
            add(cols+[d],(-values).tolist()+[-1],-np.inf,-desired_source)
    matrix=lil_matrix((len(records),variables),dtype=float)
    for i,(cols,values) in enumerate(records):matrix[i,cols]=values
    lb=np.zeros(variables);ub=np.r_[np.ones(assignments),np.full(deviations,np.inf)]
    # Fix the five largest components to different folds, independent of scores.
    for f,g in enumerate(sorted(range(len(unique)),key=lambda g:(-size[g],int(unique[g])))[:k]):lb[g*k+f]=ub[g*k+f]=1
    solved=milp(costs,integrality=np.r_[np.ones(assignments),np.zeros(deviations)],bounds=Bounds(lb,ub),
        constraints=LinearConstraint(matrix.tocsr(),lower,upper),options=dict(time_limit=45,mip_rel_gap=.01))
    if solved.x is None:raise ValueError('Balanced 80/20 allocation infeasible or timed out; no row-splitting fallback')
    x=np.rint(solved.x[:assignments]).reshape(-1,k)
    if np.max(np.abs(x-solved.x[:assignments].reshape(-1,k)))>1e-5 or not np.all(x.sum(axis=1)==1):raise ValueError('Nonintegral allocation')
    folds=[];cover=[]
    for f in range(k):
        test=np.flatnonzero(np.isin(groups,unique[x[:,f]==1])).tolist();train=np.flatnonzero(~np.isin(groups,unique[x[:,f]==1])).tolist()
        n.validate_split(rows,groups,dict(train=train,test=test))
        if len(test)!=target[f] or sum(y[test])!=positive[f] or not min_groups<=len(set(groups[test]))<=max_groups:raise ValueError('Allocation constraints failed')
        folds.append(dict(id='group-fold-'+str(f),scheme='group-cv',train=train,test=test));cover+=test
    if sorted(cover)!=list(range(len(rows))):raise ValueError('OOF must cover each row once')
    return folds,dict(status=int(solved.status),message=solved.message,optimal=bool(solved.success),
        target_rows=target.tolist(),target_positive=positive.tolist(),target_groups=len(unique)/k,
        minimum_groups=min_groups,maximum_groups=max_groups,objective='Group-count deviation first; source/class deviation second; seeded tie-break',
        no_model_scores_used=True)


def source_folds(rows,groups):
    groups=np.asarray(groups);folds=[]
    for j,source in enumerate(sorted({r['source'] for r in rows})):
        test=[i for i,r in enumerate(rows) if r['source']==source];related=set(groups[test])
        train=[i for i,r in enumerate(rows) if r['source']!=source and groups[i] not in related]
        if {rows[i]['label'] for i in train}!={0,1}:raise ValueError('Source complement lacks two training classes')
        if set(groups[train])&related:raise ValueError('Source/template leakage')
        folds.append(dict(id='source-fold-'+str(j),scheme='source-held-out',source=source,train=train,test=test,
            related_records_purged=len(rows)-len(train)-len(test)))
    return folds


def old_split_audit(rows, groups, old):
    parts=old['partitions'];train=parts['train'];test=parts['test'];sizes=Counter(np.asarray(groups)[test].tolist())
    vec=TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),min_df=2,max_features=30000)
    x=vec.fit_transform([n.template_key(rows[i]['text']) for i in train]);xt=vec.transform([n.template_key(rows[i]['text']) for i in test])
    distance,nearest=NearestNeighbors(n_neighbors=1,metric='cosine',algorithm='brute',n_jobs=1).fit(x).kneighbors(xt)
    similarity=np.clip(1-distance[:,0],0,1)
    return dict(test_records=len(test),test_groups=len(sizes),largest_test_group=max(sizes.values()),
        largest_test_group_fraction=max(sizes.values())/len(test),
        exact_casefold_overlap=len({rows[i]['text'].casefold() for i in train}&{rows[i]['text'].casefold() for i in test}),
        template_group_overlap=len(set(np.asarray(groups)[train])&set(np.asarray(groups)[test])),
        near_similarity=dict(method='Nearest training character TF-IDF cosine, URL/number-normalized text; heuristic, not campaign identity',
            median=float(np.median(similarity)),p95=float(np.quantile(similarity,.95)),at_least_090=int((similarity>=.9).sum()),at_least_095=int((similarity>=.95).sum())),
        neighbour_ledger=[dict(test_index=i,nearest_train_index=train[int(nearest[j,0])],cosine=float(similarity[j])) for j,i in enumerate(test)])


def train(previous,output):
    previous,output=Path(previous),Path(output);dataset=ROOT/'research/data/newdata-20261013/smishguard_dataset_2026-10-12.zip'
    h.verify_freeze(dataset,previous)
    if output.exists():raise FileExistsError('Use a new private directory')
    rows=n.load(previous/'dataset.json');old=n.load(previous/'splits.json');groups=np.asarray(old['groups'])
    imported,_=n.read_dataset(dataset);cleaned,_,_=n.clean(imported)
    if cleaned!=rows:raise ValueError('Historical cleaning/input mismatch')
    output.mkdir(parents=True,exist_ok=False);n.save(output/'dataset.json',rows);n.save(output/'groups.json',groups.tolist())
    print('Recomputing label-blind components for leakage audit...',flush=True)
    if not np.array_equal(n.group_rows(rows),groups):raise ValueError('Historical grouping mismatch')
    with threadpool_limits(limits=1):audit=old_split_audit(rows,groups,old)
    n.save(output/'old-split-audit.json',audit)
    print('Allocating five balanced whole-group 80/20 folds...',flush=True)
    cv,allocation=balanced_folds(rows,groups);sources=source_folds(rows,groups);folds=cv+sources
    n.save(output/'folds.json',dict(folds=folds,allocation=allocation))
    for f in cv:print(f['id'],len(f['train']),len(f['test']),'test groups',len(set(groups[f['test']])),flush=True)
    permutation=np.random.default_rng(20261019).permutation([r['label'] for r in rows]).tolist()
    n.save(output/'permuted-label-negative-control.json',dict(labels=permutation,seed=20261019,note='Negative control only; actual labels unchanged'))
    config=dict(specs=SPECS,threshold=.5,seed=SEED,no_hyperparameter_or_threshold_search=True,
        source_ids={v:'source'+str(j) for j,v in enumerate(sorted({r['source'] for r in rows}))},
        primary_artifact='group-fold-0; all candidate fits use its 80% training only; no performance-based fold selection',
        history='Previously exposed inherited-label corpus; all evaluations retrospective',
        previous_freeze_sha256=n.digest(previous/'freeze.json'),input_zip_sha256=n.digest(dataset),
        dataset_sha256=n.digest(output/'dataset.json'),old_grouping_sha256=n.digest(previous/'splits.json'))
    n.save(output/'configuration.json',config);shutil.copyfile(PROTOCOL,output/'protocol.md')
    n.save(output/'environment.json',dict(python=sys.version,packages={p:importlib.metadata.version(p) for p in ('numpy','scipy','scikit-learn','threadpoolctl')}))
    source_paths={'experiment.py':Path(__file__),'nb_comparison.py':Path(n.__file__),'holdout_8020.py':Path(h.__file__)}
    for name,path in source_paths.items():shutil.copyfile(path,output/name)
    fits=[]
    with threadpool_limits(limits=1):
        for fold in folds:
            ids=fold['train'];texts=[rows[i]['text'] for i in ids];y=[rows[i]['label'] for i in ids]
            for spec in SPECS:
                started=time.perf_counter();model=make_pipeline(spec).fit(texts,y)
                if model['classifier'].classes_.tolist()!=[0,1]:raise ValueError('Positive-class mapping changed')
                folder=output/fold['id']/spec['id'];folder.mkdir(parents=True)
                (folder/'pipeline.pkl').write_bytes(pickle.dumps(model,protocol=5))
                fits.append(dict(fold=fold['id'],model=spec['id'],training_ids=ids,training_seconds=time.perf_counter()-started,
                    features=len(model['tfidf'].vocabulary_),train=measure(y,model.predict_proba(texts)[:,1]>=.5,groups[ids])))
            if fold['scheme']=='group-cv':
                for name in ('source-only','permuted-label'):
                    folder=output/fold['id']/name;folder.mkdir(parents=True)
                    if name=='source-only':
                        data=[config['source_ids'][rows[i]['source']] for i in ids]
                        model=Pipeline([('tfidf',CountVectorizer()),('classifier',MultinomialNB(alpha=.1))]).fit(data,y)
                    else:model=make_pipeline(SPECS[0]).fit(texts,[permutation[i] for i in ids])
                    (folder/'pipeline.pkl').write_bytes(pickle.dumps(model,protocol=5))
            print('Fresh fits complete:',fold['id'],flush=True)
    n.save(output/'training-results.json',fits)
    n.save(output/'freeze.json',dict(sources={name:n.digest(path) for name,path in source_paths.items()},protocol_sha256=n.digest(PROTOCOL),
        files={p.relative_to(output).as_posix():n.digest(p) for p in output.rglob('*') if p.is_file()}))
    print('Sealed all fits before held-out prediction.',flush=True)


def verify(output):
    output=Path(output);seal=n.load(output/'freeze.json')
    for name,path in {'experiment.py':Path(__file__),'nb_comparison.py':Path(n.__file__),'holdout_8020.py':Path(h.__file__)}.items():
        if n.digest(path)!=seal['sources'][name]:raise ValueError('Frozen source changed')
    if n.digest(PROTOCOL)!=seal['protocol_sha256']:raise ValueError('Protocol changed')
    for name,sha in seal['files'].items():
        if n.digest(output/name)!=sha:raise ValueError('Frozen file changed: '+name)


def evaluate(output):
    output=Path(output);verify(output)
    with (output/'evaluation-started.json').open('x',encoding='utf-8') as f:json.dump(dict(freeze_sha256=n.digest(output/'freeze.json')),f)
    rows=n.load(output/'dataset.json');groups=np.asarray(n.load(output/'groups.json'));config=n.load(output/'configuration.json')
    permutation=n.load(output/'permuted-label-negative-control.json')['labels'];results=[];pooled={}
    with threadpool_limits(limits=1):
        for fold in n.load(output/'folds.json')['folds']:
            ids=fold['test'];texts=[rows[i]['text'] for i in ids]
            for name in [s['id'] for s in SPECS]+(['source-only','permuted-label'] if fold['scheme']=='group-cv' else []):
                folder=output/fold['id']/name;model=pickle.loads((folder/'pipeline.pkl').read_bytes())
                data=[config['source_ids'][rows[i]['source']] for i in ids] if name=='source-only' else texts
                y=[permutation[i] if name=='permuted-label' else rows[i]['label'] for i in ids]
                if model['classifier'].classes_.tolist()!=[0,1]:raise ValueError('Positive-class mapping changed')
                score=model.predict_proba(data)[:,1];pred=(score>=.5).astype(int)
                if not np.isfinite(score).all() or ((score<0)|(score>1)).any():raise ValueError('Invalid held-out scores')
                saved=dict(indices=ids,labels=y,scores=score.tolist(),predictions=pred.tolist())
                n.save(folder/'predictions.json',saved)
                result=dict(fold=fold['id'],scheme=fold['scheme'],source=fold.get('source'),model=name,
                    test=measure(y,pred,groups[ids]),training_records=len(fold['train']),purged=fold.get('related_records_purged',0),
                    zero_feature_messages=int((model['tfidf'].transform(data).getnnz(axis=1)==0).sum()))
                results.append(result)
                if fold['scheme']=='group-cv':
                    target=pooled.setdefault(name,dict(indices=[],labels=[],predictions=[]))
                    for key in target:target[key].extend(saved[key])
            print('Held-out evaluation complete:',fold['id'],flush=True)
    summaries={}
    for name,p in pooled.items():
        if sorted(p['indices'])!=list(range(len(rows))) or len(set(p['indices']))!=len(rows):raise ValueError('Incomplete OOF coverage')
        summaries[name]=measure(p['labels'],p['predictions'],groups[p['indices']])
    n.save(output/'results.json',dict(results=results,group_cv=summaries,
        all_ham_baseline=measure([r['label'] for r in rows],np.zeros(len(rows),dtype=int),groups),selected_for_deployment=None))
    verify(output)


def report(output,destination):
    output,destination=Path(output),Path(destination);verify(output)
    rows=n.load(output/'dataset.json');groups=np.asarray(n.load(output/'groups.json'));folds=n.load(output/'folds.json')['folds'];data=n.load(output/'results.json')
    permutation=n.load(output/'permuted-label-negative-control.json')['labels']
    for result in data['results']:
        fold=next(f for f in folds if f['id']==result['fold']);p=n.load(output/fold['id']/result['model']/'predictions.json')
        if p['indices']!=fold['test'] or set(fold['train'])&set(fold['test']) or set(groups[fold['train']])&set(groups[fold['test']]):raise ValueError('Held-out isolation failed')
        expected=[permutation[i] if result['model']=='permuted-label' else rows[i]['label'] for i in p['indices']]
        if p['labels']!=expected or (np.asarray(p['scores'])>=.5).astype(int).tolist()!=p['predictions']:raise ValueError('Prediction labels/threshold changed')
        if measure(p['labels'],p['predictions'],groups[p['indices']])!=result['test']:raise ValueError('Saved metrics do not match predictions')
    old=n.load(output/'old-split-audit.json');old_public={k:v for k,v in old.items() if k!='neighbour_ledger'}
    fit=n.load(output/'training-results.json');destination.mkdir(parents=True,exist_ok=True)
    n.save(destination/'results.json',dict(data,old_split_audit=old_public,allocation=n.load(output/'folds.json')['allocation'],
        folds=[dict(id=f['id'],scheme=f['scheme'],source=f.get('source'),train=n.counts([rows[i] for i in f['train']]),test=n.counts([rows[i] for i in f['test']]),
                    test_groups=len(set(groups[f['test']])),purged=f.get('related_records_purged',0)) for f in folds],
        training=[{k:v for k,v in item.items() if k!='training_ids'} for item in fit]))
    lines=['# NB generalization audit and retraining — 19 October 2026','',
        'The earlier 99.71% result came from 684 test rows but only nine independent components; '
        f'{old["largest_test_group"]} rows ({old["largest_test_group_fraction"]:.2%}) belonged to one component. '
        f'Exact-text overlap: {old["exact_casefold_overlap"]}; stored template-group overlap: {old["template_group_overlap"]}. '
        'This is evidence of a concentrated evaluation, not proof that the model memorized exact test messages. '
        'The earlier best-algorithm claim was stronger than this evidence supports.', '',
        'Five disjoint, whole-group tests each use integer-rounded 80% training / 20% testing. '
        'Every eligible message is predicted once without being used by that model. Group counts are balanced before fitting; '
        'no model score enters allocation. Three additional source-held-out fits remove all related groups from training. '
        'Source holdouts are stress tests with different fractions, not additional 80/20 experiments. '
        'All labels/corpus remain historically exposed; this does not create a fresh prospective test.', '',
        '| Fixed condition | Mean training accuracy | Group CV accuracy | Scam precision | Scam recall | Scam F1 | Fold F1 range | Equal-group accuracy |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for name,m in data['group_cv'].items():
        trained=[e['train']['accuracy'] for e in fit if e['model']==name and e['fold'].startswith('group-fold')]
        train='—' if not trained else f'{np.mean(trained):.2%}'
        fold_f1=[e['test']['f1'] for e in data['results'] if e['model']==name and e['scheme']=='group-cv']
        lines.append(f'| {name} | {train} | {m["accuracy"]:.2%} | {m["precision"]:.2%} | {m["recall"]:.2%} | {m["f1"]:.2%} | {min(fold_f1):.2%}–{max(fold_f1):.2%} | {m["group_weighted_accuracy"]:.2%} |')
    lines+=['', '| Group fold | Training rows | Test rows | Test ham/scam | Test components |', '|---|---:|---:|---:|---:|']
    for f in folds:
        if f['scheme']=='group-cv':
            support=n.counts([rows[i] for i in f['test']])
            lines.append(f'| {f["id"]} | {len(f["train"])} | {len(f["test"])} | {support["ham"]}/{support["smishing"]} | {len(set(groups[f["test"]]))} |')
    lines+=['',f'An all-ham classifier gets {data["all_ham_baseline"]["accuracy"]:.2%} accuracy and zero scam F1. '
        'Source-only NB receives source identity with no message text. The label-permutation model is a deliberately randomized negative control, '
        'evaluated against its separately permuted labels; it is not a phishing-quality estimate or a permutation significance test.', '',
        '| Entire held-out source | Model | Training rows | Purged related rows | Ham/scam test support | Accuracy | Recall | Scam F1 | FPR |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for e in data['results']:
        if e['scheme']!='source-held-out':continue
        m=e['test'];fpr='not estimable' if m['fpr'] is None else f'{m["fpr"]:.2%}'
        lines.append(f'| {e["source"]} | {e["model"]} | {e["training_records"]} | {e["purged"]} | {m["ham"]}/{m["smishing"]} | {m["accuracy"]:.2%} | {m["recall"]:.2%} | {m["f1"]:.2%} | {fpr} |')
    lines+=['', 'Original NB keeps the earlier full-URL/number/currency tokenizer, alpha=.1 and threshold >=.5. '
        'Reduced models remove complete URLs/emails/numeric identifiers and amounts using a fixed transform; '
        'keep conservative stopwords and word (1,2) TF-IDF; use min_df=2, max_df=.95, cap=20,000. '
        'Compare alpha=.1 and stronger smoothing alpha=1. These feature changes can also remove useful signals; '
        'lower accuracy is not automatically better generalization. No condition, threshold or split is selected by test ranking.', '',
        'Equal-group accuracy gives each template/sender component equal weight, instead of allowing hundreds of related '
        'messages to dominate. Train/test gaps are descriptive; low gaps do not establish absence of memorization. '
        'Source and inherited labeling rules remain confounded. Positive-only source tests cannot measure false-positive rate. '
        'No independent campaign/sender identity, human labels or verified receipt chronology has been added. '
        'A chronological claim or real-world accuracy estimate cannot be established from these retrospective reshuffles.', '',
        'All fitted models and private neighbor/prediction ledgers are retained under '+output.as_posix()+'. '
        'The fixed first fold supplies each reference 80%-trained artifact; it was chosen before evaluation. '
        'No Android model is replaced. Source attribution and existing license restrictions remain in ../source-evidence.md.', '',
        'Reproduce from the repository root with a new private output directory:', '', '```powershell',
        '$run=\'research/runs/nb-generalization-20261019/NEW-RUN\'',
        'research/.venv/Scripts/python.exe scripts/retrain_nb_generalization.py train $run',
        'research/.venv/Scripts/python.exe scripts/retrain_nb_generalization.py evaluate $run',
        'research/.venv/Scripts/python.exe scripts/retrain_nb_generalization.py report $run', '```','']
    (destination/'RESULTS.md').write_text('\n'.join(lines),encoding='utf-8')
    n.save(output/'completion-verification.json',dict(freeze_verified=True,metric_tables_recomputed=len(data['results']),
        actual_labels_unchanged=True,primary_80_20_folds=5,source_purged_folds=3,deployment_selected=None,
        public_files={p.name:n.digest(p) for p in destination.iterdir() if p.is_file()}))
    print('Verified report:',destination/'RESULTS.md',flush=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['train','evaluate','report']);parser.add_argument('output',type=Path)
    parser.add_argument('--previous',type=Path,default=ROOT/'research/runs/holdout-8020-20261019/run-v1')
    parser.add_argument('--report-dir',type=Path,default=ROOT/'docs/nb-generalization-20261019');a=parser.parse_args()
    if a.phase=='train':train(a.previous,a.output)
    elif a.phase=='evaluate':evaluate(a.output)
    else:report(a.output,a.report_dir)


if __name__=='__main__':
    import scripts
    sys.modules['scripts.retrain_nb_generalization']=sys.modules[__name__]
    reduced_text.__module__='scripts.retrain_nb_generalization'
    main()
