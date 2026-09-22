import csv
import json
from pathlib import Path
import tempfile
import unittest
from smishguard.annotation_results import summarize
from smishguard.review_packets import ANNOTATION_FIELDS
from smishguard.evaluate import metrics
from smishguard.uncertainty import cluster_intervals


class CompletionTests(unittest.TestCase):
    def sheets(self, root, labels):
        paths=[]
        for n,values in enumerate(labels):
            path=root/f'annotator-{n}.csv';paths.append(path)
            with path.open('w',newline='',encoding='utf-8') as f:
                writer=csv.DictWriter(f,fieldnames=ANNOTATION_FIELDS);writer.writeheader()
                writer.writerows(dict(id=f'SG_{i}',text_redacted=f'Fictional software fixture {i}',category=c,
                    language='en',financial_scope='true',note='') for i,c in enumerate(values))
        return paths

    def test_cohen_known_result_and_no_text_export(self):
        with tempfile.TemporaryDirectory() as d:
            paths=self.sheets(Path(d),[['legitimate','legitimate','financial_phishing','financial_phishing'],
                                      ['legitimate','financial_phishing','financial_phishing','financial_phishing']])
            result=summarize(paths)
            self.assertEqual(result['raw_pairwise_agreement'],.75)
            self.assertEqual(result['kappa'],.5)
            self.assertEqual(result['disagreement_records'],1)
            self.assertNotIn('Fictional',json.dumps(result));self.assertNotIn('SG_',json.dumps(result))

    def test_fleiss_and_degenerate_agreement(self):
        with tempfile.TemporaryDirectory() as d:
            paths=self.sheets(Path(d),[['legitimate','financial_phishing']]*3)
            self.assertEqual(summarize(paths)['kappa'],1)
            paths=self.sheets(Path(d),[['legitimate']]*3)
            self.assertIsNone(summarize(paths)['kappa'])

    def test_reject_missing_duplicate_and_changed_text(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            paths=self.sheets(root,[['legitimate'],['']])
            with self.assertRaises(ValueError): summarize(paths)
            paths=self.sheets(root,[['legitimate'],['legitimate','uncertain']])
            with self.assertRaises(ValueError): summarize(paths)
            paths=self.sheets(root,[['legitimate'],['legitimate']])
            paths[1].write_text(paths[1].read_text().replace('Fictional','Altered'))
            with self.assertRaises(ValueError): summarize(paths)
            with self.assertRaises(ValueError): summarize([paths[0],paths[0]])

    def test_adjudication_requires_complete_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);paths=self.sheets(root,[['legitimate'],['uncertain']])
            adjudication=root/'final.csv'
            adjudication.write_text('id,final_category,adjudicator_id,reason\nSG_0,uncertain,reviewer,Insufficient context\n')
            self.assertEqual(summarize(paths,adjudication)['final_adjudicated_label_counts'],{'uncertain':1})
            adjudication.write_text('id,final_category,adjudicator_id,reason\nSG_0,legitimate,,\n')
            with self.assertRaises(ValueError): summarize(paths,adjudication)

    def test_metrics_known_and_undefined_cases(self):
        result=metrics([0,0,1,1],[.1,.8,.4,.9],.5)
        self.assertEqual(result['accuracy'],.5);self.assertEqual(result['specificity'],.5)
        result=metrics([1,1],[.3,.8],.5)
        self.assertIsNone(result['roc_auc']);self.assertIsNone(result['specificity'])
        for y,p in [([],[]),([0],[float('nan')]),([2],[.5]),([0],[1.1])]:
            with self.assertRaises(ValueError): metrics(y,p,.5)

    def test_cluster_bootstrap_reproducible_and_bounded(self):
        args=([0,0,1,1],[.1,.8,.4,.9],['a','a','b','b'],.5)
        a=cluster_intervals(*args,repetitions=30)
        self.assertEqual(a,cluster_intervals(*args,repetitions=30))
        self.assertLess(a['intervals']['roc_auc']['valid_replicates'],30)
        self.assertIsNone(cluster_intervals([0,1],[.1,.9],['a','a'],.5)['intervals'])

    def test_supplied_evaluation_rejects_normalized_training_overlap(self):
        from smishguard.supplied_evaluate import independent_groups
        with self.assertRaises(ValueError):
            independent_groups(['Fictional account 123'],[dict(text_redacted='Fictional account 456')])
        self.assertEqual(len(independent_groups(['Fictional account 123'],[dict(text_redacted='Weather is sunny')])),1)

    def test_freeze_preserves_groups_without_raw_text_and_refuses_overwrite(self):
        from unittest.mock import patch
        from smishguard.freeze_dataset import freeze
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'source.csv';ledger=root/'ledger.csv'
            source.write_text('id,message_text,source\na,Fictional software sample,fixture\nb,Another fictional sample,fixture\n')
            ledger.write_text('id,template_group\na,GROUP_0\nb,GROUP_0\n')
            with patch('smishguard.freeze_dataset.private_output'):
                report=freeze(source,ledger,root/'manifest.json',root/'summary.json')
                manifest=json.loads((root/'manifest.json').read_text())
                self.assertEqual({r['group_id'] for r in manifest['records']},{'GROUP_0'})
                self.assertNotIn('Fictional',json.dumps(manifest))
                self.assertEqual(report['rows'],2)
                with self.assertRaises(FileExistsError): freeze(source,ledger,root/'manifest.json',root/'summary2.json')


if __name__=='__main__':unittest.main()
