import unittest
import numpy as np
from smishguard.preliminary_compare import assessable, deployment_metrics

class PreliminaryComparisonTests(unittest.TestCase):
    def test_abstentions_not_correct_negatives(self):
        r=deployment_metrics(['qwerty','hello','https://hello.example'],[0,1,1],[.1,.8,.2],.5,{'hello'})
        self.assertEqual(r['abstained'],2)
        self.assertEqual(r['abstained_labels'],{'ham':1,'smishing':1})
        self.assertEqual(r['conditional_metrics']['confusion'],dict(tn=0,fp=0,fn=0,tp=1))
    def test_policy_matches_android_edge_cases(self):
        for text in ('','!!!','1234','qwerty','xxxx','https://hello.example','xqzvplmkj','hello '*2001):
            self.assertFalse(assessable(text,{'hello','qwerty','xxxx'}))
        self.assertTrue(assessable('HELLO po',{'hello'}))
        self.assertTrue(assessable('Bayad na po',{'bayad'}))
    def test_all_abstain_has_no_metrics(self):
        r=deployment_metrics(['!!!'],[0],[.1],.5,{'hello'})
        self.assertIsNone(r['conditional_metrics'])
        self.assertEqual(r['coverage'],0)
