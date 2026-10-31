"""All previously used algorithm families on one preserved 80/20 membership.

Fresh fits, including word+character models, mBERT, voting and OOF stacking.
Fixed historical settings, training-only calibration, and one frozen test pass.
"""
from itertools import combinations
from pathlib import Path
import argparse
import importlib.metadata
import json
import pickle
import shutil
import time
import warnings

import numpy as np
from scipy.special import softmax, expit
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from threadpoolctl import threadpool_limits

from . import holdout_8020 as h, nb_comparison as n, retraining as r
from . import fair_compare as fair
from . import ensemble_mbert as bert
from .preprocessing import normalize as ascii_normalize

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT/'docs/all-algorithms-8020-20261019/PROTOCOL.md'
COMPONENTS = ('legacy-lr', 'legacy-svm', 'legacy-nb', 'mbert')
STACKS = (('legacy-lr','legacy-svm','legacy-nb'), ('mbert','legacy-svm','legacy-nb'))


def dump(path, obj):
    Path(path).write_bytes(pickle.dumps(obj, protocol=5))


def unpickle(path):
    return pickle.loads(Path(path).read_bytes())


def spec_matrix():
    historical = n.load(ROOT/'research/runs/retraining-20261013/notebook-run-v2/selection.json')['family_winners']
    specs = [dict(id='AE-'+f, kind='ae', spec=historical[f]['spec'], modes=['raw','sigmoid']) for f in 'ABCDE']
    specs += [dict(id='latest-'+s['id'], kind='latest', spec=s, modes=['raw']) for s in n.matrix()]
    specs += [dict(id='legacy-'+a, kind='legacy', algorithm=a, value=.1 if a == 'nb' else 10., modes=['sigmoid']) for a in ('lr','svm','nb')]
    specs += [dict(id='random-forest', kind='rf', modes=['raw']), dict(id='knn', kind='knn', modes=['raw'])]
    return specs


def source_hashes():
    return {p.name:n.digest(p) for p in Path(__file__).parent.glob('*.py')}


def prepare(previous, output, base):
    previous, output, base = Path(previous), Path(output), Path(base)
    dataset = ROOT/'research/data/newdata-20261013/smishguard_dataset_2026-10-12.zip'
    h.verify_freeze(dataset, previous)
    expected = {'model.safetensors':'876f584f15ebf14887dec17539c114bb99a032e96b9e72507a51c41e205337fc',
                'vocab.txt':'fe0fda7c425b48c516fc8f160d594c8022a0808447475c1a7c6d6479763f310c'}
    for name, sha in expected.items():
        if n.digest(base/name) != sha:
            raise ValueError('Pinned multilingual base changed: '+name)
    output.mkdir(parents=True, exist_ok=False)
    for name in ('dataset.json', 'splits.json', 'data-audit.json', 'cleaning-ledger.json'):
        shutil.copyfile(previous/name, output/name)
    shutil.copyfile(PROTOCOL, output/'protocol.md')
    code = output/'code'; code.mkdir()
    for path in Path(__file__).parent.glob('*.py'):
        shutil.copyfile(path, code/path.name)
    cfg = dict(matrix=spec_matrix(), base=str(base.resolve()), previous=str(previous.resolve()),
        previous_freeze_sha256=n.digest(previous/'freeze.json'), dataset_sha256=n.digest(output/'dataset.json'),
        split_sha256=n.digest(output/'splits.json'), source_hashes=source_hashes(), protocol_sha256=n.digest(PROTOCOL),
        base_files={p.name:n.digest(p) for p in base.iterdir() if p.is_file()},
        primary_metric='smishing-class F1', selection='No overall selection on test: report descriptive test leaders only',
        threshold='Raw SVM >=0; other standalone >=0.5; soft votes and stacks >0.5 (ties ham)',
        historical_exposure='Previous 80/20 results already viewed; retrospective extension on identical records',
        mbert='Pinned local multilingual cased base; fresh two fixed epochs per full/fold fit; no test checkpoint selection',
        excluded='XLM-R was not previously trained; quantized mBERT is an inference derivative, not another algorithm')
    n.save(output/'configuration.json', cfg)
    n.save(output/'environment.json', dict(packages={p:importlib.metadata.version(p) for p in ('numpy','scipy','scikit-learn','torch','transformers','threadpoolctl')},
        timestamp_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())))
    print('Prepared',len(cfg['matrix']),'classical fit settings, their raw/calibrated variants, mBERT, 11 votes and 2 stacks.',flush=True)


