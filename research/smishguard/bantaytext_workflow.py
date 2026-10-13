"""Baseline-first retrospective research; never installs a model or changes app policy.

The notebook embeds these functions so its training/metric code is visible and runnable.
Populated ledgers, vocabulary and fitted parameters belong only in ignored storage.
"""
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
import argparse
import csv
import hashlib
import importlib.metadata
import json
import pickle
import re
import time

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.model_selection import train_test_split, StratifiedGroupKFold
from sklearn.metrics import (confusion_matrix, precision_score, recall_score, f1_score,
    accuracy_score, average_precision_score, roc_auc_score, brier_score_loss, log_loss)

SEED = 42
URL = re.compile(r'https?://\S+|www\.\S+', re.I)
PLACEHOLDER = re.compile(r'<(?:REAL NAME|NAME|REDACTED|BLANK|n)>|\[name redacted\]|\(full name\)|\[my name\]', re.I)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def class_counts(rows):
    labels = Counter(int(r['label']) for r in rows)
    return dict(records=len(rows), ham=labels[0], smishing=labels[1],
                scam_fraction=labels[1]/len(rows) if rows else None)


def clean_rows(records):
    """Source labels stay intact; flagged/unsupported/conflicting rows are held.

    Input is the existing source-joined, identifier-masked fitting view. We do not
    automatically grant permission to raw sources or run the supplied rule builder.
    """
    staged, ledger = [], []
    for i, r in enumerate(records):
        raw = r.get('text')
        text = re.sub(r'\s+', ' ', PLACEHOLDER.sub(' ', raw)).strip(' ,') if isinstance(raw, str) else ''
        label = r.get('label')
        reason = ('empty' if not text else 'unsupported_label' if type(label) is not int or label not in (0, 1)
                  else 'pending_flagged_review' if str(r.get('needs_review', '')).lower() == 'true' else None)
        key = text.lower()
        staged.append(dict(r, text=text, _key=key, _row=i))
        ledger.append(dict(row=i, id=r.get('id'), original_label=label,
            original_text_sha256=hashlib.sha256((raw or '').encode()).hexdigest(),
            text_changed=raw != text, reason=reason))
    buckets = defaultdict(list)
    for r in staged:
        # Conflicts include flagged records: do not retain the other side as certainty.
        if r['text'] and type(r.get('label')) is int and r['label'] in (0, 1):
            buckets[r['_key']].append(r)
    conflict_keys = {key for key, rr in buckets.items() if len({r['label'] for r in rr}) > 1}
    seen, retained = set(), []
    for r in staged:
        entry = ledger[r['_row']]
        if r['_key'] in conflict_keys:
            entry['reason'] = 'conflicting_exact_labels'
        if not entry['reason']:
            if r['_key'] in seen:
                entry['reason'] = 'duplicate_masked_casefold_text'
            else:
                seen.add(r['_key'])
                retained.append({k:v for k,v in r.items() if not k.startswith('_')})
    return retained, ledger, dict(before=class_counts([r for r in records if type(r.get('label')) is int and r['label'] in (0,1)]),
        after=class_counts(retained), removals=dict(Counter(e['reason'] for e in ledger if e['reason'])),
        conflicting_exact_groups=len(conflict_keys), missing_fields={k:sum(not r.get(k) for r in records) for k in ('text','source','category','language')},
        input_labels={str(k):v for k,v in Counter(r.get('label') for r in records).items()},
        transformations='Remove known placeholder spans, collapse whitespace, hold flagged/unsupported/conflicting records, retain first masked casefold duplicate',
        label_mapping={'0':'ham', '1':'smishing'}, label_status='Inherited source/rule labels; independently unverified')


def template_key(text):
    # Label-blind grouping uses a broader normalization than the training features.
    text = URL.sub(' ', text.lower())
    text = re.sub(r'\bzz(?:url|number|email)zz\b|[0-9]+', ' ', text)
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z]+', ' ', text)).strip()


