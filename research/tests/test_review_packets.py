"""Synthetic fixtures only; no actual personal messages or approvals."""
import csv
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from smishguard.review_packets import prepare, release, private_output, REDACTION_FIELDS
from smishguard.source_matching import indexes, match


class ReviewPacketTests(unittest.TestCase):
    def test_private_output_boundary(self):
        with self.assertRaises(ValueError): private_output(Path('docs/unsafe-review'))

    def test_blinding_release_and_redaction_gate(self):
        with tempfile.TemporaryDirectory() as directory, patch('smishguard.review_packets.private_output'):
            root=Path(directory); source=root/'input.csv'; packet=root/'packet'
            with source.open('w',encoding='utf-8',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=['id','message_text','label','source','notes']);writer.writeheader()
                writer.writerow(dict(id='PRIVATE_ORIGIN',message_text='=SOFTWARE_TEST_ONLY',label='SECRET_LABEL',source='SECRET_SOURCE',notes='SECRET_NOTE'))
            self.assertEqual(prepare(source,packet),1)
            pending=(packet/'annotator-a-pending.csv').read_text(encoding='utf-8')
            for hidden in ('PRIVATE_ORIGIN','SOFTWARE_TEST_ONLY','SECRET_LABEL','SECRET_SOURCE','SECRET_NOTE'):
                self.assertNotIn(hidden,pending)
            with self.assertRaisesRegex(ValueError,'No human-verified'): release(packet,root/'unreleased')
            with (packet/'redaction-review.csv').open(encoding='utf-8',newline='') as f: rows=list(csv.DictReader(f))
            self.assertTrue(rows[0]['text_for_review'].startswith("'="))
            rows[0].update(text_redacted='hello kumusta',redaction_status='verified',reviewer_id='TEST_REVIEWER')
            with (packet/'redaction-review.csv').open('w',encoding='utf-8',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=REDACTION_FIELDS);writer.writeheader();writer.writerows(rows)
            self.assertEqual(release(packet,root/'released'),1)
            for who in ('a','b'):
                with (root/f'released/annotator-{who}.csv').open(encoding='utf-8') as f:r=list(csv.DictReader(f))[0]
                self.assertEqual(r['text_redacted'],'hello kumusta');self.assertEqual(r['category'],'')
                self.assertNotIn('source',r)

    def test_matching_is_conservative_and_preserves_ambiguity(self):
        index=indexes([{'text':'hello  world'},{'text':'hello world'},{'text':'hello world'}])
        self.assertEqual(match('hello world',index)['candidate_rows'],[3,4])
        self.assertEqual(match('hello\nworld',index)['kind'],'whitespace_only')
        self.assertIsNone(match('HELLO world',index))
        self.assertIsNone(match('hello scam',index))


if __name__ == '__main__': unittest.main()
