"""Guard the new split, training-only selection and frozen test boundary."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from smishguard import holdout_8020 as h
from smishguard import nb_comparison as n


class Holdout8020Tests(unittest.TestCase):
    def test_exact_counts_stratification_group_separation_and_determinism(self):
        rows = [dict(label=i % 2, text='unique '+str(i)) for i in range(120)]
        groups = np.arange(120)//2
        parts = h.split_rows(rows, groups)
        self.assertEqual(parts, h.split_rows(rows, groups))
        self.assertEqual([len(parts[p]) for p in ('train', 'test')], [96, 24])
        self.assertEqual(sum(rows[i]['label'] for i in parts['test']), 12)
        self.assertFalse(set(groups[parts['train']]) & set(groups[parts['test']]))

    def test_fractional_record_rounding(self):
        rows = [dict(label=i % 2, text='unique '+str(i)) for i in range(123)]
        parts = h.split_rows(rows, np.arange(123))
        self.assertEqual(len(parts['test']), 25)
        self.assertEqual(sum(rows[i]['label'] for i in parts['test']), 12)

    def test_infeasible_whole_groups_fail_without_row_random_fallback(self):
        rows = [dict(label=i//20, text='unique '+str(i)) for i in range(40)]
        with self.assertRaisesRegex(ValueError, 'infeasible'):
            h.split_rows(rows, np.arange(40)//10)

    def test_inner_cv_covers_training_once_and_excludes_outer_test(self):
        rows = [dict(label=i % 2, text='unique '+str(i)) for i in range(120)]
        groups = np.arange(120)//2
        parts = h.split_rows(rows, groups)
        folds = h.training_folds(rows, groups, parts['train'])
        covered = []
        for fold in folds:
            self.assertFalse(set(fold['train']+fold['validation']) & set(parts['test']))
            self.assertFalse(set(groups[fold['train']]) & set(groups[fold['validation']]))
            covered.extend(fold['validation'])
        self.assertEqual(sorted(covered), sorted(parts['train']))

    def test_feature_fitting_excludes_held_text(self):
        rows = [dict(text='ordinary family dinner', label=0),
                dict(text='verify account claim money', label=1),
                dict(text='reservedonlysentinel', label=1)]
        vec, model = h.fit(rows, [0, 1], dict(algorithm='nb', alpha=.1))
        vec.transform([rows[2]['text']])
        self.assertNotIn('reservedonlysentinel', vec.vocabulary_)
        self.assertEqual(model.class_count_.tolist(), [1, 1])

    def test_selection_uses_training_cv_even_if_test_ranking_disagrees(self):
        results = [dict(spec=dict(id='a'), cv=dict(f1=.8, recall=.8, precision=.8),
                        model_bytes=100, test=dict(f1=.5)),
                   dict(spec=dict(id='b'), cv=dict(f1=.7, recall=.9, precision=.9),
                        model_bytes=1, test=dict(f1=1.))]
        self.assertEqual(h.choose(results), 'a')

    def test_freeze_rejects_changed_selection_and_dataset(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); data = root/'data'; data.write_text('input')
            n.save(root/'selection.json', dict(selected='a'))
            n.save(root/'freeze.json', dict(dataset_sha256=n.digest(data),
                sources={'implementation.py':n.digest(h.__file__), 'nb_comparison.py':n.digest(n.__file__)},
                files={'selection.json':n.digest(root/'selection.json')}))
            h.verify_freeze(data, root)
            n.save(root/'selection.json', dict(selected='b'))
            with self.assertRaises(ValueError):
                h.verify_freeze(data, root)
            data.write_text('changed')
            with self.assertRaisesRegex(ValueError, 'Dataset changed'):
                h.verify_freeze(data, root)

    def test_repeat_evaluation_refused_before_predictions(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            (root/'test-evaluation-started.json').write_text('started')
            with patch.object(h, 'verify_freeze'):
                with self.assertRaises(FileExistsError):
                    h.evaluate(root/'data', root)


if __name__ == '__main__':
    unittest.main()