def make_groups(rows):
    texts = [template_key(r['text']) for r in rows]
    counts = [Counter(t) for t in texts]
    parent = list(range(len(rows)))
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i in range(len(rows)):
        for j in range(i):
            if root(i) == root(j):
                continue
            supplied_equal = bool(rows[i].get('template_group')) and rows[i].get('template_group') == rows[j].get('template_group')
            if texts[i] == texts[j] or supplied_equal:
                parent[root(i)] = root(j)
                continue
            total = len(texts[i])+len(texts[j])
            if 2*min(len(texts[i]),len(texts[j]))/max(1,total) < .85:
                continue
            bound = 2*sum(min(v,counts[j].get(c,0)) for c,v in counts[i].items())/max(1,total)
            if bound >= .85 and SequenceMatcher(None,texts[i],texts[j],autojunk=False).ratio() >= .85:
                parent[root(i)] = root(j)
    return np.array([root(i) for i in range(len(rows))])


def partitions(rows, groups, track):
    y = np.array([r['label'] for r in rows]); ids = np.arange(len(rows))
    if track == 'random':
        train, held = train_test_split(ids,test_size=.4,stratify=y,random_state=SEED)
        val, test = train_test_split(held,test_size=.5,stratify=y[held],random_state=SEED)
    elif track == 'grouped':
        folds = [b for _,b in StratifiedGroupKFold(n_splits=10,shuffle=True,random_state=SEED).split(ids,y,groups)]
        train, val, test = (np.concatenate(folds[a:b]) for a,b in ((0,6),(6,8),(8,10)))
    else:
        raise ValueError('Unknown track')
    result = dict(train=train.tolist(), validation=val.tolist(), test=test.tolist())
    if any(len(set(y[ii])) != 2 for ii in result.values()):
        raise ValueError('Both classes required in each partition; no favorable-seed retry')
    assert len(set(train)|set(val)|set(test)) == len(rows)
    overlap = {a+'-'+b:len(set(groups[result[a]])&set(groups[result[b]])) for a in result for b in result if a<b}
    if track == 'grouped':
        assert not any(overlap.values())
    return result, dict(support={p:class_counts([rows[i] for i in ii]) for p,ii in result.items()},
        template_overlap=overlap, strategy='two-step stratified 60/20/20' if track=='random' else '10 stratified group folds allocated 6/2/2; approximate 60/20/20',
        seed=SEED, temporal='Unavailable: collection dates lack verified receipt-time meaning and timezone')


def feature_view(text, spec):
    if spec.get('ablation') == 'remove_urls':
        return re.sub(r'\bzzurlzz\b', ' ', URL.sub(' ', text))
    if spec.get('ablation') == 'placeholders_only':
        return ' '.join(re.findall(r'\bzz(?:url|email|number)zz\b', text)) or 'empty'
    if spec['features'] == 'portable':
        # Exact existing sg-ascii-v1 preprocessing, including ASCII-only lowercase.
        text = text.translate(str.maketrans('ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'))
        text = URL.sub(' zzurlzz ',text)
        text = re.sub(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', ' zzemailzz ',text)
        return re.sub('[^a-z]+',' ',re.sub('[0-9]+',' zznumberzz ',text)).strip()
    return text


def vectorizer(spec):
    word = dict(analyzer='word', ngram_range=tuple(spec.get('ngrams',[1,1])),
        stop_words=spec.get('stop_words'), max_features=None, min_df=1,
        norm='l2', sublinear_tf=False, smooth_idf=True)
    if spec['features'] == 'portable':
        word.update(lowercase=False,token_pattern=r'(?u)\b[a-z]+\b')
    if spec['features'] in ('word','portable'):
        return TfidfVectorizer(**word)
    char = TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),max_features=None,min_df=1,norm='l2')
    return char if spec['features']=='char' else FeatureUnion([('word',TfidfVectorizer(**word)),('char',char)])


def classifier(spec):
    name = spec['algorithm']
    if name == 'nb':
        return MultinomialNB(alpha=spec.get('alpha',1.0))
    if name == 'lr':
        return LogisticRegression(C=spec.get('C',1.0),class_weight=spec.get('class_weight'),solver='liblinear',max_iter=2000,random_state=SEED)
    return LinearSVC(C=spec.get('C',1.0),class_weight=spec.get('class_weight'),dual='auto',max_iter=10000,random_state=SEED)