def context(output):
    output = Path(output); cfg = n.load(output/'configuration.json')
    if source_hashes() != cfg['source_hashes'] or n.digest(PROTOCOL) != cfg['protocol_sha256']:
        raise ValueError('Source/protocol changed since preparation')
    if n.digest(output/'dataset.json') != cfg['dataset_sha256'] or n.digest(output/'splits.json') != cfg['split_sha256']:
        raise ValueError('Dataset/membership changed')
    rows = n.load(output/'dataset.json'); split = n.load(output/'splits.json')
    n.validate_split(rows, np.asarray(split['groups']), split['partitions'])
    return cfg, rows, split


def pipe(spec):
    if spec['kind'] == 'ae':
        return r.pipeline(spec['spec'], h.SEED)
    if spec['kind'] == 'latest':
        return Pipeline([('tfidf',n.vectorizer()),('classifier',h.classifier(spec['spec']))])
    if spec['kind'] == 'legacy':
        vec = fair.vectorizer().set_params(preprocessor=ascii_normalize)
        return Pipeline([('tfidf',vec),('classifier',fair.classifier(spec['algorithm'],spec['value']))])
    vec = TfidfVectorizer(lowercase=True,ngram_range=(1,2),max_features=5000,token_pattern=r'\b\w+\b')
    model = (RandomForestClassifier(n_estimators=200,class_weight='balanced',random_state=42,n_jobs=1)
             if spec['kind'] == 'rf' else KNeighborsClassifier(n_neighbors=5,n_jobs=1))
    return Pipeline([('tfidf',vec),('classifier',model)])


def raw_score(fitted, texts):
    model = fitted['classifier']
    if model.classes_.tolist() != [0,1]:
        raise ValueError('Class mapping changed')
    x = fitted['tfidf'].transform(texts)
    if hasattr(model, 'predict_log_proba') and type(model).__name__ == 'MultinomialNB':
        p = model.predict_log_proba(x)
        return p[:,1]-p[:,0]
    if hasattr(model,'decision_function'):
        return np.asarray(model.decision_function(x))
    p = model.predict_proba(x)[:,1]
    return np.log(np.clip(p,1e-15,1-1e-15)/np.clip(1-p,1e-15,1))


def is_svm(spec):
    return (spec.get('algorithm') == 'svm' or spec.get('spec',{}).get('algorithm') == 'svm')


def fit_model(rows, groups, ids, spec):
    y = np.array([rows[i]['label'] for i in ids]); cal = None; records = []
    if 'sigmoid' in spec['modes']:
        values = np.full(len(ids), np.nan); positions = {i:j for j,i in enumerate(ids)}
        for fold in h.training_folds(rows, groups, ids):
            p = pipe(spec).fit([rows[i]['text'] for i in fold['train']],[rows[i]['label'] for i in fold['train']])
            values[[positions[i] for i in fold['validation']]] = raw_score(p,[rows[i]['text'] for i in fold['validation']])
            records.append(fold)
        if not np.isfinite(values).all():
            raise ValueError('Incomplete calibration OOF')
        cal = LogisticRegression(C=1,solver='lbfgs',random_state=42,max_iter=2000).fit(values.reshape(-1,1),y)
        if cal.coef_[0,0] <= 0:
            raise ValueError('Nonmonotone training-only sigmoid')
    fitted = pipe(spec).fit([rows[i]['text'] for i in ids], y)
    return dict(pipe=fitted, calibrator=cal, training_ids=list(ids), calibration_folds=records, spec=spec)


