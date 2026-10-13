"""Validate independent operating-point partitions, interval arithmetic and immutable fits."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from smishguard import predeployment_validation as v


class PredeploymentValidationTests(unittest.TestCase):
    def test_zero_errors_does_not_mean_zero_population_error(self):
        interval=v.wilson(0,55)
        self.assertEqual(interval['low'],0)
        self.assertGreater(interval['high'],.06)
        self.assertIsNone(v.wilson(0,0))

    def test_paired_bootstrap_preserves_identical_predictions(self):
        y=np.array([0,0,1,1,0,1]);pred=np.array([False,True,True,False,False,True])
        result=v.intervals(y,pred,pred,np.arange(len(y)),repetitions=30)
        self.assertEqual(result['intervals']['paired_f1_delta_vs_baseline']['low'],0)
        self.assertEqual(result['intervals']['paired_f1_delta_vs_baseline']['high'],0)

    def test_nested_source_fit_and_threshold_never_see_outer_records(self):
        rows=[dict(id=str(i),text='fixture',label=i%2,source='a' if i<20 else 'b') for i in range(40)]
        # One cross-source group must be purged from source-complement fitting.
        groups=np.arange(40);groups[20]=groups[0]
        observed=[]
        def fitted(data,g,ids,spec):
            observed.append((list(ids),dict(spec)))
            return dict(spec=spec)
        def score(artifact,texts):return np.linspace(.1,.9,len(texts))
        with tempfile.TemporaryDirectory() as temp, patch.object(v.w,'fit_candidate',side_effect=fitted),patch.object(v.w,'score',side_effect=score):
            out=Path(temp)
            v.nested_sources(rows,groups,out)
            for source in ('a','b'):
                parts=json.loads((out/'source-heldout'/source/'partitions.json').read_text())
                outer=set(parts['test']);train=set(parts['train']);val=set(parts['validation'])
                self.assertFalse(outer&(train|val))
                self.assertFalse(set(groups[list(outer)])&set(groups[list(train|val)]))
                self.assertFalse(train&val)
                self.assertEqual(parts['outer_related_records_purged'],1)
            self.assertEqual(len(observed),6)

    def test_export_rejects_feature_contract_change(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        vectorizer=TfidfVectorizer(ngram_range=(1,1)).fit(['normal bank','verify account'])
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(AssertionError):
                v.export_selected({'pipe':{'tfidf':vectorizer,'classifier':None},'calibrator':None},[],[],Path(temp))


if __name__=='__main__':unittest.main()