def margin(model, x):
    return (model.predict_log_proba(x)[:,1]-model.predict_log_proba(x)[:,0]) if isinstance(model,MultinomialNB) else model.decision_function(x)


def fit_candidate(rows, groups, ids, spec):
    texts = [feature_view(rows[i]['text'],spec) for i in ids]
    y = np.array([rows[i]['label'] for i in ids]); start = time.perf_counter()
    pipe = Pipeline([('tfidf',vectorizer(spec)),('classifier',classifier(spec))])
    calibrator = None
    if spec.get('calibrated'):
        # Calibration uses training-derived grouped OOF margins. Every fold learns
        # its own vocabulary/IDF; neither outer validation nor test is used.
        oof = np.full(len(ids),np.nan)
        fold_audit = []
        for a,b in StratifiedGroupKFold(n_splits=3,shuffle=True,random_state=SEED).split(texts,y,groups[ids]):
            fold_pipe = Pipeline([('tfidf',vectorizer(spec)),('classifier',classifier(spec))])
            assert not set(groups[np.asarray(ids)[a]]) & set(groups[np.asarray(ids)[b]])
            fold_pipe.fit([texts[i] for i in a],y[a])
            oof[b] = margin(fold_pipe['classifier'],fold_pipe['tfidf'].transform([texts[i] for i in b]))
            fold_audit.append(dict(train=[ids[int(i)] for i in a], calibration=[ids[int(i)] for i in b]))
        assert np.isfinite(oof).all()
        calibrator = LogisticRegression(C=1,solver='lbfgs',random_state=SEED).fit(oof.reshape(-1,1),y)
    pipe.fit(texts,y)
    assert pipe['classifier'].classes_.tolist() == [0,1]
    return dict(pipe=pipe,calibrator=calibrator,spec=spec,training_seconds=time.perf_counter()-start,
                calibration_folds=fold_audit if calibrator is not None else [])


def score(artifact, texts):
    spec = artifact['spec']; pipe = artifact['pipe']
    x = pipe['tfidf'].transform([feature_view(t,spec) for t in texts])
    if artifact['calibrator'] is not None:
        return artifact['calibrator'].predict_proba(margin(pipe['classifier'],x).reshape(-1,1))[:,1]
    return pipe['classifier'].predict_proba(x)[:,1] if spec['algorithm'] != 'svm' else margin(pipe['classifier'],x)


def calculate_metrics(y, scores, threshold, probability=True):
    y = np.array(y); scores = np.array(scores); pred = scores >= threshold
    if not len(y) or not np.isfinite(scores).all():
        raise ValueError('Nonempty finite predictions required')
    tn,fp,fn,tp = (int(n) for n in confusion_matrix(y,pred,labels=[0,1]).ravel())
    # Independent confusion-count arithmetic, checked against the library.
    precision = tp/(tp+fp) if tp+fp else 0.0
    recall = tp/(tp+fn) if tp+fn else 0.0
    f1 = 2*precision*recall/(precision+recall) if precision+recall else 0.0
    accuracy = (tp+tn)/(tp+tn+fp+fn)
    assert np.allclose([precision,recall,f1,accuracy], [precision_score(y,pred,zero_division=0),
        recall_score(y,pred,zero_division=0),f1_score(y,pred,zero_division=0),accuracy_score(y,pred)],atol=1e-12)
    both = len(set(y))==2
    if probability and ((scores<0)|(scores>1)).any():
        raise ValueError('Probability-like scores must lie in [0,1]')
    return dict(records=len(y),precision=precision,recall=recall,f1=f1,accuracy=accuracy,
        average_precision=float(average_precision_score(y,scores)) if both else None,
        roc_auc=float(roc_auc_score(y,scores)) if both else None,
        false_positive_rate=fp/(fp+tn) if fp+tn else None, false_negative_rate=fn/(fn+tp) if fn+tp else None,
        confusion=dict(tn=tn,fp=fp,fn=fn,tp=tp),brier=float(brier_score_loss(y,scores)) if probability else None,
        log_loss=float(log_loss(y,scores,labels=[0,1])) if probability else None,
        ranking_score='probability-like, calibration quality unvalidated' if probability else 'uncalibrated SVM margin; not probability')