def scores(artifact, texts, mode):
    raw = raw_score(artifact['pipe'], texts)
    if mode == 'sigmoid':
        return artifact['calibrator'].predict_proba(raw.reshape(-1,1))[:,1]
    return raw if is_svm(artifact['spec']) else expit(raw)


def classical(output):
    output = Path(output); cfg, rows, split = context(output)
    if (output/'freeze.json').exists() or (output/'test-started.json').exists():
        raise ValueError('Training is closed')
    groups = np.asarray(split['groups']); ids = split['partitions']['train']; index = {i:j for j,i in enumerate(ids)}
    y = [rows[i]['label'] for i in ids]; results = []
    with threadpool_limits(limits=1):
        for spec in cfg['matrix']:
            folder = output/spec['id']
            if (folder/'training-complete.json').exists():
                print('Reusing completed',spec['id'],flush=True)
                results.extend(n.load(folder/'training-complete.json')); continue
            folder.mkdir(exist_ok=False)
            started = time.perf_counter()
            oof = {mode:np.full(len(ids),np.nan) for mode in spec['modes']}; fold_notes = []
            for k, fold in enumerate(split['training_cv']):
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter('always')
                    a = fit_model(rows,groups,fold['train'],spec)
                if caught:
                    raise ValueError('Training warning: '+'; '.join(str(w.message) for w in caught))
                for mode in spec['modes']:
                    oof[mode][[index[i] for i in fold['validation']]] = scores(a,[rows[i]['text'] for i in fold['validation']],mode)
                # Retain exact fold parameters and memberships for audit/recovery.
                dump(folder/f'fold-{k}.pkl',a)
                fold_notes.append(dict(train=fold['train'],validation=fold['validation'],calibration_folds=a['calibration_folds']))
            a = fit_model(rows,groups,ids,spec)
            dump(folder/'model.pkl',a)
            np.savez(folder/'oof.npz',indices=np.array(ids),labels=np.array(y),**oof)
            n.save(folder/'folds.json',fold_notes)
            entries = []
            for mode in spec['modes']:
                if not np.isfinite(oof[mode]).all():
                    raise ValueError('Incomplete OOF for '+spec['id'])
                threshold = 0. if mode == 'raw' and is_svm(spec) else .5
                entries.append(dict(id=spec['id']+'-'+mode,fit_id=spec['id'],mode=mode,threshold=threshold,
                    training_oof=n.metrics(y,(oof[mode]>=threshold).astype(int)),
                    training_seconds=time.perf_counter()-started,
                    features=len(a['pipe']['tfidf'].get_feature_names_out()),model_bytes=(folder/'model.pkl').stat().st_size))
            n.save(folder/'training-complete.json',entries); results.extend(entries)
            print('Completed fresh',spec['id'],'OOF and full 80% refit',flush=True)
    n.save(output/'classical-results.json',results)


