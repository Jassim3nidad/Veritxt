"""Compare exact APK classifiers on a frozen cohort unused for fitting/tuning by either.

Retrospective only: no new unbiased benchmark can be manufactured from old data.
Raw SMS and row-level predictions stay in ignored research/runs.
"""
from collections import Counter
from pathlib import Path
import argparse
import hashlib
import json
import math
import pickle
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import retrain_nb_generalization as g
from smishguard import nb_comparison as n, bantaytext_workflow as w
from smishguard.raw_sms_validation import raw_view
import numpy as np
from sklearn.metrics import confusion_matrix

OLD = ROOT/'research/runs/bantaytext-20261013/notebook-run-v3'
NEW = ROOT/'research/runs/nb-generalization-20261019/run-v1'
PROTOCOL = ROOT/'docs/apk-model-comparison-20261020-protocol.md'
APKS = {
    'svm': (ROOT/'deliverables/Veritxt-LinearSVM-20261019/Veritxt-0.3.0-LinearSVM-20261019.apk',
            'ef6caef798e7a7359018e86410c550589b123a75e520bb504217081ca9e1a0c4',
            '15cc0105b0e51e5342682ea36896c4436e515c39d165faf040476046b6b8059c'),
    'nb': (ROOT/'deliverables/Veritxt-Retrained-NB-20261020/Veritxt-0.3.0-Retrained-NB-80-20.apk',
           'f1dd903e8696267e176904884bbe83a00158cba185080a8a459f4b7d911e1804',
           '7cd219db2c9c4559aec60fdea2558821e48cc73085455a9c9caf0b5465d9df5c')}


def assets():
    result = {}
    for key, (path, apk_hash, model_hash) in APKS.items():
        assert n.digest(path) == apk_hash
        with zipfile.ZipFile(path) as archive:
            payload = archive.read('assets/model.json')
            assert hashlib.sha256(payload).hexdigest() == model_hash
            result[key] = json.loads(payload)
            if key == 'svm':
                assert hashlib.sha256(archive.read('assets/raw-sms-adapter.json')).hexdigest() == '11c3ee93fb7523e72b5658bec9f4bc5ee7389d9e5add25d5ca3fceceeedb5b8c'
    return result


def verify_inputs():
    g.verify(NEW)
    config = n.load(OLD/'configuration.json'); seal = n.load(OLD/'improvement-freeze.json')
    assert n.digest(OLD/'configuration.json') == seal['configuration_sha256']
    assert n.digest(OLD/'dataset.json') == config['cleaned_sha256']
    assert n.digest(OLD/'splits.json') == config['split_sha256']
    selected = 'grouped/svm-C-10.0/pipeline.pkl'
    frozen = {key.replace('\\', '/'): value for key, value in seal['files'].items()}
    assert n.digest(OLD/selected) == frozen[selected]
    return dict(svm_pipeline_sha256=frozen[selected], nb_pipeline_sha256=n.digest(NEW/'group-fold-0/original-alpha-0.1/pipeline.pkl'),
        svm_dataset_sha256=n.digest(OLD/'dataset.json'), nb_dataset_sha256=n.digest(NEW/'dataset.json'),
        svm_splits_sha256=n.digest(OLD/'splits.json'), nb_folds_sha256=n.digest(NEW/'folds.json'),
        nb_groups_sha256=n.digest(NEW/'groups.json'), protocol_sha256=n.digest(PROTOCOL), script_sha256=n.digest(Path(__file__)))


