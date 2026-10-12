"""Verify saved actual OOF components against the preserved training assignments."""
import argparse
import json
from pathlib import Path
import pickle
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research'))
from smishguard import fair_compare as fair
from smishguard.ensemble_compare import validate_folds
from smishguard.train import write_json


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def audit(run):
    rows=load(run/'dataset.json')
    m=load(run/'splits.json')
    train=np.array(m['partitions']['train'])
    texts=[rows[i]['text_redacted'] for i in train]
    y=np.array([rows[i]['label'] for i in train])
    groups=np.array(m['groups'])[train]
    oof=dict(np.load(run/'classical-oof.npz'))
    np.testing.assert_array_equal(oof['labels'],y)
    np.testing.assert_array_equal(oof['train_indices'],train)
    count=0
    max_error=0.
    def vectorizer(pipe,indices):
        nonlocal count
        fresh=fair.vectorizer().fit([texts[i] for i in indices])
        fitted=pipe['tfidf']
        if fresh.vocabulary_!=fitted.vocabulary_:
            raise ValueError('Vocabulary includes another fold or partition')
        np.testing.assert_array_equal(fresh.idf_,fitted.idf_)
        if list(pipe.classes_)!=[0,1]:
            raise ValueError('Reversed component classes')
        count+=1
    for k,fold in enumerate(m['inner_folds']):
        saved=pickle.loads((run/f'classical/fold-{k}.pkl').read_bytes())
        a,b=np.array(fold['train']),np.array(fold['validation'])
        np.testing.assert_array_equal(saved['train'],a)
        np.testing.assert_array_equal(saved['validation'],b)
        if set(groups[a])&set(groups[b]):
            raise ValueError('Outer group overlap')
        for name,component in saved['components'].items():
            pipe=component['pipeline']
            vectorizer(pipe,a)
            held=[texts[i] for i in b]
            if name=='svm':
                nested=component['nested_fits']
                folds=[(np.array(f['train']),np.array(f['validation'])) for f in nested]
                validate_folds(folds,y[a],groups[a])
                for f in nested:
                    ia,ib=a[f['train']],a[f['validation']]
                    vectorizer(f['pipeline'],ia)
                    q=f['pipeline'].decision_function([texts[i] for i in ib])
                    np.testing.assert_array_equal(q,component['calibration_oof_margins'][f['validation']])
                raw=pipe.decision_function(held)
                np.testing.assert_array_equal(raw,oof['raw_svm'][b])
                p=component['calibrator'].predict_proba(raw.reshape(-1,1))[:,1]
            else:
                p=pipe.predict_proba(held)[:,1]
            np.testing.assert_array_equal(p,oof[name][b])
            max_error=max(max_error,float(np.max(abs(p-oof[name][b]))))
    mbert_folds=0
    if (run/'mbert-oof.npz').exists():
        mb=dict(np.load(run/'mbert-oof.npz'))
        np.testing.assert_array_equal(mb['train_indices'],train)
        for k,fold in enumerate(m['inner_folds']):
            folder=run/f'mbert-oof-{k}'
            cfg=load(folder/'configuration.json')
            summary=load(folder/'training-summary.json')
            np.testing.assert_array_equal(cfg['train_indices'],train[fold['train']])
            if cfg['checkpoint_validation_indices'] is not None or cfg['checkpoint_policy']!='fixed_epoch_2':
                raise ValueError('mBERT OOF checkpoint uses outer validation')
            if not summary['complete'] or len(summary['history'])!=2 or any(h['validation_average_precision'] is not None for h in summary['history']):
                raise ValueError('mBERT OOF epochs not fixed')
            saved=dict(np.load(folder/'oof.npz'))
            np.testing.assert_array_equal(saved['indices'],train[fold['validation']])
            np.testing.assert_array_equal(saved['positions'],fold['validation'])
            np.testing.assert_array_equal(saved['probabilities'],mb['mbert'][fold['validation']])
            mbert_folds+=1
    write_json(run/'oof-artifact-audit.json',dict(classical_fold_vocabularies_and_idfs_verified=count,
        outer_folds=5,nested_svm_folds=25,mbert_folds=mbert_folds,
        predictions_reproduced_exactly=True,max_classical_oof_error=max_error,
        meta_training_records=len(train),no_validation_calibration_or_test_records_in_fold_fits=True))
    print('OOF artifact audit:',count,'classical vocabularies/IDFs;',mbert_folds,'mBERT folds; no outer-held vocabulary or group leakage.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('run',type=Path)
    a=p.parse_args()
    audit(a.run)