def mbert(output):
    output = Path(output); cfg, rows, split = context(output)
    if (output/'freeze.json').exists() or (output/'test-started.json').exists():
        raise ValueError('Training is closed')
    base = Path(cfg['base'])
    for name, sha in cfg['base_files'].items():
        if n.digest(base/name) != sha:
            raise ValueError('Pinned base changed')
    ids = split['partitions']['train']; index = {i:j for j,i in enumerate(ids)}
    oof = np.full(len(ids),np.nan); summaries=[]
    # Full 80% fit and every independent OOF fit start from the pinned base.
    for key, train, held in [('mbert',ids,None)]+[(f'mbert-oof-{k}',f['train'],f['validation']) for k,f in enumerate(split['training_cv'])]:
        folder = output/key
        if (folder/'training-summary.json').exists():
            summary = n.load(folder/'training-summary.json')
            if n.load(folder/'configuration.json')['train_indices'] != train or summary['fixed_epoch'] != 2:
                raise ValueError('Completed mBERT membership/settings changed')
        else:
            summary = bert.fit(base,rows,train,folder)
        summaries.append(dict(id=key,**summary))
        if held is not None:
            cache = folder/'oof.npz'
            if cache.exists():
                saved = np.load(cache); np.testing.assert_array_equal(saved['indices'],held); p = saved['probabilities']
            else:
                logits, seconds = bert.logits(folder/summary['final_path'],[rows[i]['text'] for i in held],summary['max_length'],'cuda')
                p = softmax(logits,axis=1)[:,1]
                np.savez(cache,indices=held,probabilities=p)
                n.save(folder/'prediction-timing.json',dict(seconds=seconds))
            oof[[index[i] for i in held]] = p
        print('Completed fresh',key,'fit',flush=True)
    if not np.isfinite(oof).all():
        raise ValueError('Incomplete fresh mBERT OOF')
    np.savez(output/'mbert-oof.npz',indices=ids,labels=[rows[i]['label'] for i in ids],probabilities=oof)
    n.save(output/'mbert-complete.json',dict(summaries=summaries,training_oof=n.metrics([rows[i]['label'] for i in ids],(oof>=.5).astype(int))))


def check_probabilities(values, length):
    values = np.asarray(values)
    if values.shape != (length,) or not np.isfinite(values).all() or ((values<0)|(values>1)).any():
        raise ValueError('Invalid or misaligned ensemble probabilities')
    return values


def ensemble_oof(output, split):
    output = Path(output); ids = split['partitions']['train']; p = {}
    rows = n.load(output/'dataset.json')
    for name in COMPONENTS:
        source = output/'mbert-oof.npz' if name == 'mbert' else output/name/'oof.npz'
        saved = np.load(source); np.testing.assert_array_equal(saved['indices'],ids)
        if name == 'mbert':
            values = saved['probabilities']
        elif name == 'legacy-svm':
            values = saved['sigmoid']
        else:
            # Ensemble LR/NB use native posteriors, matching the prior protocol.
            values = np.full(len(ids),np.nan); positions = {i:j for j,i in enumerate(ids)}
            for k, fold in enumerate(split['training_cv']):
                a = unpickle(output/name/f'fold-{k}.pkl')
                values[[positions[i] for i in fold['validation']]] = expit(raw_score(a['pipe'],[rows[i]['text'] for i in fold['validation']]))
        p[name] = check_probabilities(values,len(ids))
    return p


def freeze(output):
    output = Path(output); cfg, rows, split = context(output)
    if (output/'freeze.json').exists() or (output/'test-started.json').exists():
        raise ValueError('Experiment already frozen/opened')
    entries = n.load(output/'classical-results.json')
    m = n.load(output/'mbert-complete.json'); ids = split['partitions']['train']; y = np.array([rows[i]['label'] for i in ids])
    entries.append(dict(id='mbert',fit_id='mbert',mode='native',threshold=.5,training_oof=m['training_oof'],
        training_seconds=sum(s['seconds'] for s in m['summaries'])))
    p = ensemble_oof(output,split)
    votes = []
    for size in (2,3,4):
        for components in combinations(COMPONENTS,size):
            key = 'vote-'+'+'.join(components); values = np.mean([p[c] for c in components],axis=0)
            entry = dict(id=key,components=list(components),mode='soft-vote',threshold=.5,tie='ham',
                training_oof=n.metrics(y,(values>.5).astype(int)))
            entries.append(entry); votes.append(entry)
    for components in STACKS:
        key = 'stack-'+'+'.join(components)
        x = np.column_stack([p[c] for c in components])
        model = LogisticRegression(C=1,solver='lbfgs',max_iter=2000,random_state=fair.SEED).fit(x,y)
        dump(output/(key+'.pkl'),dict(model=model,components=components,training_ids=ids))
        # Meta training fit is not held-out OOF performance; do not rank it as CV.
        entries.append(dict(id=key,components=list(components),mode='stacking',threshold=.5,tie='ham',training_oof=None,
            meta_rows=len(ids),meta_input='Strictly base-OOF positive probabilities; fold-local features and nested SVM sigmoids'))
    n.save(output/'entries.json',entries)
    n.save(output/'ensemble-training.json',dict(votes=votes,stacks=[list(s) for s in STACKS],
        base_oof_indices=ids,test_used=False,overall_selected=None,interpretation='Test leaders descriptive only; historical fixed settings; no stacking resubstitution reported as CV'))
    n.save(output/'freeze.json',dict(configuration_sha256=n.digest(output/'configuration.json'),
        files={p.relative_to(output).as_posix():n.digest(p) for p in output.rglob('*') if p.is_file()}))
    print('Sealed',len(entries),'configurations before test transformation.',flush=True)


