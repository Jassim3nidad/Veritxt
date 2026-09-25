import copy
import importlib.util
from pathlib import Path
import unittest
from smishguard import candidate_evidence as evidence


class CandidateEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.rows = evidence.read_table(evidence.EVIDENCE/'calibration_metrics.csv',
                                       ('protocol', 'variant', 'seed', 'model', *evidence.METRICS))
        self.bins = evidence.read_table(evidence.EVIDENCE/'reliability.csv',
                                       ('model', 'band', 'messages', 'avg_score', 'actual_scam_rate'))

    def test_supplied_aggregate_consistency(self):
        result = evidence.review()
        self.assertEqual((result['metric_rows'], result['reliability_rows']), (30, 20))
        self.assertEqual(result['pooled_observations_not_unique_messages']['raw'], (1216, 222))

    def test_missing_or_duplicate_seed_rejected(self):
        for rows in (self.rows[:-1], self.rows + [self.rows[0]]):
            with self.assertRaises(ValueError): evidence.validate_metrics(rows)

    def test_nonfinite_and_invalid_metrics_rejected(self):
        for value in ('nan', 'inf', '-0.1', '1.1'):
            rows = copy.deepcopy(self.rows); rows[0]['brier'] = value
            with self.assertRaises(ValueError): evidence.validate_metrics(rows)

    def test_inconsistent_f1_rejected(self):
        self.rows[0]['f1'] = '0'
        with self.assertRaises(ValueError): evidence.validate_metrics(self.rows)

    def test_invalid_bins_rejected(self):
        for key, value in [('avg_score', 'nan'), ('actual_scam_rate', '0.12345'), ('messages', '0')]:
            rows = copy.deepcopy(self.bins); rows[0][key] = value
            with self.assertRaises(ValueError): evidence.validate_reliability(rows)

    def test_missing_or_duplicate_bins_rejected(self):
        for rows in (self.bins[:-1], self.bins + [self.bins[0]]):
            with self.assertRaises(ValueError): evidence.validate_reliability(rows)

    def test_staged_path_guards(self):
        path = Path(__file__).resolve().parents[2]/'scripts/check_staged.py'
        spec = importlib.util.spec_from_file_location('staged_check', path)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        for name in ('training/model_export_calibrated.json', 'nested/data/rows.csv',
                     'training/fresh_test_messages.csv', 'training/candidate_parity_cases.json',
                     'nested/model.safetensors', 'local.sqlite', 'research/runs/output.csv',
                     'android/app/src/development/assets/model.json'):
            self.assertTrue(module.forbidden_path(name), name)
        self.assertFalse(module.forbidden_path('research/candidate_review/calibration_metrics.csv'))
        self.assertFalse(module.forbidden_path('research/model_evidence/MODEL_INTEGRATION.md'))
        self.assertFalse(module.forbidden_path('android/app/src/main/java/ph/smishguard/data/PreferencesRepository.kt'))
        self.assertTrue(module.forbidden_path('android/app/src/main/java/ph/smishguard/data/rows.csv'))


if __name__ == '__main__': unittest.main()
