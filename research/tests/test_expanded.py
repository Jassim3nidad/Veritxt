"""Regression boundaries for the new experiment using fictional fixtures only."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from smishguard.data import template_groups, split_rows
from smishguard.expanded_prepare import clean
from smishguard.expanded_train import checked, threshold
from smishguard.expanded_evaluate import deployment
from smishguard.mbert_experiment import redacted_case_view
from smishguard.preprocessing import normalize
from smishguard.train import write_json
from smishguard import fair_compare as fair

class ExpandedBoundaries(unittest.TestCase):
    def test_common_private_view_preserves_case_and_baseline_identity(self):
        text='Hello <NAME>, code 123 at https://account.example/a. Contact person@example.invalid'
        view=redacted_case_view(clean(text))
        self.assertIn('Hello',view)
        self.assertNotIn('123',view)
        self.assertNotIn('account.example',view)
        self.assertNotIn('person@example.invalid',view)
        self.assertEqual(normalize(view),normalize(clean(text)))

    def test_audited_grouping_merges_different_supplied_keys(self):
        rows=[dict(id=str(i),text_redacted=text,template_group=key,label=0) for i,(text,key) in enumerate([
            ('Your code is 111','a'),('Your code is 222','b'),('Completely distinct meeting message','c')])]
        groups=template_groups(rows)
        self.assertEqual(groups[0],groups[1]);self.assertNotEqual(groups[0],groups[2])

    def test_abstention_does_not_become_correct_negative(self):
        result=deployment(['123456','Hello'],np.array([1,0]),np.array([.1,.1]),.5,['hello','zznumberzz'])
        self.assertEqual(result['coverage'],.5)
        self.assertEqual(result['abstained_labels']['smishing'],1)
        self.assertEqual(result['conditional_metrics']['confusion']['tn'],1)

    def test_threshold_ties_choose_higher(self):
        self.assertAlmostEqual(threshold(np.array([0,1]),np.array([.1,.9])),.9)

    def test_changed_partition_blocks_training(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for name in ('dataset.json','splits.json','case-view.json'):write_json(root/name,[])
            protocol=root/'protocol.md';protocol.write_text('frozen protocol')
            prep={k:fair.digest(path) for path,k in ((root/'dataset.json','dataset_sha256'),(root/'splits.json','split_sha256'),(root/'case-view.json','case_view_sha256'),(protocol,'protocol_sha256'))}
            write_json(root/'preparation.json',prep);write_json(root/'exposure-summary.json',{})
            write_json(root/'splits.json',{'changed':True})
            with patch('smishguard.expanded_train.PROTOCOL',protocol),self.assertRaisesRegex(ValueError,'Frozen'):
                checked(root)

if __name__=='__main__':unittest.main()
