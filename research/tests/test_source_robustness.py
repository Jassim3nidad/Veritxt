"""Guards against source/test leakage and misleading all-negative operating points."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from smishguard import source_robustness as s


class SourceRobustnessTests(unittest.TestCase):
    def test_source_fold_purges_related_groups_and_reserved_records(self):
        rows = [dict(text='fixture', label=i % 2, source='a' if i < 20 else 'b') for i in range(44)]
        groups = np.arange(44)
        groups[20] = groups[0]
        folds = s.source_folds(rows, groups, list(range(40)), list(range(40, 44)))
        for fold in folds:
            self.assertEqual(fold['related_records_purged'], 1)
            self.assertFalse(set(fold['train']) & set(fold['validation']))
            self.assertFalse(set(groups[fold['train']]) & set(groups[fold['validation']]))
            self.assertTrue(all(rows[i]['source'] != fold['source'] for i in fold['train']))
            self.assertFalse(set(fold['train'] + fold['validation']) & set(range(40, 44)))

    def test_single_class_source_complement_is_rejected(self):
        rows = [dict(source='a', label=0), dict(source='b', label=1)]
        with self.assertRaisesRegex(ValueError, 'two classes'):
            s.source_folds(rows, np.arange(2), [0, 1], [])

    def test_reserved_template_contamination_is_rejected(self):
        rows = [dict(source='a' if i < 10 else 'b', label=i % 2) for i in range(22)]
        groups = np.arange(22)
        groups[20] = groups[0]
        with self.assertRaises(AssertionError):
            s.source_folds(rows, groups, list(range(20)), [20, 21])

    def test_svm_features_and_calibration_use_only_training_records(self):
        rows = [dict(text=('ordinary payment received' if i % 2 == 0 else 'verify account suspended') + f' unique{i}',
            label=i % 2, source='private_source_marker') for i in range(60)]
        rows.append(dict(text='heldoutsecret heldoutsecret', label=1, source='held'))
        spec = dict(algorithm='svm', features='word-none', value=.1, min_df=2)
        artifact = s.fit(rows, np.arange(61) // 2, list(range(60)), spec)
        words = set(artifact['pipe']['tfidf'].get_feature_names_out())
        self.assertNotIn('heldoutsecret', words)
        self.assertNotIn('private_source_marker', words)
        self.assertNotIn(60, artifact['training_ids'])
        for fold in artifact['calibration_folds']:
            self.assertFalse(set(fold['train']) & set(fold['calibration']))
            self.assertNotIn(60, fold['train'] + fold['calibration'])
        self.assertTrue(np.isfinite(s.score(artifact, ['heldoutsecret', 'verify suspended'])).all())

    def operating_fixture(self, positive=.8, negative=.1):
        rows = []
        scores = []
        for source in ('a', 'b'):
            for i in range(120):
                y = int(i >= 100)
                rows.append(dict(label=y, source=source, language='English'))
                scores.append(positive if y else negative)
        return rows, np.asarray(scores)

    def test_feasible_threshold_uses_inclusive_score_boundary(self):
        rows, scores = self.operating_fixture()
        result = s.choose_threshold(rows, list(range(len(rows))), scores)
        self.assertTrue(result['goal_met'])
        self.assertEqual(result['threshold'], .8)
        self.assertEqual(result['minimum_supported_source_recall'], 1)
        self.assertEqual(result['worst_supported_fpr'], 0)

    def test_fallback_never_credits_all_negative_classifier(self):
        rows, scores = self.operating_fixture(positive=.2, negative=.7)
        result = s.choose_threshold(rows, list(range(len(rows))), scores)
        self.assertFalse(result['goal_met'])
        self.assertGreaterEqual(result['minimum_supported_source_recall'], s.RECALL_FLOOR)
        self.assertEqual(result['worst_supported_fpr'], 1)
        self.assertEqual(result['threshold'], .2)

    def test_positive_only_source_has_no_fabricated_false_positive_rate(self):
        rows, scores = self.operating_fixture()
        rows.extend(dict(label=1, source='positive-only', language='English') for _ in range(25))
        scores = np.concatenate((scores, np.full(25, .8)))
        result = s.choose_threshold(rows, list(range(len(rows))), scores)
        source = result['metrics']['subgroups']['source:positive-only']
        self.assertIsNone(source['false_positive_rate'])
        self.assertEqual(source['ham_support'], 0)
        self.assertTrue(result['goal_met'])

    def test_goal_feasibility_precedes_favorable_f1(self):
        def record(goal, fpr, f1):
            return dict(mean_feature_count=10, operating_point=dict(goal_met=goal,
                macro_source_f1=f1, worst_supported_fpr=fpr, pooled_recall=.9))
        self.assertGreater(s.rank(record(True, .01, .7)), s.rank(record(False, .1, .99)))
        self.assertGreater(s.rank(record(False, .05, .6)), s.rank(record(False, .2, .95)))

    def test_original_hash_change_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            original = root / 'original.bin'
            original.write_bytes(b'unchanged model')
            manifest = {'original.bin': s.w.digest(original)}
            s.verify_protected(root, manifest)
            original.write_bytes(b'changed model')
            with self.assertRaisesRegex(ValueError, 'Protected original changed'):
                s.verify_protected(root, manifest)


if __name__ == '__main__':
    unittest.main()
