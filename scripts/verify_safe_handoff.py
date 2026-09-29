"""Safe-file-only evidence checks; never imports training scripts or opens private data."""
import ast
import csv
import json
from pathlib import Path
import re
import statistics
import unittest

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'research/model_evidence'
MOBILE = re.compile(r'(?<![\w.])(?:\+?63|0)[ -]?9(?:[ -]?\d){9}(?!\d)')


def rows(name):
    with (EVIDENCE / name).open(encoding='utf-8', newline='') as source:
        return list(csv.DictReader(source))


class SafeHandoffTest(unittest.TestCase):
    def test_failed_emulator_run_cleans_permissions_and_restores_settings(self):
        import importlib.util
        import subprocess
        from unittest.mock import patch
        spec = importlib.util.spec_from_file_location('handoff_emulator', ROOT / 'scripts/emulator_verify.py')
        verifier = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(verifier)
        calls = []
        def fake_run(command, **kwargs):
            args = command[3:]
            calls.append(args)
            output = b''
            if args[:2] == ['shell', 'getprop']:
                output = b'36' if args[-1] == 'ro.build.version.sdk' else b'1'
            elif args[:3] == ['shell', 'settings', 'get']:
                output = {'font_scale': b'1.0', 'wifi_on': b'1', 'airplane_mode_on': b'0'}[args[-1]]
            elif args[:3] == ['shell', 'am', 'instrument']:
                output = b'FAILURES!!! synthetic harness failure'
            return subprocess.CompletedProcess(command, 0, stdout=output)
        with patch.object(verifier.subprocess, 'run', side_effect=fake_run), \
                patch('sys.argv', ['emulator_verify.py']), patch.object(Path, 'write_text'):
            with self.assertRaises(RuntimeError):
                verifier.main()
        self.assertEqual(calls.count(['shell', 'pm', 'clear', 'ph.smishguard']), 2)
        self.assertIn(['shell', 'settings', 'put', 'system', 'font_scale', '1.0'], calls)
        self.assertIn(['shell', 'cmd', 'connectivity', 'airplane-mode', 'disable'], calls)
        self.assertIn(['shell', 'svc', 'wifi', 'enable'], calls)

    def test_python_syntax_without_execution(self):
        scripts = list(EVIDENCE.glob('*.py'))
        self.assertEqual(len(scripts), 4)
        for source in scripts:
            ast.parse(source.read_text(encoding='utf-8'), filename=source.name)

    def test_only_allowlisted_evidence_and_no_mobile_literals(self):
        allowed = {'README.md', 'MODEL_EVALUATION.md', 'MODEL_INTEGRATION.md', 'THRESHOLD_POLICY.md',
                   'comparative_analysis_v2.py', 'lr_tuned.py', 'lr_5seed_bootstrap.py', 'train_final_lr.py',
                   'comparative_analysis_v2.csv', 'lr_5seed_results.csv', 'lr_tuned_5seed_results.csv',
                   'lr_best_params.json'}
        self.assertEqual({p.name for p in EVIDENCE.iterdir()}, allowed)
        for source in EVIDENCE.iterdir():
            # Assert only filename/status, never print a matched value.
            self.assertFalse(bool(MOBILE.search(source.read_text(encoding='utf-8'))), source.name)

    def test_dataset_counts_against_existing_aggregate_record(self):
        audit = json.loads((ROOT / 'docs/dataset-audit.json').read_text())
        self.assertEqual(audit['rows'], 1276)
        self.assertEqual(audit['labels'], {'ham': 1054, 'smishing': 222})
        self.assertEqual(sum(audit['labels'].values()), audit['rows'])

    def test_final_hyperparameters_and_tokenizer(self):
        parameters = json.loads((EVIDENCE / 'lr_best_params.json').read_text())
        self.assertEqual(parameters, dict(C=2, penalty='l2', solver='liblinear', class_weight='balanced'))
        source = ast.parse((EVIDENCE / 'train_final_lr.py').read_text())
        calls = {n.func.id: n for n in ast.walk(source) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        lr = {k.arg: ast.literal_eval(k.value) for k in calls['LogisticRegression'].keywords}
        self.assertEqual({k: lr[k] for k in parameters}, parameters)
        vec = {k.arg: ast.literal_eval(k.value) for k in calls['TfidfVectorizer'].keywords}
        self.assertEqual(vec, dict(lowercase=True, ngram_range=(1, 2), max_features=5000, token_pattern=r'\b\w+\b'))

    def test_csv_arithmetic_and_documented_discrepancies(self):
        comparison = {r['Algorithm']: r for r in rows('comparative_analysis_v2.csv')}
        self.assertEqual(len(comparison), 5)
        lr = comparison['Logistic Regression']
        self.assertEqual([float(lr[k]) for k in ('Accuracy', 'Smishing Precision', 'Smishing Recall', 'Smishing F1')],
                         [.9453, .8163, .8889, .8511])
        self.assertEqual(max(comparison, key=lambda k: float(comparison[k]['Smishing F1'])), 'Random Forest')
        self.assertEqual(max(comparison, key=lambda k: float(comparison[k]['Macro F1 (CV std)'])), 'Multinomial Naive Bayes')
        means = []
        for name in ('lr_5seed_results.csv', 'lr_tuned_5seed_results.csv'):
            data = rows(name)
            self.assertEqual([int(r['seed']) for r in data], [42, 7, 123, 2024, 99])
            for row in data:
                p, r, f = (float(row[k]) for k in ('smishing_precision', 'smishing_recall', 'smishing_f1'))
                self.assertAlmostEqual(2 * p * r / (p + r), f)
            means.append(statistics.mean(float(r['smishing_f1']) for r in data))
        self.assertAlmostEqual(means[0], .8610173636585963)
        self.assertAlmostEqual(means[1], .8643458175218611)
        self.assertAlmostEqual(means[1] - means[0], .0033284538632648)

    def test_saved_reference_score_consistency_not_new_inference(self):
        conversion = json.loads((ROOT / 'docs/model-conversion.json').read_text())
        expected = [.9081, .4698, .7279, .1555, .8875]
        self.assertEqual([r['rounded_expected'] for r in conversion['guide_references']], expected)
        for row in conversion['guide_references']:
            self.assertLess(abs(row['python_score'] - row['rounded_expected']), .00005)
        test = (ROOT / 'android/app/src/androidTest/java/ph/smishguard/SuppliedModelTest.kt').read_text()
        self.assertIn('1e-10', test)

    def test_android_safety_and_schema_contract_unchanged(self):
        model = (ROOT / 'android/app/src/main/java/ph/smishguard/model/SuppliedDetector.kt').read_text()
        self.assertIn('if (candidate) score >= .4 else score > .5', model)
        self.assertIn('Detection.Success(isSuspicious(score, candidate)', model)
        # Runtime nextDown/equal/nextUp checks live in CandidatePolicyTest.
        self.assertIn('object ModelLoader', model)
        export = ast.parse((EVIDENCE / 'train_final_lr.py').read_text())
        dictionary = next(n.value for n in export.body if isinstance(n, ast.Assign)
                          and any(isinstance(t, ast.Name) and t.id == 'export' for t in n.targets))
        keys = {ast.literal_eval(k) for k in dictionary.keys}
        self.assertTrue({'coef', 'idf', 'vocabulary', 'classes', 'ngram_range', 'intercept'} <= keys)
        for path in (ROOT / 'android/app/src').rglob('AndroidManifest.xml'):
            self.assertNotIn('android.permission.INTERNET', path.read_text())
            self.assertNotIn('android.permission.READ_CONTACTS', path.read_text())
        report = (ROOT / 'android/app/src/main/java/ph/smishguard/privacy/Reports.kt').read_text(encoding='utf-8')
        self.assertIn('class DisabledReportingRepository', report)
        self.assertIn('override val available = false', report)
        self.assertIn('result.synthetic || result.experimental', report)


if __name__ == '__main__':
    unittest.main(verbosity=2)
