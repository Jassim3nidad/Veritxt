"""Versioned A–E research comparison; private input/output, no production mutations.

Only explicit inherited mappings are admitted. Final evaluation is separate from
fitting/selection, checks frozen hashes, and refuses repeated evaluation.
"""
from collections import Counter, defaultdict
from pathlib import Path
import argparse
import csv
import hashlib
import importlib.metadata
import importlib.util
import io
import json
import pickle
import platform
import re
import stat
import sys
import time
import unicodedata
import warnings
import zipfile

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, average_precision_score, precision_recall_curve, auc,
    roc_auc_score, brier_score_loss)
from sklearn.calibration import calibration_curve
from threadpoolctl import threadpool_limits

from .bantaytext_workflow import make_groups
from .convert_supplied import unicode_contract

POLICY = dict(precision_floor=.90, fpr_ceiling=.02, minimum_tp=5,
    objective='recall, then phishing F1, average precision, smaller serialized model',
    status='Provisional research goals; independent deployment acceptance pending')
MAX_ZIP_BYTES = 100_000_000
LABELS = {'ham': 0, 'smishing': 1, '0': 0, '1': 1}


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def label_value(value):
    if type(value) is int and value in (0, 1):
        return value
    if isinstance(value, str) and value in LABELS:
        return LABELS[value]
    raise ValueError('Unsupported label: explicit ham/smishing or 0/1 required; spam is not automatically phishing')