def threshold_policy(y, scores):
    trials = [dict(threshold=float(t),**calculate_metrics(y,scores,float(t))) for t in np.linspace(.05,.95,91)]
    feasible = [r for r in trials if r['precision'] >= .90 and r['confusion']['tp'] >= 5]
    chosen = max(feasible,key=lambda r:(r['f1'],r['recall'],-r['confusion']['fp'],r['threshold'])) if feasible else None
    return (chosen['threshold'] if chosen else .5), trials, bool(chosen)


def experiment_matrix():
    base = [dict(id=f'baseline-{a}',phase='baseline',algorithm=a,features='word',ngrams=[1,1],stop_words=None,
                 alpha=1.0,C=1.0,class_weight=None,calibrated=False,tune_threshold=False) for a in ('nb','lr','svm')]
    experiments = list(base)
    for a in ('nb','lr','svm'):
        ref = dict(phase='improvement',algorithm=a,features='word',ngrams=[1,2],stop_words='english',
            alpha=.1,C=1.0,class_weight=None,calibrated=a=='svm',tune_threshold=True)
        experiments.append(dict(ref,id=f'{a}-word12-english'))
        experiments.append(dict(ref,id=f'{a}-word12-no-stop',stop_words=None))
        for feature in ('char','combined'):
            experiments.append(dict(ref,id=f'{a}-{feature}',features=feature))
        if a=='nb':
            for alpha in (.03,.3,1.0):
                experiments.append(dict(ref,id=f'nb-alpha-{alpha}',alpha=alpha))
            experiments.append(dict(ref,id='nb-word1-english',ngrams=[1,1]))
        else:
            for c in (.1,10.0):
                experiments.append(dict(ref,id=f'{a}-C-{c}',C=c))
            experiments.append(dict(ref,id=f'{a}-balanced',class_weight='balanced'))
        if a=='lr':
            experiments.append(dict(ref,id='lr-oof-calibrated',calibrated=True))
        if a=='svm':
            experiments.append(dict(ref,id='svm-word1-calibrated',ngrams=[1,1],stop_words=None))
    experiments.append(dict(phase='improvement',id='lr-portable',algorithm='lr',features='portable',ngrams=[1,1],
        stop_words=None,C=1.0,class_weight=None,calibrated=True,tune_threshold=True))
    # Prespecified shortcut diagnostics, excluded from winner selection.
    for ablation in ('remove_urls','placeholders_only','source_only'):
        experiments.append(dict(phase='diagnostic',id='lr-'+ablation,algorithm='lr',features='word',ngrams=[1,2],
            stop_words='english',C=1.0,class_weight=None,calibrated=False,tune_threshold=True,ablation=ablation))
    return experiments


def prepare_run(dataset, output):
    if output.exists():
        raise ValueError('Use a fresh run directory; never overwrite a frozen experiment')
    output.mkdir(parents=True)
    raw = load(dataset)
    rows,ledger,audit = clean_rows(raw)
    save(output/'cleaning-ledger.json',ledger); save(output/'dataset.json',rows)
    groups = make_groups(rows)
    audit.update(template_groups=len(set(groups)), mixed_label_template_groups=sum(len({rows[i]['label'] for i in np.flatnonzero(groups==g)})>1 for g in set(groups)),
        grouping='Label-blind supplied templates + ASCII URL/identifier-stripped SequenceMatcher >=.85 connected components; heuristic, not verified campaign identity',
        sources={s:class_counts([r for r in rows if r['source']==s]) for s in sorted({r['source'] for r in rows})},
        human_review='Pending; no category converted to ground truth',data_history='Previously exposed; retrospective comparisons only')
    save(output/'data-audit.json',audit)
    manifests = {}; support = {}
    for track in ('random','grouped'):
        manifests[track],support[track] = partitions(rows,groups,track)
    save(output/'splits.json',dict(groups=groups.tolist(),partitions=manifests,support=support))
    cfg = dict(seed=SEED,input_sha256=digest(dataset),cleaned_sha256=digest(output/'dataset.json'),
        split_sha256=digest(output/'splits.json'),matrix=experiment_matrix(),
        versions={k:importlib.metadata.version(k) for k in ('numpy','scipy','scikit-learn','joblib')},
        threshold_criterion='Validation F1 maximum subject to precision >= .90 and TP >=5; tie recall, fewer FP, larger threshold; unmet criterion is not deployable',
        selection_criterion='Grouped validation F1 among feasible improved candidates; ties lower measured serialized bytes then ID; random track separate',
        final_test_history='Prior historical exposure; no prospective independence claim',
        deployment='Retain active model: independent labels, prospective test, and calibration/deployment review unresolved')
    save(output/'configuration.json',cfg)
    return rows,groups,manifests,audit,cfg