def verify(output):
    output = Path(output); context(output)
    seal = n.load(output/'freeze.json')
    for name, sha in seal['files'].items():
        if n.digest(output/name) != sha:
            raise ValueError('Frozen file changed: '+name)


def evaluate(output):
    output = Path(output); verify(output)
    with (output/'test-started.json').open('x',encoding='utf-8') as f:
        json.dump(dict(freeze_sha256=n.digest(output/'freeze.json')),f)
    cfg, rows, split = context(output); ids = split['partitions']['test']; texts = [rows[i]['text'] for i in ids]; y = [rows[i]['label'] for i in ids]
    results=[]; component_p={}; cached={}
    with threadpool_limits(limits=1):
        for entry in n.load(output/'entries.json'):
            started = time.perf_counter(); key = entry['id']; mode = entry['mode']
            if mode in ('raw','sigmoid'):
                fit_id=entry['fit_id']
                if fit_id not in cached:
                    cached[fit_id] = unpickle(output/fit_id/'model.pkl')
                a = cached[fit_id]; values = scores(a,texts,mode); prediction = (values>=entry['threshold']).astype(int)
                if fit_id in COMPONENTS:
                    component_p[fit_id] = (values if fit_id == 'legacy-svm' else expit(raw_score(a['pipe'],texts)))
            elif key == 'mbert':
                summary = n.load(output/'mbert/training-summary.json')
                logits,_ = bert.logits(output/'mbert'/summary['final_path'],texts,summary['max_length'],'cuda')
                values = softmax(logits,axis=1)[:,1]; component_p['mbert']=values; prediction=(values>=.5).astype(int)
            else:
                arrays=[check_probabilities(component_p[c],len(ids)) for c in entry['components']]
                if mode == 'soft-vote':
                    values=np.mean(arrays,axis=0)
                else:
                    meta=unpickle(output/(key+'.pkl'))
                    if meta['model'].classes_.tolist() != [0,1]:
                        raise ValueError('Meta classes reversed')
                    values=meta['model'].predict_proba(np.column_stack(arrays))[:,1]
                prediction=(values>.5).astype(int)
            if not np.isfinite(values).all():
                raise ValueError('Nonfinite test scores')
            pred_dir=output/'test-predictions';pred_dir.mkdir(exist_ok=True)
            n.save(pred_dir/(key+'.json'),dict(indices=ids,labels=y,scores=values.tolist(),predictions=prediction.tolist()))
            subgroup={}
            for field in ('language','source'):
                for value in sorted({rows[i][field] for i in ids}):
                    jj=[j for j,i in enumerate(ids) if rows[i][field] == value]
                    yy=[y[j] for j in jj]
                    subgroup[field+':'+value]=dict(records=len(jj),smishing=sum(yy),
                        metrics=n.metrics(yy,prediction[jj]) if min(sum(yy),len(yy)-sum(yy))>=5 else None)
            result=dict(entry,test=n.metrics(y,prediction),subgroups=subgroup,test_batch_seconds=time.perf_counter()-started)
            results.append(result)
            print(key,'test F1',round(result['test']['f1'],6),flush=True)
    n.save(output/'test-results.json',dict(results=results,primary_metric='smishing F1',selected=None,
        interpretation='Descriptive retrospective comparison; no prospective/general deployment winner'))
    verify(output)


