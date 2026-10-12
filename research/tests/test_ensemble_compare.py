"""Leakage and probability boundaries for the fixed-setting ensemble experiment."""
import unittest
from unittest.mock import patch
import tempfile
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression

from smishguard.ensemble_compare import (fit_svm_calibrator, make_pipe, measure,
    predict_probability, probability, validate_folds, vote, freeze, evaluate)
from smishguard import fair_compare as fair
from smishguard.train import write_json


class EnsembleBoundaries(unittest.TestCase):
    def fixture(self):
        # Unique groups, both classes in every inner split; held-out tokens are unique.
        texts=[('meeting schedule ' if i%2==0 else 'verify account reward ')+f'unique{i}' for i in range(60)]
        return texts,np.array([i%2 for i in range(60)]),np.arange(60)

    def test_invalid_probabilities_fail_without_clipping(self):
        for p in ([[.2,.9]], [[0,float('nan')]], [[-.1,1.1]], [[.3,.3,.4]]):
            with self.assertRaises(ValueError):
                probability(p)

    def test_class_order_rejected(self):
        model=LogisticRegression().fit([[0],[1],[2],[3]],[0,0,1,1])
        model.classes_=np.array([1,0])
        with self.assertRaisesRegex(ValueError,'orientation'):
            predict_probability(model,np.array([[1]]))

    def test_equal_voting_and_ties(self):
        p,pred,kind=vote([np.array([[.8,.2],[.4,.6]]),np.array([[.2,.8],[.3,.7]])])
        np.testing.assert_allclose(p,[.5,.65])
        self.assertEqual(pred.tolist(),[0,1])
        self.assertEqual(kind,'soft')
        _,pred,kind=vote(predictions=[[0,1,1],[1,0,1]])
        self.assertEqual(pred.tolist(),[0,0,1])
        self.assertEqual(kind,'hard')
        self.assertEqual(measure([0,1],np.array([.5,.7]))['confusion'],dict(tn=1,fp=0,fn=0,tp=1))

    def test_fold_group_leakage_and_missing_oof_rejected(self):
        _,y,g=self.fixture()
        folds=fair.training_folds(y,g)
        validate_folds(folds,y,g)
        with self.assertRaisesRegex(ValueError,'exactly once'):
            validate_folds(folds[:-1],y,g)
        bad=g.copy()
        bad[folds[0][0][0]]=bad[folds[0][1][0]]
        with self.assertRaisesRegex(ValueError,'group leakage'):
            validate_folds(folds,y,bad)

    def test_calibration_vocab_and_margins_are_out_of_fold(self):
        texts,y,g=self.fixture()
        cal,raw,fits=fit_svm_calibrator(texts,y,g,10.)
        seen=[]
        for fit in fits:
            held=fit['validation']
            vocab=fit['pipeline']['tfidf'].vocabulary_
            for i in held:
                self.assertNotIn(f'unique{i}',vocab)
            np.testing.assert_allclose(raw[held],fit['pipeline'].decision_function([texts[i] for i in held]))
            seen.extend(held)
        self.assertEqual(sorted(seen),list(range(len(y))))
        probability(cal.predict_proba(raw.reshape(-1,1)))

    def test_nested_calibration_never_sees_outer_held_rows(self):
        texts,y,g=self.fixture()
        a,b=fair.training_folds(y,g)[0]
        _,_,fits=fit_svm_calibrator([texts[i] for i in a],y[a],g[a],10.)
        for fit in fits:
            for i in b:
                self.assertNotIn(f'unique{i}',fit['pipeline']['tfidf'].vocabulary_)
            self.assertFalse(set(a[fit['train']])&set(b))
            self.assertFalse(set(a[fit['validation']])&set(b))

    def test_nb_gets_nonnegative_tfidf(self):
        texts,y,_=self.fixture()
        pipe=make_pipe('nb',.1).fit(texts,y)
        self.assertGreaterEqual(pipe['tfidf'].transform(texts).data.min(),0)
        probability(pipe.predict_proba(texts))

    def test_meta_fit_only_uses_oof_train_then_tamper_blocks_test(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'classical').mkdir()
            rows=[dict(id=f'id{i}',label=i%2) for i in range(16)]
            manifest=dict(partitions=dict(train=list(range(8)),validation=list(range(8,12)),test=list(range(12,16))))
            cfg=dict(meta=dict(C=1.,solver='lbfgs',max_iter=2000,random_state=fair.SEED),
                baseline_thresholds=dict(lr=.82,nb=.63,svm=.59),mbert_threshold=.89,prior_test_opened=True)
            write_json(root/'configuration.json',cfg)
            for name in ('baseline-timing.json','native-timing.json'):
                write_json(root/'classical'/name,dict(lr=.1,nb=.1,svm=.1))
            write_json(root/'classical/oof-timing.json',dict(by_component=dict(lr=.2,nb=.2,svm=.5),
                svm_voting_calibration_seconds=.2,final_sigmoid_seconds=.01))
            y=np.array([r['label'] for r in rows[:8]])
            values=y*.6+.2
            np.savez(root/'classical-oof.npz',lr=values,nb=values,svm=values,labels=y,train_indices=np.arange(8))
            original=LogisticRegression.fit
            seen=[]
            def fitting(model,x,labels,*args,**kwargs):
                seen.append((np.array(x),np.array(labels)))
                return original(model,x,labels,*args,**kwargs)
            def infer(output,allrows,indices):
                self.assertEqual(indices,manifest['partitions']['validation'])
                p=np.array([.1,.9,.1,.9])
                return ({n:p for n in fair.NAMES},{n:np.column_stack([1-p,p]) for n in fair.NAMES},
                        {key:.001 for n in fair.NAMES for key in (n,n+'_baseline')})
            with patch('smishguard.ensemble_compare.context',return_value=(cfg,rows,manifest)), \
                    patch('smishguard.ensemble_compare.infer_components',side_effect=infer), \
                    patch.object(LogisticRegression,'fit',fitting):
                freeze(root)
            self.assertEqual(len(seen),1)
            np.testing.assert_array_equal(seen[0][1],y)
            np.testing.assert_array_equal(seen[0][0],np.column_stack([values]*3))
            self.assertFalse((root/'test-started.json').exists())
            # Tamper with a sealed learned component before test: reject before access.
            (root/'stacking_lr_svm_nb.pkl').write_bytes(b'changed')
            with patch('smishguard.ensemble_compare.context'), self.assertRaisesRegex(ValueError,'Frozen model'):
                evaluate(root)
            self.assertFalse((root/'test-started.json').exists())


if __name__=='__main__':
    unittest.main()