def run_phase(output, rows, groups, manifests, cfg, phase):
    if digest(output/'dataset.json') != cfg['cleaned_sha256'] or digest(output/'splits.json') != cfg['split_sha256']:
        raise ValueError('Frozen data or split changed')
    if phase=='improvement' and not (output/'baseline-test.json').exists():
        raise ValueError('Finish and save baseline before improvements')
    specs = [s for s in cfg['matrix'] if (s['phase']=='baseline') == (phase=='baseline')]
    results = []; artifacts = {}; freezes = {}
    for track,parts in manifests.items():
        for spec in specs:
            run = output/track/spec['id']; run.mkdir(parents=True,exist_ok=False)
            fitting_rows = rows
            if spec.get('ablation')=='source_only':
                fitting_rows = [dict(r,text=r['source']) for r in rows]
            artifact = fit_candidate(fitting_rows,groups,parts['train'],spec)
            val_text = [fitting_rows[i]['text'] for i in parts['validation']]
            yv = [rows[i]['label'] for i in parts['validation']]
            p = score(artifact,val_text)
            probability = spec['algorithm']!='svm' or spec.get('calibrated',False)
            threshold = .5 if probability else 0.0; feasible = True
            default_metrics = calculate_metrics(yv,p,threshold,probability)
            if spec.get('tune_threshold'):
                threshold,trials,feasible = threshold_policy(yv,p)
                save(run/'threshold-trials.json',trials)
            artifact.update(threshold=threshold,probability=probability)
            (run/'pipeline.pkl').write_bytes(pickle.dumps(artifact))
            fitted = artifact['pipe']['tfidf']; feature_count = len(fitted.get_feature_names_out())
            x = fitted.transform([feature_view(fitting_rows[i]['text'],spec) for i in parts['train']])
            start = time.perf_counter(); score(artifact,val_text); elapsed = time.perf_counter()-start
            record = dict(track=track,id=spec['id'],phase=spec['phase'],config=spec,threshold=threshold,
                threshold_criterion_met=feasible,default_validation=default_metrics,
                validation=calculate_metrics(yv,p,threshold,probability),feature_count=feature_count,
                serialized_bytes=(run/'pipeline.pkl').stat().st_size,training_seconds=artifact['training_seconds'],
                host_validation_ms_per_message=elapsed*1000/len(val_text),
                sparse_training_bytes=int(x.data.nbytes+x.indices.nbytes+x.indptr.nbytes),
                calibration='training-group-OOF sigmoid; quality not validated' if artifact['calibrator'] is not None else 'not fitted')
            save(run/'validation.json',record)
            results.append(record); artifacts[(track,spec['id'])]=artifact
            freezes[str(run.relative_to(output)/'pipeline.pkl')] = digest(run/'pipeline.pkl')
            print(track,spec['id'],'validation F1',round(record['validation']['f1'],4),flush=True)
    # Select and freeze before any current-phase test transform/prediction.
    selected = {}
    for track in manifests:
        eligible = [r for r in results if r['track']==track and r['phase']!='diagnostic' and r['threshold_criterion_met']]
        if eligible:
            selected[track] = max(eligible,key=lambda r:(r['validation']['f1'],-r['serialized_bytes'],r['id']))['id']
        else:
            selected[track] = None
    freeze = dict(files=freezes,selected=selected,validation=results,test_opened=False,
                  configuration_sha256=digest(output/'configuration.json'))
    save(output/(phase+'-freeze.json'),freeze)
    test_results = []
    for record in results:
        track,key=record['track'],record['id']; artifact=artifacts[(track,key)]
        assert digest(output/track/key/'pipeline.pkl') == freezes[str(Path(track)/key/'pipeline.pkl')]
        ids = manifests[track]['test']; texts = [rows[i]['source'] if record['config'].get('ablation')=='source_only' else rows[i]['text'] for i in ids]
        start=time.perf_counter(); p=score(artifact,texts); latency=(time.perf_counter()-start)*1000/len(ids)
        record = dict(record,test=calculate_metrics([rows[i]['label'] for i in ids],p,artifact['threshold'],artifact['probability']),host_test_ms_per_message=latency)
        save(output/track/key/'test-predictions.json',dict(indices=ids,labels=[rows[i]['label'] for i in ids],scores=p.tolist()))
        test_results.append(record)
    save(output/(phase+'-test.json'),test_results)
    return test_results,selected


