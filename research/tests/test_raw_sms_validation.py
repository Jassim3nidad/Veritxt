"""Raw input preprocessing boundaries and parity-critical masking order."""
import unittest
from smishguard.raw_sms_validation import raw_view,adapter_contract

class RawSmsValidationTests(unittest.TestCase):
    def test_url_is_masked_before_embedded_digits_and_email(self):
        self.assertEqual(raw_view('OTP 123 at HTTPS://example.invalid/user@example.invalid?otp=456'), 'OTP zznumberzz at zzurlzz')
        self.assertEqual(raw_view('email user@example.invalid ref 123'), 'email zzemailzz ref zznumberzz')

    def test_case_whitespace_and_placeholders_replay_training(self):
        self.assertEqual(raw_view(' , <REAL NAME> \u00a0Hello\u001cpo , '),'Hello po')
        self.assertEqual(raw_view('<BLANK> Hello po'),'Hello po')
        self.assertFalse(adapter_contract()['lowercase'])

    def test_ascii_mask_rules_do_not_silently_expand(self):
        self.assertEqual(raw_view('١٢٣٤ 1234'),'١٢٣٤ zznumberzz')
        self.assertIn('httpſ://',raw_view('httpſ://example.invalid/path'))
        self.assertEqual(raw_view('example.invalid'),'example.invalid')

    def test_unusable_inputs_remain_unusable_and_wrong_types_fail(self):
        self.assertEqual(raw_view(' <NAME> '),'')
        self.assertEqual(raw_view('123456'),'zznumberzz')
        with self.assertRaises(ValueError):raw_view(None)

if __name__=='__main__':unittest.main()
