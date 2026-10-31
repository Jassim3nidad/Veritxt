"""Synthetic-only guards for the stricter NB generalization experiment."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from scripts import retrain_nb_generalization as g


def records(count=120):
    return [dict(label=i%2,text=('ordinary dinner ' if i%2==0 else 'verify account ')+str(i),
                 source='source-'+str(i%3)) for i in range(count)]


class NbGeneralizationTests(unittest.TestCase):
    def test_balanced_allocation_is_disjoint_complete_and_80_20(self):
        rows=records();groups=np.arange(120)//2
        folds,status=g.balanced_folds(rows,groups)
        again,_=g.balanced_folds(rows,groups)
        self.assertEqual(folds,again);self.assertTrue(status['no_model_scores_used'])
        covered=[]
        for f in folds:
            self.assertEqual(len(f['test']),24);self.assertEqual(len(f['train']),96)
            self.assertEqual(sum(rows[i]['label'] for i in f['test']),12)
            self.assertFalse(set(groups[f['train']])&set(groups[f['test']]))
            self.assertGreaterEqual(len(set(groups[f['test']])),status['minimum_groups'])
            covered+=f['test']
        self.assertEqual(sorted(covered),list(range(120)))

    def test_impossible_large_component_does_not_split_or_retry(self):
        rows=records(100);groups=np.r_[np.zeros(70,dtype=int),np.arange(1,31)]
        with self.assertRaisesRegex(ValueError,'infeasible'):
            g.balanced_folds(rows,groups)

    def test_source_holdouts_purge_related_other_source_rows(self):
        rows=records(90);groups=np.arange(90)
        groups[1]=groups[0]
        folds=g.source_folds(rows,groups)
        held=next(f for f in folds if f['source']==rows[0]['source'])
        self.assertIn(0,held['test']);self.assertNotIn(1,held['train']);self.assertGreater(held['related_records_purged'],0)
        for fold in folds:
            self.assertFalse(set(groups[fold['train']])&set(groups[fold['test']]))
            self.assertTrue(all(rows[i]['source']!=fold['source'] for i in fold['train']))

    def test_reduced_text_retains_language_but_removes_identifiers(self):
        result=g.reduced_text('May ₱5,000.50 ka. Email foo@example.invalid o https://example.invalid/a123?x=4 at 123456.')
        self.assertIn('may',result);self.assertIn('ka',result);self.assertIn('at',result)
        for value in ('5000','123456','https','example','foo','@'):self.assertNotIn(value,result)

    def test_single_class_source_cannot_estimate_false_positive_rate(self):
        m=g.measure([1,1,1],[1,0,1],[0,1,2])
        self.assertIsNone(m['fpr']);self.assertFalse(m['full_two_class_support'])
        self.assertAlmostEqual(m['recall'],2/3)

    def test_equal_group_metrics_do_not_overweight_large_components(self):
        m=g.measure([0]*99+[1],[0]*100,[0]*99+[1])
        self.assertEqual(m['accuracy'],.99);self.assertAlmostEqual(m['group_weighted_accuracy'],.5)
        self.assertEqual(m['f1'],0.)

    def test_reduced_vocabulary_is_learned_only_from_training(self):
        rows=records(30);model=g.make_pipeline(g.SPECS[1]).fit([r['text'] for r in rows],[r['label'] for r in rows])
        model.predict_proba(['reservedonlysentinel https://held.invalid 777'])
        self.assertNotIn('reservedonlysentinel',model['tfidf'].vocabulary_)
        self.assertFalse(any('https' in word or 'held.invalid' in word for word in model['tfidf'].vocabulary_))

    def test_evaluation_is_exclusive(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'evaluation-started.json').write_text('{}')
            with patch.object(g,'verify'):
                with self.assertRaises(FileExistsError):g.evaluate(root)


if __name__=='__main__':unittest.main()
