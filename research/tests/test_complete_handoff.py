import copy
import unittest
from smishguard.complete_handoff import validate_candidate, content_findings, convert


class CompleteHandoffTests(unittest.TestCase):
    def model(self):
        return dict(model_type="logistic_regression_calibrated", vocabulary={"hello": 0, "account": 1},
                    idf=[1., 2.], coef=[-.4, .7], intercept=-.2, calibration_a=2., calibration_b=-.1,
                    threshold=.4, ngram_range=[1, 2], lowercase=True, l2_normalize=True)

    def test_conversion_preserves_parameters_and_policy(self):
        model = self.model(); result = convert(model, "0" * 64)
        self.assertEqual(result['weights'], model['coef'])
        self.assertEqual(result['idf'], model['idf'])
        self.assertEqual(result['bias'], model['intercept'])
        self.assertEqual(result['calibration'], dict(a=2., b=-.1))
        self.assertEqual(result['threshold_comparison'], 'greater_or_equal')
        self.assertFalse(result['automatic_warnings_approved'])
        self.assertEqual(result['calibration_status'], 'fitted_unvalidated')

    def test_invalid_models_fail_without_silent_changes(self):
        for patch in [dict(coef=[float('nan'), 1]), dict(calibration_a=float('inf')),
                      dict(calibration_b=True), dict(threshold=.5), dict(idf=[0., 1.]),
                      dict(vocabulary={"hello": 0, "account": 0}), dict(l2_normalize=False)]:
            model = self.model(); model.update(patch)
            with self.assertRaises(ValueError): validate_candidate(model)

    def test_identifier_screen_keeps_weights_and_vocabulary_unchanged(self):
        model = self.model()
        # Assembled artificial pattern; not a real contact or a research datum.
        token = '09' + '0' * 9
        model['vocabulary'] = {token: 0, 'to ' + token: 1}
        before = copy.deepcopy(model)
        findings = content_findings(model)
        self.assertEqual(len(findings['phone_shaped_tokens']), 1)
        self.assertEqual(len(findings['phone_bearing_features']), 2)
        self.assertEqual(model, before)