def report(output, destination):
    output, destination=Path(output),Path(destination);verify(output)
    cfg,rows,split=context(output);results=n.load(output/'test-results.json')['results']; audit=n.load(output/'data-audit.json')
    for item in results:
        p=n.load(output/'test-predictions'/(item['id']+'.json'))
        if p['indices'] != split['partitions']['test'] or p['labels'] != [rows[i]['label'] for i in p['indices']] or n.metrics(p['labels'],p['predictions']) != item['test']:
            raise ValueError('Saved metric/membership verification failed')
    ranked=sorted(results,key=lambda r:(-r['test']['f1'],-r['test']['recall'],r['id']))
    leaders=[e['id'] for e in ranked if e['test']['f1'] == ranked[0]['test']['f1']]
    destination.mkdir(parents=True,exist_ok=True)
    n.save(destination/'results.json',dict(results=results,audit=audit,highest_observed_test_f1=leaders,
        configuration=cfg,freeze_sha256=n.digest(output/'freeze.json')))
    table=[dict(id=e['id'],training_oof_f1=e['training_oof']['f1'] if e['training_oof'] else None,
        **{k:e['test'][k] for k in ('accuracy','precision','recall','f1','macro_f1','fpr','fnr')},
        tn=e['test']['confusion_matrix'][0][0],fp=e['test']['confusion_matrix'][0][1],
        fn=e['test']['confusion_matrix'][1][0],tp=e['test']['confusion_matrix'][1][1]) for e in ranked]
    n.write_csv(destination/'comparison.csv',table)
    lines=['# All-algorithm 80/20 retraining — 19 October 2026','',
        '**Highest observed test F1:** '+', '.join(leaders)+'.', '',
        f'All {len(results)} configurations were freshly retrained or constructed from freshly fitted components on the identical 2,734 training records. '
        'All use the identical 684 test records (611 ham, 73 smishing). No old fitted classifier or transformer checkpoint was substituted for retraining. '
        'The local pretrained mBERT base initializes every fresh full/fold fine-tune. The earlier NB-only 80/20 experiment is preserved.', '',
        'This is a retrospective extension after earlier test results were already viewed. Fixed historical settings and default thresholds were recorded before fitting; '
        'there is no newly untouched test or overall deployment selection. Rankings below are descriptive. '
        'The same constraints that produced 79.9883%/20.0117% membership preserve whole groups and class counts, '
        'but yield only nine test components, source concentration, and uneven training CV folds. '
        'Do not interpret 684 rows as independent campaigns. Inherited source/rule labels remain unverified.', '',
        '| Configuration | Training OOF F1 | Test accuracy | Scam precision | Scam recall | Scam F1 | TN/FP/FN/TP |',
        '|---|---:|---:|---:|---:|---:|---|']
    for e in table:
        cv='—' if e['training_oof_f1'] is None else f'{e["training_oof_f1"]:.2%}'
        lines.append(f'| {e["id"]} | {cv} | {e["accuracy"]:.2%} | {e["precision"]:.2%} | {e["recall"]:.2%} | {e["f1"]:.2%} | {e["tn"]}/{e["fp"]}/{e["fn"]}/{e["tp"]} |')
    lines += ['', 'A–E reproduce the previous family-winning hyperparameters: A word LR, B word Linear SVM, '
        'C word+character Linear SVM, D word+character LR, E word NB. Each is compared with native/raw and '
        'training-OOF sigmoid scores at fixed default thresholds; these are not the older validation-tuned thresholds. '
        'Latest NB variants and SVM preserve the raw-URL/currency tokenizer and conservative stopwords. '
        'Legacy LR/SVM/NB use sg-ascii-v1 normalization, unigram TF-IDF and fixed C=10 / alpha=.1; '
        'their standalone sigmoids are training-only. RF uses 200 balanced trees; KNN uses k=5, '
        'both with the original 5,000-feature Unicode word-bigram settings. Different feature paths are explicit model configurations, not an isolated estimator-only experiment.', '',
        'mBERT uses the pinned multilingual cased base, two fixed epochs, Adafactor 2e-5, accumulation 8, '
        'microbatch 1, deterministic CUDA float16 and fit-only p95 lengths capped at 256. '
        'It receives the same eligible CSV messages with case preserved and its native tokenizer, rather than TF-IDF. '
        'No held-out checkpoint selection is performed. This updated text view and allocation differ from the older redacted mBERT experiment.', '',
        'All 11 equal-weight soft votes over legacy LR/SVM/NB/mBERT are included. LR/NB/mBERT supply native posteriors; '
        'SVM supplies a training-OOF sigmoid. For OOF SVM probability predictions, each outer fit uses a separate inner grouped sigmoid. '
        'The two historical LR meta stacks use the same full-training OOF base probability rows, '
        'with fold-local features and independent mBERT base fits. Meta training fit is not presented as held-out CV; '
        'the stack rows therefore show no training OOF F1. Ensemble ties map to ham; standalone ties map to smishing.', '',
        'All saved test metrics were recomputed from frozen predictions. Test membership, source hashes, fitted artifacts '
        'and protocol were checked before/after the exclusive test evaluation. Full models, message text, vocabularies and predictions '
        'stay private under '+output.as_posix()+'. Source terms/attribution remain in ../source-evidence.md. '
        'No APK or app model was changed. XLM-R has not previously been trained; mBERT quantization is an inference derivative.', '',
        'Reproduction (use a new run directory; mBERT requires the existing local CUDA environment/base):', '', '```powershell',
        "$env:PYTHONPATH='research'",
        "$py='research/data/mbert-20261002/venv/Scripts/python.exe'",
        '$run=\'research/runs/all-algorithms-8020-20261019/NEW-RUN\'',
        '& $py -m smishguard.all_algorithms_8020 prepare $run',
        '& $py -m smishguard.all_algorithms_8020 classical $run',
        '& $py -m smishguard.all_algorithms_8020 mbert $run',
        '& $py -m smishguard.all_algorithms_8020 freeze $run',
        '& $py -m smishguard.all_algorithms_8020 evaluate $run',
        '& $py -m smishguard.all_algorithms_8020 report $run', '```','']
    (destination/'RESULTS.md').write_text('\n'.join(lines),encoding='utf-8')
    n.save(output/'completion-verification.json',dict(freeze_verified=True,metric_tables_recomputed=len(results),
        identical_test_membership=True,highest_observed_test_f1=leaders,overall_selected=None,
        public_files={p.name:n.digest(p) for p in destination.iterdir() if p.is_file()}))
    print('Verified results:',destination/'RESULTS.md',flush=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','classical','mbert','freeze','evaluate','report'])
    parser.add_argument('output',type=Path)
    parser.add_argument('--previous',type=Path,default=ROOT/'research/runs/holdout-8020-20261019/run-v1')
    parser.add_argument('--base',type=Path,default=ROOT/'research/data/mbert-20261002/base')
    parser.add_argument('--report-dir',type=Path,default=ROOT/'docs/all-algorithms-8020-20261019')
    a=parser.parse_args()
    if a.phase == 'prepare': prepare(a.previous,a.output,a.base)
    elif a.phase == 'classical': classical(a.output)
    elif a.phase == 'mbert': mbert(a.output)
    elif a.phase == 'freeze': freeze(a.output)
    elif a.phase == 'evaluate': evaluate(a.output)
    else: report(a.output,a.report_dir)


if __name__ == '__main__': main()
