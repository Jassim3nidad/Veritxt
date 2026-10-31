"""Guard full family coverage, train-only calibration and ensemble alignment."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from smishguard import all_algorithms_8020 as a, nb_comparison as n, holdout_8020 as h


class AllAlgorithms8020Tests(unittest.TestCase):
    def test_inventory_covers_original_families_and_combined(self):
        historic = {f:dict(spec=dict(algorithm=alg,combined=f in 'CD'))
                    for f,alg in zip('ABCDE',('lr','svm','svm','lr','nb'))}
        with patch.object(n,'load',return_value=dict(family_winners=historic)):
            specs = a.spec_matrix()
        self.assertEqual(len(specs),16)
        self.assertEqual({s['kind'] for s in specs},{'ae','latest','legacy','rf','knn'})
        self.assertEqual([s['id'] for s in specs if s['kind']=='ae'],['AE-'+f for f in 'ABCDE'])
        self.assertEqual(sum(len(s['modes']) for s in specs),21)
        self.assertEqual(sum(1 for k in (2,3,4) for _ in a.combinations(a.COMPONENTS,k)),11)
        self.assertEqual(len(a.STACKS),2)

    def test_native_scores_match_classifier_probabilities(self):
        rows=[dict(text='ordinary family dinner '+str(i),label=0) for i in range(12)]
        rows += [dict(text='verify account claim money '+str(i),label=1) for i in range(12)]
        spec=dict(id='nb',kind='latest',spec=dict(algorithm='nb',alpha=.1),modes=['raw'])
        fitted=a.fit_model(rows,np.arange(24),list(range(24)),spec)
        texts=['ordinary family dinner','verify account claim money','reservedonlysentinel']
        np.testing.assert_allclose(a.scores(fitted,texts,'raw'),fitted['pipe'].predict_proba(texts)[:,1],atol=1e-12)
        self.assertNotIn('reservedonlysentinel',fitted['pipe']['tfidf'].vocabulary_)

    def test_sigmoid_is_fitted_with_training_oof_only(self):
        rows=[dict(text=('ordinary family dinner ' if i%2==0 else 'verify account money ')+str(i),label=i%2) for i in range(120)]
        rows.append(dict(text='reservedonlysentinel',label=1))
        groups=np.arange(121)
        spec=dict(id='svm',kind='legacy',algorithm='svm',value=10.,modes=['sigmoid'])
        fitted=a.fit_model(rows,groups,list(range(120)),spec)
        self.assertEqual(fitted['training_ids'],list(range(120)))
        validation=[]
        for fold in fitted['calibration_folds']:
            self.assertNotIn(120,fold['train']+fold['validation'])
            self.assertFalse(set(fold['train']) & set(fold['validation']))
            validation += fold['validation']
        self.assertEqual(sorted(validation),list(range(120)))
        self.assertGreater(fitted['calibrator'].coef_[0,0],0)
        self.assertNotIn('reservedonlysentinel',fitted['pipe']['tfidf'].vocabulary_)

    def test_probability_alignment_and_range_rejected(self):
        for bad in ([.1],[-.1,.2],[.1,1.1],[np.nan,.2],[[.1,.9],[.2,.8]]):
            with self.assertRaises(ValueError): a.check_probabilities(bad,2)
        np.testing.assert_equal(a.check_probabilities([.1,.9],2),[.1,.9])

    def test_stacks_never_receive_full_fit_training_predictions(self):
        # Meta construction is restricted to explicitly aligned OOF files.
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);n.save(root/'dataset.json',[])
            (root/'legacy-lr').mkdir()
            np.savez(root/'legacy-lr/oof.npz',indices=[99],sigmoid=[.2])
            with self.assertRaises(AssertionError):
                a.ensemble_oof(root,dict(partitions=dict(train=[0])))

    def test_exclusive_test_marker_rejects_repeated_evaluation(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'test-started.json').write_text('{}')
            with patch.object(a,'verify'):
                with self.assertRaises(FileExistsError): a.evaluate(root)

    def test_complete_35_entry_workflow_with_synthetic_transformer(self):
        # Exercise real classical/nested fits and ensemble construction, while
        # replacing only expensive transformer training/inference with a stub.
        rows=[dict(text=('ordinary dinner family ' if i%2==0 else 'verify account money ')+str(i),
                   label=i%2,language='fixture',source='fixture') for i in range(150)]
        groups=np.arange(len(rows));parts=h.split_rows(rows,groups)
        split=dict(partitions=parts,groups=groups.tolist(),training_cv=h.training_folds(rows,groups,parts['train']))
        historic={f:dict(spec=dict(id=f,algorithm=alg,combined=f in 'CD',
            min_df=1,max_features=None,word_ngrams=[1,2],char_ngrams=[3,5],
            value=.03 if alg=='nb' else .1,class_weight=None if alg=='nb' else 'balanced'))
            for f,alg in zip('ABCDE',('lr','svm','svm','lr','nb'))}
        with patch.object(n,'load',return_value=dict(family_winners=historic)):
            cfg=dict(matrix=a.spec_matrix())
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);n.save(root/'dataset.json',rows);n.save(root/'configuration.json',cfg)
            with patch.object(a,'context',return_value=(cfg,rows,split)):
                a.classical(root)
                n.save(root/'mbert-complete.json',dict(summaries=[dict(seconds=0.)],training_oof=dict(f1=1.)))
                ids=parts['train'];y=np.array([rows[i]['label'] for i in ids])
                np.savez(root/'mbert-oof.npz',indices=ids,labels=y,probabilities=np.where(y,.9,.1))
                (root/'mbert').mkdir();n.save(root/'mbert/training-summary.json',dict(final_path='final',max_length=128))
                a.freeze(root)
                entries=n.load(root/'entries.json')
                self.assertEqual(len(entries),35)
                self.assertEqual(sum(e['mode']=='soft-vote' for e in entries),11)
                stacks=[e for e in entries if e['mode']=='stacking']
                self.assertEqual(len(stacks),2)
                self.assertTrue(all(e['training_oof'] is None for e in stacks))
                def logits(checkpoint,texts,length,device):
                    return np.array([[-1.,1.] if 'verify' in text else [1.,-1.] for text in texts]),0.
                with patch.object(a.bert,'logits',side_effect=logits):
                    a.evaluate(root)
                results=n.load(root/'test-results.json')['results']
                self.assertEqual(len(results),35)
                for result in results:
                    p=n.load(root/'test-predictions'/(result['id']+'.json'))
                    self.assertEqual(p['indices'],parts['test'])
                    self.assertEqual(result['test'],n.metrics(p['labels'],p['predictions']))


if __name__ == '__main__': unittest.main()
