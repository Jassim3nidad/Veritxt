import unittest
from smishguard.mbert_experiment import redacted_case_view
from smishguard.preprocessing import normalize
from smishguard.deployment_policy import assessable

class MbertPreparationTests(unittest.TestCase):
    def test_case_preserved_while_underlying_baseline_view_stays_equal(self):
        for text in ('Hello HELLO hello','Kumusta po! Bayad 123.','É ñ 你好 visit https://example.invalid/x?code=12','Mail user@example.invalid now'):
            view=redacted_case_view(text)
            self.assertEqual(normalize(view),normalize(text))
            self.assertEqual(redacted_case_view(view),view)
        self.assertEqual(redacted_case_view('Hello HELLO hello'),'Hello HELLO hello')
    def test_reserved_placeholders_do_not_create_meaningful_input(self):
        vocabulary={'zznumberzz','zzemailzz','zzurlzz','hello'}
        for text in ('1234','user@example.invalid','https://example.invalid'):
            self.assertFalse(assessable(text,vocabulary))
        self.assertTrue(assessable('Hello 1234',vocabulary))
