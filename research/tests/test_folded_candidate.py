import unittest
from smishguard.folded_candidate import validate_folded
from smishguard.vocabulary_policy import identifier_like, select_terms, screen


class FoldedCandidateTests(unittest.TestCase):
    def model(self):
        return dict(model_type='logistic_regression',model_version='lr-calibrated-4',
            vocabulary={'hello':0,'account':1},idf=[1.,2.],coef=[-.4,.7],intercept=-.2,
            classes=['ham','smishing'],ngram_range=[1,2],lowercase=True,
            calibration=dict(method='platt',a=2.,b=-.1,folded_into_coef_and_intercept=True))

    def test_contract_requires_explicit_folding_and_positive_class(self):
        self.assertEqual(validate_folded(self.model()), self.model())
        for field,value in [('folded_into_coef_and_intercept',False),('a',float('nan')),('a',-1),('b',True)]:
            m=self.model();m['calibration'][field]=value
            with self.assertRaises(ValueError): validate_folded(m)
        m=self.model();m['classes'].reverse()
        with self.assertRaises(ValueError): validate_folded(m)

    def test_identifier_screen_never_changes_export(self):
        m=self.model();m['vocabulary']={'ref'+'1'*5:0,'hello':1}
        original=dict(m['vocabulary'])
        with self.assertRaises(ValueError): validate_folded(m)
        self.assertEqual(m['vocabulary'],original)
        for term in ['a '+'9'*5,'xxx'+'1234','123xxx','XXx12','ab**cd']:
            self.assertTrue(identifier_like(term))
        self.assertFalse(identifier_like('amount 1234'))
        self.assertEqual(screen(['hello'])['identifier_pattern_features'],0)

    def test_future_vocabulary_selection_is_deterministic_before_fitting(self):
        terms=['beta','alpha','ref'+'1'*5,'gamma'];counts=[5,5,100,3]
        self.assertEqual(select_terms(terms,counts,2),['alpha','beta'])
        self.assertEqual(select_terms(terms[::-1],counts[::-1],2),['alpha','beta'])