def error_analysis(rows, ids, p, threshold):
    y=np.array([rows[i]['label'] for i in ids]); pred=np.array(p)>=threshold
    results = {}
    for field in ('category','language','source'):
        groups = {}
        for value in sorted({rows[i].get(field,'unknown') for i in ids}):
            ii = [j for j,i in enumerate(ids) if rows[i].get(field,'unknown')==value]
            negatives = [j for j in ii if y[j]==0]; positives = [j for j in ii if y[j]==1]
            fp=sum(pred[j] for j in negatives); fn=sum(not pred[j] for j in positives)
            groups[value]=dict(records=len(ii),ham=len(negatives),smishing=len(positives),fp=int(fp),fn=int(fn),
                false_positive_rate=float(fp/len(negatives)) if len(negatives)>=20 else None,
                false_negative_rate=float(fn/len(positives)) if len(positives)>=20 else None,
                interpretation='Descriptive inherited labels; rate suppressed if relevant denominator <20')
        results[field]=groups
    # No message content, identifiers or URLs in public errors.
    return dict(subgroups=results,errors=[dict(private_row_index=ids[j],label=int(y[j]),predicted=int(pred[j])) for j in range(len(ids)) if pred[j]!=y[j]],
        limitation='No independently confirmed scam or financial-only scope labels; no inferred bank/e-wallet subgroup metrics')


