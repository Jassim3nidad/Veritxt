"""Scientific integrity checks; synthetic fixtures contain no real SMS."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from smishguard import multiclass_comparison as m


def row(i,text,label='ham',**extra):
    return dict(id=str(i),text=text,label=label,source=m.legacy.SOURCES[0],needs_review='False',language='English',**extra)


class MulticlassComparisonTests(unittest.TestCase):
    def test_three_class_mapping_duplicate_conflict_and_review_holds(self):
        records=[row(0,'ordinary message'),row(1,'account threat','smishing'),row(2,'casino promotion','gambling_ad'),
                 row(3,' ORDINARY  message '),row(4,'ambiguous','ham'),row(5,'AMBIGUOUS','smishing'),row(6,'review pending')]
        records[-1]['needs_review']='True'
        rows,ledger,audit=m.clean(records)
        self.assertEqual([r['label'] for r in rows],[0,1,2])
        self.assertEqual(audit['conflicting_normalized_groups'],1)
        self.assertEqual(audit['excluded_records'],4)
        self.assertEqual(ledger[3]['reasons'],['duplicate_normalized_text'])
        with self.assertRaises(ValueError):m.clean(records+[row(7,'unknown','spam')])

    def test_group_templates_cross_class_stay_connected(self):
        records=[row(0,'Verify account https://one.invalid 123'),row(1,'Verify account https://two.invalid 456','gambling_ad'),
                 row(2,'entirely different topic',template_group='shared'),row(3,'another unrelated topic',template_group='shared')]
        g=m.legacy.group_rows(records)
        self.assertEqual(g[0],g[1]);self.assertEqual(g[2],g[3])

    def test_allocation_nested_and_cv_disjoint(self):
        y=np.tile(np.arange(3),40); groups=np.arange(len(y)); texts=['fixture '+str(i) for i in groups]
        parts,_=m.allocate(y,groups); again,_=m.allocate(y,groups)
        self.assertEqual(parts,again)
        self.assertEqual([len(v) for v in parts.values()],[72,24,24])
        self.assertTrue(all(not any(v.values()) for v in m.validate(y,texts,groups,parts).values()))
        training=sorted(parts['train60']+parts['validation20'])
        self.assertTrue(set(parts['train60'])<set(training))
        folds=m.folds_for(y,texts,groups,training)
        self.assertEqual(len(folds),5)
        self.assertEqual(sorted(i for f in folds for i in f['validation']),training)
        self.assertTrue(all(not set(parts['test20'])&set(f['train']+f['validation']) for f in folds))
        bad={k:list(v) for k,v in parts.items()};bad['test20'][0]=parts['train60'][0]
        with self.assertRaises(ValueError):m.validate(y,texts,groups,bad)

    def test_group_and_exact_text_leaks_rejected(self):
        y=np.tile(np.arange(3),3); groups=np.arange(9); texts=[str(i) for i in groups]
        parts=dict(train=[0,1,2],validation=[3,4,5],test=[6,7,8])
        groups[6]=0
        with self.assertRaises(ValueError):m.validate(y,texts,groups,parts)
        groups=np.arange(9);texts[6]=texts[0]
        with self.assertRaises(ValueError):m.validate(y,texts,groups,parts)

    def test_infeasible_grouping_fails_without_fallback(self):
        y=np.tile(np.arange(3),10)
        with self.assertRaises(ValueError):m.allocate(y,np.zeros(len(y),dtype=int))

    def test_pipeline_vocabulary_and_idf_never_learn_validation(self):
        texts=['ordinary appointment','verify password','casino slots','heldoutonly heldoutonly']
        y=np.array([0,1,2,0])
        for algorithm in ('svm','nb'):
            model=m.fit(algorithm,1.,texts,y,[0,1,2]); vec=model['tfidf']; before=vec.idf_.copy()
            model.predict([texts[3]])
            self.assertNotIn('heldoutonly',vec.vocabulary_)
            np.testing.assert_array_equal(before,vec.idf_)
            self.assertEqual(model.classes_.tolist(),[0,1,2])

    def test_confusion_metrics_orientation_and_dangerous_errors(self):
        result=m.metrics([0,0,1,1,2,2],[0,2,0,1,0,2])
        self.assertEqual(result['confusion_matrix'],[[1,0,1],[1,1,0],[1,0,1]])
        self.assertEqual(result['correct'],3);self.assertEqual(result['misclassified'],3)
        self.assertEqual(result['smishing_as_ham'],1);self.assertEqual(result['gambling_as_ham'],1)
        self.assertEqual(result['ham_as_gambling'],1)
        self.assertAlmostEqual(result['macro_f1'],47/90)

    def test_paired_cluster_bootstrap_identical_predictions_zero(self):
        y=np.tile(np.arange(3),10);g=np.arange(30)
        result=m.cluster_difference(y,y,y,g,repetitions=30)
        self.assertEqual(result['difference'],0)
        self.assertEqual(result['percentile_95'],[0.,0.])

    def test_freeze_detects_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp); dataset=output/'input.zip'; dataset.write_bytes(b'fixture')
            m.save(output/'configuration.json',dict(dataset=str(dataset),input_identity=dict(zip_sha256=m.legacy.digest(dataset))))
            payload=output/'membership.json';m.save(payload,dict(test=[1,2,3]))
            m.seal(output,'prepare-seal.json');m.verify(output,'prepare-seal.json')
            m.save(payload,dict(test=[1,2,4]))
            with self.assertRaises(ValueError):m.verify(output,'prepare-seal.json')

    def test_repeated_final_evaluation_refused_before_loading_messages(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp);m.save(output/'evaluation-started.json',{})
            m.save(output/'selection.json',[])
            with patch.object(m,'verify'),patch.object(m,'load') as read:
                with self.assertRaises(FileExistsError):m.evaluate(output)
                read.assert_not_called()


if __name__=='__main__':unittest.main()
