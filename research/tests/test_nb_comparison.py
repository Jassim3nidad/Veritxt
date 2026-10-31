"""Leakage and inference guards using synthetic text only."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import numpy as np
from sklearn.naive_bayes import MultinomialNB
from smishguard import nb_comparison as n


def row(identity, text, label='ham', **extra):
    return dict(id=identity, text=text, label=label, source=n.SOURCES[0], needs_review='False',
                language='English', **extra)


class NbComparisonTests(unittest.TestCase):
    def test_clean_deduplicates_and_holds_all_sides_of_conflicts(self):
        rows = [row('a','Same SMS'), row('b',' SAME  sms '),
                row('c','Conflict text'), row('d','conflict text','smishing'),
                row('e','casino','gambling_ad'), row('f','flagged')]
        rows[-1]['needs_review'] = 'True'
        kept, ledger, audit = n.clean(rows)
        self.assertEqual([r['id'] for r in kept], ['a'])
        self.assertEqual(audit['conflicting_normalized_groups'], 1)
        self.assertIn('conflicting_normalized_labels', ledger[2]['reasons'])
        self.assertIn('conflicting_normalized_labels', ledger[3]['reasons'])

    def test_whitespace_only_and_conservative_stopwords_preserve_filipino(self):
        text = 'May\t₱5,000.50 sa https://example.invalid/?a=12 at an no not 123.45 a'
        vec = n.vectorizer(); tokens = vec.build_analyzer()(n.normalize(text))
        for value in ['may','₱5,000.50','sa','https://example.invalid/?a=12','at','an','no','not','123.45','a']:
            self.assertIn(value, tokens)
        self.assertNotIn('the', vec.build_analyzer()('the account'))

    def test_grouping_joins_url_number_templates_and_metadata(self):
        rows = [row('a','Verify bank account https://one.invalid 123'),
                row('b','Verify bank account https://two.invalid 456'),
                row('c','Kumain ka na ba', template_group='manual'),
                row('d','Unrelated topic', template_group='manual')]
        groups = n.group_rows(rows)
        self.assertEqual(groups[0], groups[1]); self.assertEqual(groups[2], groups[3])

    def test_split_reproducible_and_leakage_rejected(self):
        rows = [row(str(i), 'unique '+str(i), label=i%2) for i in range(120)]
        groups = np.arange(120)
        a = n.split_rows(rows, groups); self.assertEqual(a, n.split_rows(rows, groups))
        self.assertEqual([len(a[k]) for k in ('train','validation','test')], [84,18,18])
        b = dict(a); b['test'] = a['validation']
        with self.assertRaises(ValueError): n.validate_split(rows, groups, b)
        with self.assertRaises(ValueError): n.split_rows(rows, np.zeros(120))

    def test_vectorizer_fit_train_only_and_json_reference_parity(self):
        texts = ['safe bank statement ₱20', 'verify bank account https://example.invalid/claim',
                 'at may an no not', 'the ordinary conversation']
        vec = n.vectorizer(); x = vec.fit_transform([n.normalize(t) for t in texts]); model = MultinomialNB(alpha=.1).fit(x,[0,1,1,0])
        vec.transform(['reservedonly']); self.assertNotIn('reservedonly', vec.vocabulary_)
        with tempfile.TemporaryDirectory() as t:
            p = Path(t)/'candidate.json'; spec = dict(algorithm='nb')
            n.export_reference(vec, model, spec, p)
            report = n.inference_checks(vec, model, spec, n.load(p),texts)
            self.assertLess(report['max_score_error'], 1e-10)
            zero = vec.transform(['qzxqzx'])
            self.assertEqual(zero.nnz, 0)
            self.assertAlmostEqual(model.predict_proba(zero)[0,1], .5)
            self.assertFalse(n.load(p)['android_compatible'])

    def test_metric_orientation_and_validation_selection(self):
        m = n.metrics([0,0,0,1,1],[0,0,1,0,1])
        self.assertEqual(m['confusion_matrix'], [[2,1],[1,1]])
        self.assertAlmostEqual(m['fpr'], 1/3); self.assertEqual(m['fnr'], .5)
        a = dict(spec=dict(id='a'), validation=dict(f1=.9,recall=.9,precision=.9), model_bytes=99)
        b = dict(spec=dict(id='b'), validation=dict(f1=.8,recall=1.,precision=.7), model_bytes=1)
        self.assertEqual(n.choose([a,b]), 'a')
        self.assertEqual({s['alpha'] for s in n.matrix() if s['algorithm']=='nb'}, {.01,.1,.5,1.,2.})

    def test_freeze_rejects_changed_selection_data_or_code(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); data = root/'input'; data.write_text('private dataset')
            selected = root/'selection.json'; n.save(selected,dict(selected='A'))
            n.save(root/'freeze.json',dict(dataset_sha256=n.digest(data), implementation_sha256=n.digest(n.__file__),
                                         files={'selection.json':n.digest(selected)}))
            n.verify_freeze(data,root)
            n.save(selected,dict(selected='B'))
            with self.assertRaises(ValueError): n.verify_freeze(data,root)

    def test_zip_traversal_refused_before_reading(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t)/'d.zip'
            with zipfile.ZipFile(p,'w') as z: z.writestr('../bad.csv','x')
            with self.assertRaises(ValueError): n.read_dataset(p)

    def test_offline_wrapper_abstains_and_rejects_invalid_input(self):
        vec = n.vectorizer(); x = vec.fit_transform(['ordinary text', 'verify account'])
        model = MultinomialNB().fit(x, [0, 1])
        with tempfile.TemporaryDirectory() as t:
            p = Path(t)/'candidate.json'; n.export_reference(vec, model, dict(algorithm='nb'), p)
            exported = n.load(p)
            for text in ['', '???', 'qzxv', '1234567890']:
                result = n.reference_infer(exported, text)
                self.assertEqual(result['status'], 'unable_to_assess'); self.assertIsNone(result['suspicious'])
            for text in [None, '\x00', '\ud800', 'x'*10001]:
                self.assertEqual(n.reference_infer(exported,text)['status'], 'invalid_input')
            self.assertEqual(n.reference_infer(exported,'verify account')['status'], 'assessed')

    def test_evaluation_marker_refuses_repeated_or_interrupted_runs(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); (root/'test-evaluation-started.json').write_text('{}')
            with patch.object(n, 'verify_freeze'):
                with self.assertRaises(FileExistsError): n.evaluate(root/'input',root)


if __name__ == '__main__': unittest.main()