def prepare(output):
    models = assets(); hashes = verify_inputs()
    old, rows = n.load(OLD/'dataset.json'), n.load(NEW/'dataset.json')
    splits = n.load(OLD/'splits.json'); fold = n.load(NEW/'folds.json')['folds'][0]
    assert fold['id'] == 'group-fold-0'
    parts = splits['partitions']['grouped']; index = {row['id']: i for i, row in enumerate(rows)}
    assert len(index) == len(rows) and len({r['id'] for r in old}) == len(old)
    views = [raw_view(r['text']) for r in rows]
    for row in old:
        i = index[row['id']]
        assert int(row['label']) == rows[i]['label'] and views[i] == row['text']
    parent = list(range(len(rows)))
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    def connect(keys, indices):
        first = {}
        for key, i in zip(keys, indices):
            if key in first: parent[find(i)] = find(first[key])
            else: first[key] = i
    connect(n.load(NEW/'groups.json'), range(len(rows)))
    connect(splits['groups'], [index[r['id']] for r in old])
    connect([n.normalize(r['text']).casefold() for r in rows], range(len(rows)))
    connect([v.casefold() for v in views], range(len(rows)))
    exposed = {index[old[i]['id']] for part in ('train', 'validation') for i in parts[part]}
    used = exposed | set(fold['train']); used_groups = {find(i) for i in used}
    retained = sorted(i for i in fold['test'] if find(i) not in used_groups)
    common = {index[old[i]['id']] for i in parts['test']} & set(fold['test'])
    group_ids = {key: i for i, key in enumerate(sorted({find(i) for i in retained}))}
    ledger = [dict(index=i, id=rows[i]['id'], label=int(rows[i]['label']), group=group_ids[find(i)],
                   text_sha256=hashlib.sha256(rows[i]['text'].encode()).hexdigest(), source=rows[i]['source']) for i in retained]
    assert not set(retained) & used and not {find(i) for i in retained} & used_groups
    assert {r['label'] for r in ledger} == {0, 1}
    output.mkdir(parents=True, exist_ok=False)
    n.save(output/'cohort.json', ledger)
    audit = dict(svm_partition_sizes={key:len(value) for key, value in parts.items()},
        nb_partition_sizes=dict(train=len(fold['train']), test=len(fold['test'])),
        matching_raw_lineage_and_labels=len(old), original_test_intersection=len(common),
        original_test_intersection_labels=dict(Counter(int(rows[i]['label']) for i in common)),
        nb_test_excluding_svm_train_validation=len(set(fold['test'])-exposed),
        retained=len(ledger), retained_labels=dict(Counter(r['label'] for r in ledger)),
        retained_components=len(group_ids), retained_sources=dict(Counter(r['source'] for r in ledger)),
        train_validation_row_overlap=0, conservative_component_overlap=0,
        history='historically exposed, inherited labels; no prospective independent test available')
    n.save(output/'cohort-audit.json', audit)
    n.save(output/'freeze.json', dict(inputs=hashes, cohort_sha256=n.digest(output/'cohort.json'),
        audit_sha256=n.digest(output/'cohort-audit.json'),
        models={key:dict(apk_sha256=spec[1], model_sha256=spec[2], threshold=models[key]['threshold']) for key,spec in APKS.items()}))
    print(json.dumps(audit, indent=2))


def score_export(model, raw):
    if model['algorithm'] == 'nb':
        return n.reference_score(model, n.reference_features(model, raw))
    tokens = [t for t in re.findall(r'(?u)\b\w\w+\b', raw_view(raw).lower()) if t not in model['stop_words']]
    terms = tokens + [a+' '+b for a,b in zip(tokens,tokens[1:])]
    vocabulary = {term:i for i,term in enumerate(model['vocabulary'])}
    values = {vocabulary[t]:c*model['idf'][vocabulary[t]] for t,c in Counter(terms).items() if t in vocabulary}
    norm = math.sqrt(sum(v*v for v in values.values()))
    margin = model['bias'] + (sum(model['weights'][i]*v/norm for i,v in values.items()) if norm else 0.)
    margin = model['calibration']['a']*margin+model['calibration']['b']
    return 1/(1+math.exp(-margin)) if margin >= 0 else math.exp(margin)/(1+math.exp(margin))


def metrics(labels, predictions):
    counts = [sum(int(y == truth and p == pred) for y,p in zip(labels, predictions)) for truth,pred in [(0,0),(0,1),(1,0),(1,1)]]
    assert counts == confusion_matrix(labels,predictions,labels=[0,1]).ravel().tolist()
    tn,fp,fn,tp = counts
    return dict(records=len(labels), accuracy=(tp+tn)/len(labels), precision=tp/(tp+fp) if tp+fp else 0.,
        recall=tp/(tp+fn), f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.,
        balanced_accuracy=((tp/(tp+fn))+(tn/(tn+fp)))/2,
        false_positive_rate=fp/(tn+fp), false_negative_rate=fn/(tp+fn),
        confusion=dict(tn=tn,fp=fp,fn=fn,tp=tp))


