"""Fail-closed label and historical-fit reuse boundaries for supplied updates."""
from pathlib import Path
import unittest
from unittest.mock import patch

from smishguard.new_dataset_compare import label_value, reuse_mbert_oof


class SuppliedUpdateBoundaries(unittest.TestCase):
    def test_only_explicit_binary_labels_are_supported(self):
        self.assertEqual(label_value('ham'),0)
        self.assertEqual(label_value('smishing'),1)
        for label in ('gambling_ad','spam','fraud','legitimate','1','uncertain'):
            with self.assertRaisesRegex(ValueError,'Unsupported binary label'):
                label_value(label)

    def test_cached_fit_rejects_changed_labels_or_ordered_texts(self):
        cfg=dict(baseline_seed=20260929,mbert_seed=20261005,versions={'torch':'fixed'})
        rows=[dict(id='synthetic',text='synthetic SMS',label=0)]
        for changed in ([dict(id='synthetic',text='synthetic SMS',label=1)],
                        [dict(id='synthetic',text='different synthetic SMS',label=0)]):
            with patch('smishguard.ensemble_compare.context',side_effect=[(cfg,rows,{}),(cfg,changed,{})]):
                with self.assertRaisesRegex(ValueError,'inputs or fold assignments differ'):
                    reuse_mbert_oof(Path('unused-new'),Path('unused-old'))

    def test_cached_fit_rejects_changed_folds_or_dependencies(self):
        cfg=dict(baseline_seed=20260929,mbert_seed=20261005,versions={'torch':'fixed'})
        rows=[dict(id='synthetic',text='synthetic SMS',label=0)]
        with patch('smishguard.ensemble_compare.context',side_effect=[(cfg,rows,{'fold':1}),(cfg,rows,{'fold':2})]):
            with self.assertRaisesRegex(ValueError,'inputs or fold assignments differ'):
                reuse_mbert_oof(Path('unused-new'),Path('unused-old'))
        changed=dict(cfg,versions={'torch':'different'})
        with patch('smishguard.ensemble_compare.context',side_effect=[(cfg,rows,{}),(changed,rows,{})]):
            with self.assertRaisesRegex(ValueError,'settings/environment differ'):
                reuse_mbert_oof(Path('unused-new'),Path('unused-old'))


if __name__=='__main__':
    unittest.main()
