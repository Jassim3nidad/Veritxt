import csv
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from smishguard.validation_stage import agreement, matches, read_responses, FIELDS, texts_from_bytes, utc, intake, INTAKE, sha


class ValidationStage(unittest.TestCase):
    def test_blank_agreement_is_undefined(self):
        self.assertIsNone(agreement([])['kappa'])
        self.assertIsNone(agreement([])['observed'])

    def test_known_kappa_and_missing_category_preserved(self):
        result=agreement([('phishing','phishing'),('genuine','genuine'),('phishing','genuine'),('genuine','phishing')])
        self.assertEqual(result['observed'],.5)
        self.assertEqual(result['kappa'],0)
        self.assertEqual(agreement([('uncertain','uncertain'),('genuine','genuine')])['kappa'],1)

    def test_single_category_kappa_undefined(self):
        self.assertIsNone(agreement([('genuine','genuine')]*3)['kappa'])

    def test_normalized_exact_and_near_templates(self):
        history=['your account is suspended verify your password now','meeting at home tomorrow afternoon']
        self.assertEqual(matches('Your account is suspended. Verify your password now!',history),[0])
        self.assertEqual(matches('your account is suspended verify password now',history),[0])
        self.assertEqual(matches('bring fresh fruit and water to the picnic',history),[])

    def test_archived_tables_and_recursive_json(self):
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w') as z:
            z.writestr('data.csv','message_text,label\nfictional example,ham\n')
            z.writestr('nested.json',json.dumps({'records':[{'text_redacted':'another fictional example'}]}))
        inventory=[]
        self.assertEqual(set(texts_from_bytes(stream.getvalue(),'archive.zip',inventory)),{'fictional example','another fictional example'})
        self.assertEqual(sum(i.get('text_values',0) for i in inventory),2)

    def test_response_blanks_allowed_but_text_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'a.csv'
            def write(text):
                with p.open('w',newline='',encoding='utf-8') as f:
                    w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerow({'review_id':'fixture','redacted_text':text})
            write('Fictional text')
            self.assertEqual(read_responses(p,{'fixture':'Fictional text'})['fixture']['decision'],'')
            write('Changed text')
            with self.assertRaises(ValueError):read_responses(p,{'fixture':'Fictional text'})

    def test_utc_requires_offset(self):
        with self.assertRaises(ValueError):utc('2026-10-06T10:00:00')
        with self.assertRaises(ValueError):utc('2026-10-06T10:00:00+08:00')
        self.assertEqual(utc('2026-10-06T02:00:00Z').hour,2)

    def test_intake_holds_history_and_unverified_privacy_without_predictions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);index=root/'history';index.mkdir()
            (index/'index.json').write_text(json.dumps({'normalized_texts':['fictional scheduled meeting reminder'],'exact_sha256':[]}))
            (index/'inventory.json').write_text(json.dumps({'index_sha256':sha(index/'index.json')}))
            freeze=root/'freeze.json';freeze.write_text('{}')
            source=root/'intake.csv'
            row={k:'' for k in INTAKE};row.update(intake_id='synthetic-fixture',redacted_text='Fictional scheduled meeting reminder',
                received_at_utc='2001-01-02T00:00:00Z',collected_at_utc='2001-01-03T00:00:00Z',
                collector_code='fixture',source_use_evidence='fixture',receipt_evidence_ref='fixture',
                permission_status='approved',privacy_review_status='pending',privacy_reviewer='fixture',prior_model_viewing='no')
            with source.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=INTAKE);w.writeheader();w.writerow(row)
            with patch('smishguard.validation_stage.private_output'),patch('smishguard.validation_stage.verify_freeze',return_value={'created_utc':'2001-01-01T00:00:00Z'}):
                intake(source,index,freeze,root/'screen')
            ledger=json.loads((root/'screen/ledger.json').read_text())
            self.assertIn('historical_overlap',ledger[0]['reasons'])
            self.assertIn('privacy_review_status_unresolved',ledger[0]['reasons'])
            self.assertEqual(json.loads((root/'screen/summary.json').read_text())['evaluation'],'not performed')


if __name__=='__main__':unittest.main()