def finish_run(output, rows, groups, manifests, baseline, improved, selected):
    errors={}; source_holdout={}
    for track,key in selected.items():
        if key is None:
            continue
        artifact=pickle.loads((output/track/key/'pipeline.pkl').read_bytes())
        ids=manifests[track]['test']; p=score(artifact,[rows[i]['text'] for i in ids])
        analysis=error_analysis(rows,ids,p,artifact['threshold'])
        save(output/track/key/'error-ledger.json',analysis)
        errors[track]={k:v for k,v in analysis.items() if k!='errors'}
        probes=['Hello po, kumusta?', 'Pakisuri ang account sa opisyal na app.', 'Your OTP is 123456. Do not share it.',
                'Verify account at https://example.invalid/synthetic', 'paki verify nyo ngayon po', '', '   ',
                'qzxvunknownword zzzqqq', '🙂 ñ café İ', '\ud800 malformed', 'x'*10001]
        # Malformed surrogate stays local; vectorizer behavior is separate from Android input policy.
        ps=score(artifact,probes)
        save(output/track/key/'probe-scores.json',dict(scores=ps.tolist(),finite=bool(np.isfinite(ps).all()),
            note='Synthetic compatibility/OOD probes, no predictive accuracy or probability calibration claim'))
        # Fixed, prespecified URL removal stress test of the selected frozen fit.
        without=score(artifact,[re.sub(r'\bzzurlzz\b',' ',URL.sub(' ',rows[i]['text'])) for i in ids])
        errors[track]['url_removal_stress']=dict(changed_decisions=int(np.sum((p>=artifact['threshold'])!=(without>=artifact['threshold']))),
            original=calculate_metrics([rows[i]['label'] for i in ids],p,artifact['threshold']),
            masked=calculate_metrics([rows[i]['label'] for i in ids],without,artifact['threshold']))
        if track=='grouped':
            # Diagnostic only: fixed selected settings; purge templates from every held source.
            for source in sorted({r['source'] for r in rows}):
                test=[i for i,r in enumerate(rows) if r['source']==source]; held_groups=set(groups[test])
                train=[i for i,r in enumerate(rows) if r['source']!=source and groups[i] not in held_groups]
                if len({rows[i]['label'] for i in train})<2:
                    source_holdout[source]=dict(status='Insufficient training class support');continue
                fitted=fit_candidate(rows,groups,train,artifact['spec'])
                pp=score(fitted,[rows[i]['text'] for i in test])
                source_holdout[source]=dict(train=class_counts([rows[i] for i in train]),test=class_counts([rows[i] for i in test]),
                    metrics=calculate_metrics([rows[i]['label'] for i in test],pp,artifact['threshold']),
                    status='Post-selection source stress diagnostic; fixed main threshold, not used for selection; source also historically exposed')
    save(output/'error-analysis.json',errors);save(output/'source-heldout.json',source_holdout)
    # Export a compatible, actually fitted comparator for JVM verification only.
    # The research winner may have incompatible Unicode/bigram/character features.
    from smishguard.linear_export import export_linear
    from smishguard.parity import predict
    portable=pickle.loads((output/'grouped/lr-portable/pipeline.pkl').read_bytes())
    exported=export_linear(portable['pipe']['tfidf'],portable['pipe']['classifier'],portable['calibrator'],portable['threshold'],synthetic=False)
    exported.update(model_version='bantaytext-portable-comparator-20261013',automatic_warnings_approved=False)
    parity=output/'parity';parity.mkdir()
    save(parity/'model.json',exported)
    probes=['Hello po', 'Bayad ang account 123', 'Visit https://example.invalid/synthetic',
        'Walang link dito. Pakisuri ang account.', 'Your OTP is 123456. Do not share it.',
        'paki verify nyo po ngayon', 'HELLO hello account', '🌟 ñ Á İ hello', 'qzxvunknownword', 'bayad '*1000]
    cases=[]
    for text,expected in zip(probes,score(portable,probes)):
        actual,suspicious=predict(exported,text)
        assert abs(actual-expected)<1e-10
        cases.append(dict(text=text,normalized=feature_view(text,portable['spec']),score=float(expected),suspicious=suspicious))
    save(parity/'cases.json',cases)
    # Ordered vocabulary + IDF are inside the private pickle, not exported to Git.
    all_results=baseline+improved
    summary=dict(selected=selected,results=all_results,errors=errors,source_heldout=source_holdout,
        deployment='Retain existing model; independent label/prospective evidence insufficient',
        notebook_status='Executed metrics; no embedded SMS or fitted vocabulary',
        parity=dict(model_sha256=digest(parity/'model.json'),cases=len(cases),scope='Compatible comparator, not installation or winner validation'),
        physical_device='Not performed',android_cost='JVM parity measured separately; phone resource cost unmeasured')
    save(output/'aggregate.json',summary)
    return summary


def main():
    p=argparse.ArgumentParser();p.add_argument('dataset',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args()
    if not any(part in {'data','runs','output'} for part in a.output.parts):
        raise ValueError('Use ignored private storage for fitted artifacts and ledgers')
    rows,groups,parts,audit,cfg=prepare_run(a.dataset,a.output)
    baseline,_=run_phase(a.output,rows,groups,parts,cfg,'baseline')
    improved,selected=run_phase(a.output,rows,groups,parts,cfg,'improvement')
    finish_run(a.output,rows,groups,parts,baseline,improved,selected)


if __name__=='__main__':
    main()