def read_input(path, member=None):
    """Strict UTF-8; ZIP is read in memory, never arbitrary extractall or execution."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f'Dataset does not exist: {path}. Set DATASET_PATH to the reviewed CSV/JSON or ZIP.')
    name = path.name
    payload = path.read_bytes()
    if path.suffix.lower() == '.zip':
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            entries = archive.infolist()
            if sum(e.file_size for e in entries) > MAX_ZIP_BYTES:
                raise ValueError('ZIP exceeds 100 MB uncompressed research input limit')
            for e in entries:
                parts = e.filename.replace('\\', '/').split('/')
                if e.filename.startswith(('/', '\\')) or '..' in parts or ':' in e.filename or stat.S_ISLNK(e.external_attr >> 16):
                    raise ValueError('Unsafe archive member')
            candidates = [e.filename for e in entries if not e.is_dir() and Path(e.filename).suffix.lower() in ('.csv', '.json')]
            if member is None and len(candidates) != 1:
                raise ValueError('ZIP has multiple/no CSV/JSON datasets. Set ZIP_MEMBER explicitly; no fallback selection.')
            name = member or candidates[0]
            if name not in candidates:
                raise ValueError('Requested ZIP member is absent or unsupported')
            payload = archive.read(name)
    text = payload.decode('utf-8-sig', errors='strict')
    if Path(name).suffix.lower() == '.json':
        records = json.loads(text)
        if not isinstance(records, list) or not all(isinstance(r, dict) for r in records):
            raise ValueError('JSON dataset must be a list of record objects')
    elif Path(name).suffix.lower() == '.csv':
        reader = csv.DictReader(io.StringIO(text, newline=''), strict=True)
        if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError('Missing or duplicate CSV headers')
        records = list(reader)
        if any(None in r or any(v is None for v in r.values()) for r in records):
            raise ValueError('Malformed CSV row width')
    else:
        raise ValueError('Use an explicit UTF-8 CSV, JSON or ZIP input')
    if not records:
        raise ValueError('Dataset contains no records')
    return records, dict(container_sha256=digest(path), member=name,
        member_sha256=hashlib.sha256(payload).hexdigest(), loaded_records=len(records), encoding='strict UTF-8')


def normalized(text):
    # Preserve case, spelling, URLs, numbers and punctuation. No translation/NFC rewriting.
    return re.sub(r'\s+', ' ', text).strip()


def audit_records(records):
    staged, ledger = [], []
    ids = set()
    for i, record in enumerate(records):
        identity = str(record.get('id', f'row-{i:06d}'))
        if identity in ids:
            raise ValueError('Duplicate record IDs; resolve lineage before training')
        ids.add(identity)
        raw = record.get('text', record.get('text_redacted'))
        reason = None
        if not isinstance(raw, str) or not raw.strip():
            reason = 'missing_or_empty_text'
        elif '\ufffd' in raw or '\x00' in raw or any(0xd800 <= ord(c) <= 0xdfff for c in raw):
            reason = 'malformed_text_or_encoding'
        try:
            label = label_value(record.get('label'))
        except ValueError:
            label = None
            reason = reason or 'unsupported_label_requires_review'
        if str(record.get('needs_review', '')).lower() == 'true':
            reason = reason or 'pending_manual_review'
        text = normalized(raw) if isinstance(raw, str) else ''
        key = text.casefold()
        staged.append(dict(record, id=identity, raw_text=raw, original_label=record.get('label'),
            text=text, label=label, source=record.get('source') or 'Unknown',
            language=record.get('language') or 'Unknown', category=record.get('category') or 'Unknown'))
        ledger.append(dict(row=i, id=identity, reason=reason, text_changed=raw != text, key_sha256=hashlib.sha256(key.encode('utf-8', errors='surrogatepass')).hexdigest()))
    buckets = defaultdict(list)
    for i, r in enumerate(staged):
        if r['text'] and r['label'] is not None:
            buckets[r['text'].casefold()].append(i)
    conflicts = {key for key, ii in buckets.items() if len({staged[i]['label'] for i in ii}) > 1}
    # Keep matching texts (including cross-source copies) together rather than discard lineage.
    retained = []
    for r, entry in zip(staged, ledger):
        if r['text'].casefold() in conflicts:
            entry['reason'] = 'conflicting_exact_labels_requires_review'
        if entry['reason'] is None:
            retained.append(r)
    eligible_buckets = Counter(r['text'].casefold() for r in retained)
    audit = dict(input_records=len(records), eligible_records=len(retained),
        unique_raw_messages=len({r.get('text', r.get('text_redacted')) for r in records if isinstance(r.get('text', r.get('text_redacted')), str)}),
        unique_normalized_messages=len(eligible_buckets), exact_duplicate_extra_rows=sum(v-1 for v in eligible_buckets.values()),
        conflicting_exact_groups=len(conflicts), exclusions=dict(Counter(e['reason'] for e in ledger if e['reason'])),
        missing={k:sum(r.get(k) is None or isinstance(r.get(k),str) and not r[k].strip() for r in records)
            for k in ('text','label','source','language','category','received_at','sender','campaign','conversation')},
        distributions={k:dict(Counter(str(r[k]) for r in retained)) for k in ('label','source','language','category')},
        label_mapping={'0':'ham (inherited, independently unverified)', '1':'smishing (positive, inherited, independently unverified)'},
        preprocessing='Collapse whitespace only before vectorization; preserve raw text/original labels privately; no translation/stemming/stopwords',
        label_quality='No silent relabeling; generic spam/marketing are unsupported without explicit phishing labels',
        limitations=['Source categories and language metadata are inherited, not verified annotations',
            'Masked existing views have already replaced identifiers/links; raw traffic performance needs independent testing',
            'No verified receipt timestamps: chronological evaluation unavailable',
            'Entire available study corpus historically exposed; no untouched test claim',
            'Published source licenses do not establish all acquisition/privacy/redistribution rights'])
    return retained, ledger, audit


def group_records(rows):
    groups = np.asarray(make_groups(rows))
    parent = {int(g):int(g) for g in groups}
    def root(g):
        while parent[g] != g:
            parent[g] = parent[parent[g]]
            g = parent[g]
        return g
    for field in ('campaign', 'sender', 'conversation'):
        seen = {}
        for i, row in enumerate(rows):
            value = row.get(field)
            if value not in (None, '', 'Unknown'):
                # Metadata identifiers are scoped to their source, not globally guessed.
                key = (row['source'], str(value))
                if key in seen:
                    parent[root(int(groups[i]))] = root(seen[key])
                seen[key] = int(groups[i])
    # Explicit exact Unicode casefold equality guards gaps in the ASCII heuristic.
    seen = {}
    for i, row in enumerate(rows):
        key = row['text'].casefold()
        if key in seen:
            parent[root(int(groups[i]))] = root(seen[key])
        seen[key] = int(groups[i])
    return np.array([root(int(g)) for g in groups])


def make_split(rows, groups, seed=42):
    y = np.array([r['label'] for r in rows])
    if set(y) != {0, 1} or min(Counter(y).values()) < 20 or any(len(set(groups[y==c])) < 20 for c in (0,1)):
        raise ValueError('70/15/15 group split requires >=20 independent groups per class; document a small-sample protocol instead')
    folds = [held for _,held in StratifiedGroupKFold(n_splits=20, shuffle=True, random_state=seed).split(np.arange(len(rows)), y, groups)]
    split = {p:np.concatenate(folds[a:b]).tolist() for p,a,b in [('train',0,14),('validation',14,17),('test',17,20)]}
    validate_split(rows, groups, split)
    return split


def validate_split(rows, groups, split):
    flat = [i for p in split.values() for i in p]
    if len(flat) != len(rows) or set(flat) != set(range(len(rows))):
        raise ValueError('Partition IDs must form a complete disjoint cover')
    for p, ids in split.items():
        if {rows[i]['label'] for i in ids} != {0,1}:
            raise ValueError(f'{p} lacks both classes; no favorable-seed retry')
        for q, jj in split.items():
            if p < q and (set(groups[ids]) & set(groups[jj]) or
                {rows[i]['text'].casefold() for i in ids} & {rows[j]['text'].casefold() for j in jj}):
                raise ValueError('Exact/near/metadata component crosses partitions')


def matrix():
    entries = []
    for family, algorithm, combined in [('A','lr',False),('B','svm',False),('C','svm',True),('D','lr',True),('E','nb',False)]:
        settings = [(1,None,[1,1],[3,5]),(2,20000,[1,2],[3,5])]
        if combined:
            settings = [(1,None,[1,2],[3,5]),(2,30000,[1,2],[3,5]),(2,15000,[1,2],[3,6])]
        for df,limit,word,char in settings:
            for value in ((.03,.1,.3,1.,3.) if algorithm=='nb' else (.1,1.,10.)):
                for weighting in ([None] if algorithm=='nb' else [None,'balanced']):
                    entries.append(dict(id=f'{family}-{len(entries):03d}',family=family,algorithm=algorithm,combined=combined,
                        min_df=df,max_features=limit,word_ngrams=word,char_ngrams=char,value=value,class_weight=weighting))
    # Every family first fits original distribution; paired class-weight comparisons follow.
    return sorted(entries, key=lambda e:(e['class_weight'] is not None, e['family'], e['id']))


def vectorizer(spec):
    params = dict(min_df=spec['min_df'],max_features=spec['max_features'],lowercase=True,
        norm='l2',sublinear_tf=False,smooth_idf=True,stop_words=None)
    word = TfidfVectorizer(ngram_range=tuple(spec['word_ngrams']), **params)
    return FeatureUnion([('word',word),('char',TfidfVectorizer(analyzer='char_wb',ngram_range=tuple(spec['char_ngrams']),**params))]) if spec['combined'] else word


def pipeline(spec, seed):
    if spec['algorithm']=='lr':
        classifier = LogisticRegression(C=spec['value'], class_weight=spec['class_weight'], solver='liblinear', max_iter=2000, random_state=seed)
    elif spec['algorithm']=='svm':
        classifier = LinearSVC(C=spec['value'],class_weight=spec['class_weight'],dual='auto',max_iter=10000,random_state=seed)
    else:
        classifier = MultinomialNB(alpha=spec['value'])
    return Pipeline([('tfidf',vectorizer(spec)),('classifier',classifier)])


def margins(pipe, texts):
    if pipe['classifier'].classes_.tolist() != [0,1]:
        raise ValueError('Positive class mapping changed')
    x = pipe['tfidf'].transform(texts)
    c = pipe['classifier']
    return c.predict_log_proba(x)[:,1]-c.predict_log_proba(x)[:,0] if isinstance(c,MultinomialNB) else c.decision_function(x)


def fit(rows, groups, ids, spec, seed=42):
    ids = np.array(ids, dtype=int); y = np.array([rows[i]['label'] for i in ids]); texts = [rows[i]['text'] for i in ids]
    started = time.perf_counter(); folds=[]; oof=np.full(len(ids),np.nan)
    for a,b in StratifiedGroupKFold(n_splits=3, shuffle=True, random_state=seed).split(ids,y,groups[ids]):
        if set(y[a]) != {0,1} or set(y[b]) != {0,1} or set(groups[ids[a]]) & set(groups[ids[b]]):
            raise ValueError('Invalid training-only grouped calibration fold')
        p=pipeline(spec,seed).fit([texts[i] for i in a],y[a]); oof[b]=margins(p,[texts[i] for i in b])
        folds.append(dict(train=ids[a].tolist(),calibration=ids[b].tolist()))
    if not np.isfinite(oof).all():
        raise ValueError('Incomplete OOF calibration predictions')
    cal=LogisticRegression(C=1,solver='lbfgs',random_state=seed).fit(oof.reshape(-1,1),y)
    if cal.coef_[0,0] <= 0:
        raise ValueError('Nonmonotone calibration: do not export reversed phishing scores')
    p=pipeline(spec,seed).fit(texts,y)
    x=p['tfidf'].transform(texts).tocsr()
    return dict(pipe=p,calibrator=cal,spec=spec,seed=seed,training_ids=ids.tolist(),calibration_folds=folds,
        training_seconds=time.perf_counter()-started,feature_count=x.shape[1],
        sparse_training_bytes=x.data.nbytes+x.indices.nbytes+x.indptr.nbytes)


def score(artifact, texts, mode):
    if not all(isinstance(t,str) for t in texts):
        raise ValueError('Prediction input must contain strings')
    m=margins(artifact['pipe'],[normalized(t) for t in texts])
    if mode=='sigmoid':
        return artifact['calibrator'].predict_proba(m.reshape(-1,1))[:,1]
    if artifact['spec']['algorithm']=='svm':
        return m
    # Stable conversion of log odds for LR/NB.
    from scipy.special import expit
    return expit(m)


def metrics(y, scores, threshold, probability):
    y=np.asarray(y); s=np.asarray(scores); pred=s>=threshold
    if not len(y) or not np.isfinite(s).all():
        raise ValueError('Nonempty finite scores required')
    if probability and ((s<0)|(s>1)).any():
        raise ValueError('Probability must lie in [0,1]')
    tn,fp,fn,tp=[int(n) for n in confusion_matrix(y,pred,labels=[0,1]).ravel()]
    both=set(y)=={0,1}
    p,r,_=precision_recall_curve(y,s) if both else (None,None,None)
    return dict(records=len(y),accuracy=float(accuracy_score(y,pred)),precision=float(precision_score(y,pred,zero_division=0)),
        recall=float(recall_score(y,pred,zero_division=0)),f1=float(f1_score(y,pred,zero_division=0)),
        macro_f1=float(f1_score(y,pred,labels=[0,1],average='macro',zero_division=0)),
        average_precision=float(average_precision_score(y,s)) if both else None,
        pr_auc=float(auc(r,p)) if both else None,roc_auc=float(roc_auc_score(y,s)) if both else None,
        confusion=dict(tn=tn,fp=fp,fn=fn,tp=tp),fpr=fp/(tn+fp) if tn+fp else None,
        brier=float(brier_score_loss(y,s)) if probability else None,probability_estimate=probability)


def choose_threshold(y, scores, probability):
    y=np.asarray(y);s=np.asarray(scores)
    order=np.argsort(-s,kind='stable'); ordered=s[order]
    thresholds=np.unique(np.r_[s,np.nextafter(s,np.inf)])
    cuts=np.searchsorted(-ordered,-thresholds,side='right')
    tp=np.r_[0,np.cumsum(y[order]==1)][cuts];fp=np.r_[0,np.cumsum(y[order]==0)][cuts]
    precision=np.divide(tp,tp+fp,out=np.zeros(len(tp)),where=(tp+fp)>0)
    eligible=np.flatnonzero((precision>=POLICY['precision_floor']) & (fp/max(1,int((y==0).sum()))<=POLICY['fpr_ceiling']) & (tp>=POLICY['minimum_tp']))
    if not len(eligible):
        return None
    j=max(eligible,key=lambda j:(int(tp[j]),2*tp[j]/(tp[j]+fp[j]+int((y==1).sum())),float(thresholds[j])))
    return dict(threshold=float(thresholds[j]),metrics=metrics(y,s,float(thresholds[j]),probability))


def rank(candidate):
    m=candidate['validation'];return (m['recall'],m['f1'],m['average_precision'],-candidate['artifact_bytes'],candidate['id'])


def subgroup_metrics(rows, ids, scores, threshold, probability):
    out={}
    for field in ('language','source','category'):
        for value in sorted({rows[i][field] for i in ids}):
            jj=[j for j,i in enumerate(ids) if rows[i][field]==value];y=[rows[ids[j]]['label'] for j in jj]
            support=Counter(y); adequate=len(jj)>=20 and min(support[0],support[1])>=5
            out[f'{field}:{value}']=dict(records=len(jj),ham=support[0],phishing=support[1],
                adequate_two_class_support=adequate,interpretation='descriptive inherited subgroup; not independently validated',
                metrics=metrics(y,np.asarray(scores)[jj],threshold,probability) if adequate else None)
    return out


def robustness(artifact, rows, ids, mode, threshold):
    # Deterministic surface edits of existing validation SMS, never generated research records.
    texts=[rows[i]['text'] for i in ids];y=[rows[i]['label'] for i in ids]
    original=score(artifact,texts,mode)>=threshold
    transforms={'uppercase':lambda t:t.upper(),'extra_whitespace':lambda t:'  '+t.replace(' ','  \t ')+'  ',
        'terminal_punctuation':lambda t:t+'!!!', 'spelling_noise':lambda t:re.sub(r'(?i)\b(account|verify|payment)\b',lambda m:{'account':'acc0unt','verify':'ver1fy','payment':'paym3nt'}[m[0].lower()],t),
        'taglish_spelling':lambda t:re.sub(r'(?i)\b(hindi|kailangan|ngayon)\b',lambda m:{'hindi':'hndi','kailangan':'kelangan','ngayon':'ngaun'}[m[0].lower()],t)}
    out={}
    for name,transform in transforms.items():
        edited=[transform(t) for t in texts];changed=[i for i,(a,b) in enumerate(zip(texts,edited)) if a!=b]
        s=score(artifact,edited,mode)
        out[name]=dict(records=len(ids),changed_records=len(changed),prediction_flips=int(np.sum((s>=threshold)!=original)),
            metrics=metrics(y,s,threshold,mode=='sigmoid' or artifact['spec']['algorithm']!='svm'),
            changed_subset_metrics=metrics(np.asarray(y)[changed],s[changed],threshold,mode=='sigmoid' or artifact['spec']['algorithm']!='svm') if changed else None,
            limitation='Assumed label-preserving surface edit; spelling variants need manual semantic review; no adversarial-security claim')
    return out


def environment():
    versions={n:importlib.metadata.version(n) for n in ('numpy','scipy','scikit-learn','matplotlib','joblib','threadpoolctl')}
    return dict(python=sys.version,unicode=unicodedata.unidata_version,platform=platform.platform(),packages=versions,
        threads=1,transformer=dict(torch_available=bool(importlib.util.find_spec('torch')),
        transformers_available=bool(importlib.util.find_spec('transformers')),
        checkpoint_cached=bool(list((Path.home()/'.cache/huggingface/hub').glob('models--*xlm*'))),
        status='XLM-R not executed: current research env lacks torch/transformers and a pinned local checkpoint. Existing mBERT is a different model.'))


def train(dataset, output, history, member=None, seed=42):
    output=Path(output)
    if history!='previously_used':
        raise ValueError('This inherited-label adapter supports retrospective research only; use reviewed prospective intake workflow for new final data')
    records,identity=read_input(dataset,member)
    rows,ledger,audit=audit_records(records)
    output.mkdir(parents=True,exist_ok=False)
    save(output/'original-records.json',records);save(output/'dataset.json',rows);save(output/'cleaning-ledger.json',ledger)
    groups=group_records(rows);split=make_split(rows,groups,seed)
    audit.update(template_groups=len(set(groups)),mixed_label_groups=sum(len({rows[i]['label'] for i in range(len(rows)) if groups[i]==g})>1 for g in set(groups)),
        group_policy='Existing label-blind .85 normalized SequenceMatcher connected components plus exact Unicode casefold and supplied template/campaign/sender/conversation groups',
        source_isolation='Sources deliberately span partitions; only three sources cannot support 70/15/15 whole-source splits. Source-transfer diagnostics are separate.',
        input=identity,partitions={p:dict(records=len(ii),groups=len(set(groups[ii])),labels=dict(Counter(str(rows[i]['label']) for i in ii)),fraction=len(ii)/len(rows)) for p,ii in split.items()},
        pairwise_group_overlap={a+'-'+b:len(set(groups[split[a]])&set(groups[split[b]])) for a in split for b in split if a<b})
    save(output/'data-audit.json',audit);save(output/'splits.json',dict(partitions=split,groups=groups.tolist(),seed=seed,target=[.70,.15,.15]))
    save(output/'environment.json',environment())
    specs=matrix();save(output/'configuration.json',dict(matrix=specs,policy=POLICY,history=history,
        calibration='3 training-only group folds, fold-local feature fitting, OOF sigmoid then train-only refit; no resampling',
        ranking='Compare raw and calibrated scores separately; SVM margins never probabilities',
        seed=seed,repeat_training_seeds=[seed,seed+1,seed+2]))
    val=split['validation'];texts=[rows[i]['text'] for i in val];y=[rows[i]['label'] for i in val]
    candidates=[];failures=[];start=time.perf_counter()
    with threadpool_limits(limits=1):
        for number,spec in enumerate(specs,1):
            folder=output/spec['id'];folder.mkdir()
            try:
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter('always');a=fit(rows,groups,split['train'],spec,seed)
                if caught:
                    raise ValueError('Fitting warning: '+ ';'.join(type(w.message).__name__ for w in caught))
                model=folder/'pipeline.pkl';model.write_bytes(pickle.dumps(a,protocol=5))
                for mode in ('raw','sigmoid'):
                    s=score(a,texts,mode);probability=mode=='sigmoid' or spec['algorithm']!='svm'
                    default=metrics(y,s,0 if spec['algorithm']=='svm' and mode=='raw' else .5,probability)
                    op=choose_threshold(y,s,probability)
                    row=dict(id=spec['id']+'-'+mode,fit_id=spec['id'],family=spec['family'],spec=spec,mode=mode,
                        threshold=op['threshold'] if op else None,validation=op['metrics'] if op else None,
                        default_validation=default,feasible=op is not None,training_seconds=a['training_seconds'],
                        artifact_bytes=model.stat().st_size,feature_count=a['feature_count'],sparse_training_bytes=a['sparse_training_bytes'])
                    save(folder/f'validation-{mode}.json',dict(indices=val,labels=y,scores=s.tolist(),result=row))
                    candidates.append(row)
            except (ValueError,RuntimeError) as error:
                failures.append(dict(id=spec['id'],reason=str(error)))
            if number%10==0:
                print(f'Fitted {number}/{len(specs)} configurations',flush=True)
        winners={family:max([c for c in candidates if c['family']==family and c['feasible']],key=rank) for family in 'ABCDE' if any(c['family']==family and c['feasible'] for c in candidates)}
        selected=max(winners.values(),key=rank) if winners else None
        # Seeds change fitting/calibration only; split, spec/mode and threshold stay locked.
        variability=[]
        if selected:
            for repeat_seed in (seed+1,seed+2):
                a=fit(rows,groups,split['train'],selected['spec'],repeat_seed)
                variability.append(dict(seed=repeat_seed,validation=metrics(y,score(a,texts,selected['mode']),selected['threshold'], selected['mode']=='sigmoid' or selected['spec']['algorithm']!='svm')))
        save(output/'validation-results.json',dict(candidates=candidates,failures=failures,seconds=time.perf_counter()-start))
        save(output/'selection.json',dict(selected=selected,family_winners=winners,policy=POLICY,
            history=history,interpretation='Validation-selected retrospective research candidate; production unchanged; no future-traffic winner',
            seed_variability=variability))
        if selected:
            a=pickle.loads((output/selected['fit_id']/'pipeline.pkl').read_bytes())
            save(output/'robustness-validation.json',robustness(a,rows,val,selected['mode'],selected['threshold']))
            save(output/'subgroups-validation.json',subgroup_metrics(rows,val,score(a,texts,selected['mode']),selected['threshold'],selected['mode']=='sigmoid' or selected['spec']['algorithm']!='svm'))
            diagnostic_models(rows,groups,split,selected,output)
            export_candidate(a,selected,output)
    protected={str(p.relative_to(output)):digest(p) for p in output.rglob('*') if p.is_file() and p.name!='freeze.json'}
    save(output/'freeze.json',dict(files=protected,source_sha256=digest(Path(__file__)),dataset_sha256=digest(dataset),
        history=history,selected_id=selected['id'] if selected else None))
    plot_development(output)
    print(f'Selected: {selected["id"] if selected else "none feasible"}; frozen before holdout prediction',flush=True)
    return output


def diagnostic_models(rows,groups,split,selected,output):
    ids=split['train']; val=split['validation'];y=[rows[i]['label'] for i in val]; out={}
    # Shortcut controls fit on training only. They never enter candidate selection.
    for view in ('source_only','link_marker_only'):
        def representation(r):
            return r['source'] if view=='source_only' else ('haslink' if re.search(r'(?i)zzurlzz|https?://|www\.',r['text']) else 'nolink')
        p=Pipeline([('v',TfidfVectorizer()),('m',LogisticRegression(random_state=42))]).fit([representation(rows[i]) for i in ids],[rows[i]['label'] for i in ids])
        s=p.predict_proba([representation(rows[i]) for i in val])[:,1]
        out[view]=metrics(y,s,.5,True)
    artifact=pickle.loads((output/selected['fit_id']/'pipeline.pkl').read_bytes())
    texts=[rows[i]['text'] for i in val]
    s=score(artifact,[re.sub(r'(?i)zzurlzz|https?://\S+|www\.\S+',' ',t) for t in texts],selected['mode'])
    out['selected_frozen_url_removal']=dict(metrics=metrics(y,s,selected['threshold'],selected['mode']=='sigmoid' or selected['spec']['algorithm']!='svm'),
        interpretation='Frozen feature ablation on validation; not a newly trained model or a label-preserving robustness claim')
    save(output/'shortcut-validation.json',out)
    # Transfer diagnostics: frozen spec/mode/threshold, train complement only.
    # These use validation rows from a source, never the reserved holdout.
    transfer={}
    for source in sorted({r['source'] for r in rows}):
        held=[i for i in val if rows[i]['source']==source]; held_groups=set(groups[held])
        training=[i for i in ids if rows[i]['source']!=source and groups[i] not in held_groups]
        if not held or {rows[i]['label'] for i in training}!={0,1}:
            transfer[source]=dict(status='Insufficient supported complement');continue
        a=fit(rows,groups,training,selected['spec'],42)
        s=score(a,[rows[i]['text'] for i in held],selected['mode'])
        transfer[source]=dict(training_records=len(training),held_records=len(held),
            metrics=metrics([rows[i]['label'] for i in held],s,selected['threshold'],selected['mode']=='sigmoid' or selected['spec']['algorithm']!='svm'),
            status='Development transfer stress test; selected spec/threshold influenced by these validation records; not independent source-generalization evidence')
    save(output/'source-transfer-validation.json',transfer)


def export_candidate(artifact, selected, output):
    if unicodedata.unidata_version!='15.0.0':
        raise ValueError('Native Unicode export needs Python 3.12 / Unicode 15.0.0')
    pipe=artifact['pipe'];clf=pipe['classifier'];feature=pipe['tfidf']
    blocks=feature.transformer_list if isinstance(feature,FeatureUnion) else [('word',feature)]
    exported=[]
    for name,v in blocks:
        exported.append(dict(analyzer=v.analyzer,ngram_range=list(v.ngram_range),
            vocabulary=v.get_feature_names_out().tolist(),idf=v.idf_.tolist(),norm='l2',tf='raw'))
    weights=(clf.feature_log_prob_[1]-clf.feature_log_prob_[0]) if isinstance(clf,MultinomialNB) else clf.coef_[0]
    bias=float(clf.class_log_prior_[1]-clf.class_log_prior_[0]) if isinstance(clf,MultinomialNB) else float(clf.intercept_[0])
    calibration=(dict(a=float(artifact['calibrator'].coef_[0,0]),b=float(artifact['calibrator'].intercept_[0])) if selected['mode']=='sigmoid'
        else dict(a=1.,b=0.) if selected['spec']['algorithm']!='svm' else None)
    contract=dict(schema_version=7,research_contract='word-char-linear-v1',algorithm=selected['spec']['algorithm'],
        input_view='whitespace_normalized_existing_masked_text',blocks=exported,weights=weights.tolist(),bias=bias,
        calibration=calibration,threshold=selected['threshold'],threshold_comparison='greater_or_equal',
        classes=['ham','smishing'],positive_class='smishing',unicode=unicode_contract(),
        whitespace_codepoints=[i for i in range(sys.maxunicode+1) if chr(i).isspace()],
        probability_approved=False,automatic_warnings_approved=False,evaluation_status='retrospective_inherited_labels',
        preprocessing='Whitespace collapse; Python Unicode lowercase; word min2 no stopwords; char_wb codepoint slices; independent block L2 norms',
        configuration=selected,calibration_status='training_OOF_fitted; heldout reliability diagnostic; no real-traffic probability claim')
    save(output/'candidate-model.json',contract)
    texts=['', '   ', '\x00', '??? 123 🌟', 'qzxv qzxv', 'Hello, kumusta na?',
        'Do not share your OTP. Payment PHP 123.45 received.', 'I-verify ang account mo sa https://example.invalid',
        'ACCOUNT\taccount\nverify', 'İ Σ ΟΣ 𐐀 Ñ ñ e\u0301', 'A\u00a0B\u2003hello',
        'single a I x', ' a   b  ', 'hi', 'Paki bayad ngayon, wag i-share ang code.', '𝔸𝔹𝔠 verify',
        'one\u001ctwo', '💬code\u2028hello', 'x'*20,'hello '*2000]
    cases=[];reference=score(artifact,texts,selected['mode'])
    for text,s in zip(texts,reference):
        x=feature.transform([normalized(text)]).tocsr()
        cases.append(dict(text=text,score=float(s),suspicious=bool(s>=selected['threshold']),
            features={str(i):float(v) for i,v in zip(x.indices,x.data)}))
    save(output/'candidate-cases.json',dict(cases=cases,synthetic=True,tolerance=1e-10))


def verify_freeze(dataset, output):
    frozen=load(output/'freeze.json')
    if digest(dataset)!=frozen['dataset_sha256'] or digest(Path(__file__))!=frozen['source_sha256']:
        raise ValueError('Dataset or code changed since freeze')
    for name,sha in frozen['files'].items():
        if digest(output/name)!=sha:
            raise ValueError('Frozen artifact changed: '+name)
    return frozen


def evaluate(dataset, output):
    output=Path(output); frozen=verify_freeze(dataset,output)
    selection=load(output/'selection.json');rows=load(output/'dataset.json');manifest=load(output/'splits.json')
    split=manifest['partitions'];groups=np.array(manifest['groups']);validate_split(rows,groups,split)
    # Marker precedes any test transformation: interrupted evaluation also fails closed.
    with (output/'holdout-started.json').open('x',encoding='utf-8') as handle:
        json.dump(dict(freeze_sha256=digest(output/'freeze.json'),history=frozen['history']),handle)
    ids=split['test'];texts=[rows[i]['text'] for i in ids];y=[rows[i]['label'] for i in ids]; results={}
    with threadpool_limits(limits=1):
        for family,c in selection['family_winners'].items():
            a=pickle.loads((output/c['fit_id']/'pipeline.pkl').read_bytes())
            start=time.perf_counter();s=score(a,texts,c['mode']);batch=time.perf_counter()-start
            # Warm single-SMS end-to-end latency, fixed representative prefix, no labels used.
            latency=[]
            for text in texts[:min(100,len(texts))]:
                start=time.perf_counter();score(a,[text],c['mode']);latency.append((time.perf_counter()-start)*1000)
            probability=c['mode']=='sigmoid' or c['spec']['algorithm']!='svm'
            m=metrics(y,s,c['threshold'],probability)
            results[family]=dict(candidate=c,holdout=m,subgroups=subgroup_metrics(rows,ids,s,c['threshold'],probability),
                latency=dict(host_batch_ms_per_sms=1000*batch/len(texts),host_single_p50_ms=float(np.median(latency)),host_single_p95_ms=float(np.quantile(latency,.95)),samples=len(latency),android='Separate JVM and instrumentation checks; physical-device benchmark pending'),
                predictions_file=f'holdout-{family}-predictions.json')
            save(output/f'holdout-{family}-predictions.json',dict(indices=ids,labels=y,scores=s.tolist(),threshold=c['threshold']))
    selected=selection['selected']
    if selected:
        family=selected['family'];predictions=load(output/f'holdout-{family}-predictions.json')
        # Anonymous ledger; original texts remain private in dataset.json.
        errors=[dict(row_index=i,id=rows[i]['id'],label=int(label),score=s,kind='false_positive' if label==0 else 'false_negative',human_label='',review_reference='')
            for i,label,s in zip(ids,y,predictions['scores']) if (s>=selected['threshold'])!=bool(label)]
        save(output/'private-error-review.json',errors)
        results[family]['conditional_cluster_intervals']=bootstrap(y,predictions['scores'],groups[ids],selected['threshold'])
    save(output/'holdout-results.json',dict(results=results,selected_id=selected['id'] if selected else None,
        history=frozen['history'],interpretation='Historically exposed holdout; family winners locked before this run. Cannot establish prospective performance. Never reselect using these results.'))
    plot_holdout(output)
    print('Locked retrospective holdout evaluation complete; no production model replaced')


def bootstrap(y,scores,groups,threshold,repetitions=1000):
    y=np.array(y);s=np.array(scores);groups=np.array(groups);unique=np.unique(groups);rng=np.random.default_rng(42); samples=[]
    members={g:np.flatnonzero(groups==g) for g in unique}
    for _ in range(repetitions):
        ii=np.concatenate([members[g] for g in rng.choice(unique,len(unique),replace=True)])
        if set(y[ii])=={0,1}:
            samples.append([recall_score(y[ii],s[ii]>=threshold),precision_score(y[ii],s[ii]>=threshold,zero_division=0),f1_score(y[ii],s[ii]>=threshold)])
    if not samples:
        return dict(status='Insufficient two-class bootstrap support')
    intervals=np.quantile(samples,[.025,.975],axis=0)
    return dict(seed=42,repetitions=repetitions,valid=len(samples),
        intervals={name:dict(low=float(intervals[0,j]),high=float(intervals[1,j])) for j,name in enumerate(('recall','precision','f1'))},
        scope='Fixed selected model/threshold, cluster percentile bootstrap; excludes label, exposure, selection and training uncertainty')


def plotting():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    return plt


def plot_development(output):
    plt=plotting();audit=load(output/'data-audit.json');fig,axes=plt.subplots(1,3,figsize=(13,4))
    for ax,field in zip(axes,('label','language','source')):
        d=audit['distributions'][field]; ax.bar(d.keys(),d.values());ax.set_title(field+' coverage');ax.tick_params(axis='x',rotation=20)
    fig.tight_layout();fig.savefig(output/'coverage.png',dpi=160);plt.close(fig)


def plot_holdout(output):
    plt=plotting();results=load(output/'holdout-results.json')['results']
    if not results:return
    fig,axes=plt.subplots(2,len(results),figsize=(4*len(results),7),squeeze=False)
    fig_pr,ax_pr=plt.subplots(figsize=(7,5));fig_cal,ax_cal=plt.subplots(figsize=(7,5))
    for j,(family,item) in enumerate(results.items()):
        pred=load(output/item['predictions_file']);y=pred['labels'];s=pred['scores'];m=item['holdout'];c=m['confusion']
        cm=np.array([[c['tn'],c['fp']],[c['fn'],c['tp']]])
        axes[0,j].imshow(cm,cmap='Blues');axes[0,j].set_title(f'Family {family}: retrospective')
        axes[0,j].set_xticks([0,1],['ham','phishing']);axes[0,j].set_yticks([0,1],['ham','phishing']);axes[0,j].set_xlabel('Predicted');axes[0,j].set_ylabel('True inherited label')
        for a in range(2):
            for b in range(2):axes[0,j].text(b,a,str(cm[a,b]),ha='center',va='center')
        axes[1,j].bar(['P','R','F1','Macro F1'],[m['precision'],m['recall'],m['f1'],m['macro_f1']]);axes[1,j].set_ylim(0,1)
        p,r,_=precision_recall_curve(y,s);ax_pr.plot(r,p,label=f'{family} AP={m["average_precision"]:.3f}')
        if m['probability_estimate']:
            fraction,mean=calibration_curve(y,s,n_bins=8,strategy='quantile');ax_cal.plot(mean,fraction,'o-',label=f'{family} Brier={m["brier"]:.4f}')
    fig.tight_layout();fig.savefig(output/'confusion-and-comparison.png',dpi=160);plt.close(fig)
    ax_pr.set(xlabel='Phishing recall',ylabel='Phishing precision',title='Historically exposed holdout PR curves');ax_pr.legend();fig_pr.tight_layout();fig_pr.savefig(output/'precision-recall.png',dpi=160);plt.close(fig_pr)
    ax_cal.plot([0,1],[0,1],'--',color='gray');ax_cal.set(xlabel='Mean estimated probability',ylabel='Observed inherited phishing fraction',title='Retrospective reliability; quantile bins');ax_cal.legend();fig_cal.tight_layout();fig_cal.savefig(output/'reliability.png',dpi=160);plt.close(fig_cal)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['train','evaluate']);p.add_argument('dataset',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--history',choices=['previously_used'],default='previously_used');p.add_argument('--zip-member');p.add_argument('--seed',type=int,default=42)
    args=p.parse_args()
    if args.command=='train':train(args.dataset,args.output,args.history,args.zip_member,args.seed)
    else:evaluate(args.dataset,args.output)


if __name__=='__main__':main()