def evaluate(output):
    seal = n.load(output/'freeze.json'); assert seal['inputs'] == verify_inputs()
    assert seal['cohort_sha256'] == n.digest(output/'cohort.json') and seal['audit_sha256'] == n.digest(output/'cohort-audit.json')
    (output/'evaluation-started.json').write_text(json.dumps(dict(freeze_sha256=n.digest(output/'freeze.json'))),encoding='utf-8')
    models = assets(); rows = n.load(NEW/'dataset.json'); cohort = n.load(output/'cohort.json')
    # Replay the exported APK scorer against fitted sklearn and saved test ledgers.
    old = n.load(OLD/'dataset.json'); by_id = {r['id']:r for r in rows}
    svm = pickle.loads((OLD/'grouped/svm-C-10.0/pipeline.pkl').read_bytes())
    nb = pickle.loads((NEW/'group-fold-0/original-alpha-0.1/pipeline.pkl').read_bytes())
    svmp = n.load(OLD/'grouped/svm-C-10.0/test-predictions.json')
    nbp = n.load(NEW/'group-fold-0/original-alpha-0.1/predictions.json')
    parity = {}
    for name, texts, actual, expected in [
        ('svm', [by_id[old[i]['id']]['text'] for i in svmp['indices']],
         w.score(svm,[old[i]['text'] for i in svmp['indices']]), svmp['scores']),
        ('nb', [rows[i]['text'] for i in nbp['indices']],
         nb.predict_proba([n.normalize(rows[i]['text']) for i in nbp['indices']])[:,1], nbp['scores'])]:
        exported = np.array([score_export(models[name],t) for t in texts])
        error = max(float(np.max(np.abs(exported-actual))), float(np.max(np.abs(exported-np.array(expected)))))
        assert error <= 1e-10
        assert np.array_equal(exported >= models[name]['threshold'], actual >= models[name]['threshold'])
        parity[name] = dict(cases=len(texts), max_score_error=error)
    labels = [c['label'] for c in cohort]; predictions = {}; records = []
    for key in models:
        scores = [score_export(models[key],rows[c['index']]['text']) for c in cohort]
        predictions[key] = [int(s >= models[key]['threshold']) for s in scores]
        records.append(dict(model=key, scores=scores, predictions=predictions[key]))
    n.save(output/'private-predictions.json',dict(cohort=cohort,records=records))
    results = {key:metrics(labels,p) for key,p in predictions.items()}
    group_keys = sorted({c['group'] for c in cohort}); confusion = np.zeros((len(group_keys),2,4))
    for gi, group in enumerate(group_keys):
        ii=[i for i,c in enumerate(cohort) if c['group']==group]
        for mi,key in enumerate(('svm','nb')):
            for i in ii:
                confusion[gi,mi,2*labels[i]+predictions[key][i]] += 1
    draws = np.random.default_rng(20261020).integers(0,len(group_keys),size=(20000,len(group_keys)))
    totals = confusion[draws].sum(axis=1); den = 2*totals[:,:,3]+totals[:,:,1]+totals[:,:,2]
    f1 = np.divide(2*totals[:,:,3],den,out=np.zeros_like(den),where=den>0)
    delta = f1[:,1]-f1[:,0]
    result = dict(status='completed_retrospective_only', unbiased_winner=None,
        cohort=n.load(output/'cohort-audit.json'), models=results, inference_parity=parity,
        paired_outcomes=dict(both_correct=sum(a==y and b==y for a,b,y in zip(predictions['svm'],predictions['nb'],labels)),
            svm_only_correct=sum(a==y and b!=y for a,b,y in zip(predictions['svm'],predictions['nb'],labels)),
            nb_only_correct=sum(a!=y and b==y for a,b,y in zip(predictions['svm'],predictions['nb'],labels)),
            both_wrong=sum(a!=y and b!=y for a,b,y in zip(predictions['svm'],predictions['nb'],labels))),
        paired_component_bootstrap=dict(draws=20000,seed=20261020,components=len(group_keys),
            metric='NB minus SVM smishing F1',observed=results['nb']['f1']-results['svm']['f1'],
            conditional_95_percentile_interval=np.quantile(delta,[.025,.975]).tolist(),
            limitations='Conditional on tiny historically exposed sample and inherited labels; not a prospective superiority test'),
        freeze_sha256=n.digest(output/'freeze.json'),
        caveat='Different original tests cannot establish a winner; retained sample is tiny and class/source unrepresentative. No new independent labels/test set. Classifier metrics only, not app risk-index or abstention-adjusted end-to-end performance.')
    n.save(output/'results.json', result)
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['prepare','evaluate'])
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    (prepare if args.mode=='prepare' else evaluate)(args.output)
