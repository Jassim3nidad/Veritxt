"""Meaningful guards for label handling, train-only features and template isolation."""
import tempfile
from pathlib import Path
import unittest
import numpy as np
from smishguard import bantaytext_workflow as w


class BantayTextWorkflowTests(unittest.TestCase):
    def test_ambiguous_conflicting_and_empty_rows_never_become_ground_truth(self):
        records=[dict(id='a',text='same text',label=0),dict(id='b',text='SAME TEXT',label=1,needs_review='True'),
            dict(id='c',text=' <REAL NAME> ',label=0),dict(id='d',text='allowed message',label=0),
            dict(id='e',text='allowed   message',label=0),dict(id='f',text='unsupported',label='gambling_ad')]
        rows,ledger,audit=w.clean_rows(records)
        self.assertEqual([r['id'] for r in rows],['d'])
        self.assertEqual(audit['conflicting_exact_groups'],1)
        self.assertEqual(ledger[0]['reason'],'conflicting_exact_labels')
        self.assertEqual(ledger[1]['original_label'],1)
        self.assertEqual(ledger[-1]['reason'],'unsupported_label')

    def test_grouped_split_cannot_cross_related_templates(self):
        rows=[dict(id=str(i),text=f'content {i}',label=i%2) for i in range(120)]
        groups=np.arange(120)//2
        parts,audit=w.partitions(rows,groups,'grouped')
        self.assertFalse(any(audit['template_overlap'].values()))
        self.assertEqual(sum(len(v) for v in parts.values()),120)
        self.assertEqual(parts,w.partitions(rows,groups,'grouped')[0])

    def test_test_tokens_cannot_influence_vocabulary_or_oof_calibration(self):
        rows=[dict(text=f'{"normal" if i%2==0 else "verify"} unique{i}',label=i%2) for i in range(60)]
        rows.append(dict(text='heldoutsecret',label=1))
        spec=dict(algorithm='svm',features='word',ngrams=[1,2],calibrated=True)
        artifact=w.fit_candidate(rows,np.arange(61),list(range(60)),spec)
        words=artifact['pipe']['tfidf'].get_feature_names_out()
        self.assertNotIn('heldoutsecret',words)
        for fold in artifact['calibration_folds']:
            self.assertNotIn(60,fold['train']+fold['calibration'])
            self.assertFalse(set(fold['train'])&set(fold['calibration']))
        scores=w.score(artifact,['heldoutsecret','normal','verify'])
        self.assertTrue(np.isfinite(scores).all())
        self.assertTrue(((scores>=0)&(scores<=1)).all())

    def test_confusion_math_and_unattainable_threshold(self):
        result=w.calculate_metrics([0,0,1,1],[.9,.1,.2,.8],.5)
        self.assertEqual(result['confusion'],dict(tn=1,fp=1,fn=1,tp=1))
        self.assertEqual(result['f1'],.5)
        _,_,feasible=w.threshold_policy([0,1],[.5,.5])
        self.assertFalse(feasible)
        self.assertIsNone(w.calculate_metrics([0,0],[.1,.2],.5)['roc_auc'])

    def test_bantaytext_reference_is_explicit_and_baseline_precedes_improvements(self):
        matrix=w.experiment_matrix()
        self.assertEqual([s['algorithm'] for s in matrix[:3]],['nb','lr','svm'])
        spec=next(s for s in matrix if s['id']=='nb-word12-english')
        v=w.vectorizer(spec)
        self.assertEqual(spec['alpha'],.1)
        self.assertIsNone(v.max_features)
        self.assertEqual(v.min_df,1)
        self.assertTrue({'po','paki','nyo','ninyo','na'}.issubset(set(v.build_analyzer()('po paki nyo ninyo na'))))
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            w.save(root/'dataset.json',[]);w.save(root/'splits.json',{})
            cfg={'cleaned_sha256':w.digest(root/'dataset.json'),'split_sha256':w.digest(root/'splits.json')}
            with self.assertRaisesRegex(ValueError,'Finish and save baseline'):
                w.run_phase(root,[],np.array([]),{},cfg,'improvement')


if __name__=='__main__':unittest.main()
