"""Fictional records and reviewers only; these are never research observations."""
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import numpy as np
from smishguard import validation_stage as stage
from smishguard import review_completion as completion


class ReviewCompletion(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        for module in (stage,completion):
            p=patch.object(module,'private_output');p.start();self.addCleanup(p.stop)
        p=patch.object(completion,'verify_runtime',side_effect=lambda freeze:freeze);p.start();self.addCleanup(p.stop)

    def write(self,path,fields,rows):
        with path.open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)

    def responses(self):
        original_dir=self.root/'original';original_dir.mkdir()
        self.source=original_dir/'source.json'
        self.originals=[dict(id='fiction-'+str(i),text=text,label=i%2,group='group-'+str(i),language='en',source='synthetic')
                        for i,text in enumerate(('Meeting at noon','Verify your password','Bring water to the picnic','Fictional prize claim'))]
        stage.save(self.source,self.originals);self.review=self.root/'review';stage.prepare(self.source,self.review)
        mapping=stage.read(self.review/'coordinator/mapping.json')
        self.a=self.root/'a.csv';self.b=self.root/'b.csv'
        for who,path in (('a',self.a),('b',self.b)):
            rows=[dict(review_id=m[who],redacted_text=m['text'],decision='phishing' if i%2 else 'genuine',rationale='Synthetic fixture rationale',
                       privacy_issue='no',reviewer_code='fiction-'+who,completed_at_utc='2001-01-03T00:00:00Z') for i,m in enumerate(mapping)]
            self.write(path,stage.FIELDS,rows)
        self.write(self.review/'coordinator/attestations.csv',('packet','reviewer_code','independent_without_labels_or_predictions','signed_at_utc'),
                   [dict(packet=w,reviewer_code='fiction-'+w,independent_without_labels_or_predictions='yes',signed_at_utc='2001-01-02T00:00:00Z') for w in ('a','b')])
        self.write(self.review/'coordinator/privacy-release.csv',('review_id','redacted_text','release_status','privacy_reviewer','note'),
                   [dict(review_id=m['a'],redacted_text=m['text'],release_status='verified',privacy_reviewer='fiction-privacy',note='Synthetic fixture') for m in mapping])
        self.agreement=self.root/'agreement';stage.analyze(self.a,self.b,self.agreement,self.review)
        self.adjudication=self.agreement/'adjudication.csv'
        with self.adjudication.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
        for r in rows:r.update(final_decision=r['decision_a'],adjudicator_code='fiction-third',final_rationale='Synthetic confirmation',resolved_privacy='yes',completed_at_utc='2001-01-04T00:00:00Z')
        self.write(self.adjudication,tuple(rows[0]),rows)
        return rows

    def test_returns_agreement_version_and_original_preservation(self):
        self.responses();original=self.source.read_bytes()
        stage.adjudicate(self.adjudication,self.root/'final.json')
        version=self.root/'v1';completion.apply_labels(self.source,self.adjudication,version)
        self.assertEqual(stage.read(self.agreement/'agreement.json')['all_categories']['kappa'],1)
        self.assertEqual(stage.read(version/'dataset.json')[1]['label'],1)
        self.assertEqual(self.source.read_bytes(),original)
        with self.assertRaises(FileExistsError):completion.apply_labels(self.source,self.adjudication,version)

    def test_evidence_tamper_blocks_adjudication(self):
        self.responses();(self.agreement/'evidence/a.csv').write_text('changed')
        with self.assertRaisesRegex(ValueError,'evidence changed'):stage.validated_adjudication(self.adjudication)

    def test_changed_parent_and_third_reviewer_block_version(self):
        rows=self.responses();rows[0]['adjudicator_code']='fiction-a';self.write(self.adjudication,tuple(rows[0]),rows)
        with self.assertRaisesRegex(ValueError,'third adjudicator'):completion.apply_labels(self.source,self.adjudication,self.root/'bad')
        self.source.write_text('[]')
        with self.assertRaisesRegex(ValueError,'differs from packet'):completion.apply_labels(self.source,self.adjudication,self.root/'bad')

    def test_adjudication_before_returns_rejected(self):
        rows=self.responses();rows[0]['completed_at_utc']='2001-01-01T00:00:00Z';self.write(self.adjudication,tuple(rows[0]),rows)
        with self.assertRaisesRegex(ValueError,'predates'):stage.validated_adjudication(self.adjudication)

    def test_unknown_adjudication_columns_rejected(self):
        rows=self.responses();rows[0]['extra']='bad';self.write(self.adjudication,tuple(rows[0]),rows)
        with self.assertRaisesRegex(ValueError,'columns'):stage.validated_adjudication(self.adjudication)

    def test_history_header_alias_and_uci_headerless(self):
        archive=io.BytesIO()
        with zipfile.ZipFile(archive,'w') as z:
            z.writestr('SMSSpamCollection','ham\tSynthetic ordinary text\nspam\tSynthetic deceptive text\n')
            z.writestr('data.csv','v1, Message \nham,Synthetic column alias\n')
        values=list(stage.texts_from_bytes(archive.getvalue(),'fixture.zip',[]))
        self.assertEqual(len(values),3)

    def test_future_and_malformed_returns_rejected(self):
        path=self.root/'bad.csv'
        row=dict(review_id='fiction',redacted_text='Synthetic text',decision='genuine',rationale='Fixture',privacy_issue='no',reviewer_code='fiction',completed_at_utc='2999-01-01T00:00:00Z')
        self.write(path,stage.FIELDS,[row])
        with self.assertRaisesRegex(ValueError,'Future'):stage.read_responses(path,{'fiction':'Synthetic text'})
        path.write_text(','.join(stage.FIELDS)+'\nfiction,Synthetic text\n')
        with self.assertRaisesRegex(ValueError,'Malformed'):stage.read_responses(path,{'fiction':'Synthetic text'})

    def test_near_matching_checks_both_directions(self):
        # SequenceMatcher('tide','diet') is asymmetric; screening must be symmetric.
        self.assertEqual(stage.matches('tide',['diet'],minimum=.5),[0])
        self.assertEqual(stage.matches('diet',['tide'],minimum=.5),[0])

    def test_same_reviewer_cannot_supply_both_returns(self):
        self.responses()
        with self.b.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
        for r in rows:r['reviewer_code']='fiction-a'
        self.write(self.b,stage.FIELDS,rows)
        with self.assertRaisesRegex(ValueError,'distinct independent'):stage.analyze(self.a,self.b,self.root/'bad-agreement',self.review)

    def test_nonfinancial_phishing_and_uncertainty_are_preserved(self):
        rows=self.responses();rows[0].update(final_decision='phishing',final_rationale='Synthetic nonfinancial phishing mechanism');rows[2]['final_decision']='uncertain'
        self.write(self.adjudication,tuple(rows[0]),rows)
        target=self.root/'v2';completion.apply_labels(self.source,self.adjudication,target)
        self.assertEqual(stage.read(target/'dataset.json')[0]['label'],1)
        self.assertEqual(stage.read(target/'dataset.json')[0]['historical_label'],0)
        self.assertEqual(stage.read(target/'excluded.json'),[dict(id='fiction-2',reasons=['uncertain'])])

    def test_screen_admit_review_evaluate_and_single_open(self):
        freeze=self.root/'freeze.json';stage.save(freeze,dict(created_utc='2001-01-01T00:00:00Z',files={},models={name:dict(threshold=.5) for name in ('lr','nb','svm','mbert')}))
        index=self.root/'history';index.mkdir();stage.save(index/'index.json',dict(normalized_texts=[],exact_sha256=[]));stage.save(index/'inventory.json',dict(index_sha256=stage.sha(index/'index.json')))
        intake=self.root/'intake.csv';texts=['Meeting at noon','Verify password immediately','Bring water for a picnic','Fictional prize claim']
        rows=[dict.fromkeys(stage.INTAKE,'') for _ in texts]
        for i,r in enumerate(rows):r.update(intake_id=f'fiction-{i}',redacted_text=texts[i],received_at_utc='2001-01-02T00:00:00Z',collected_at_utc='2001-01-03T00:00:00Z',collector_code='fiction',source_use_evidence='fixture',receipt_evidence_ref='fixture',permission_status='approved',privacy_review_status='verified',privacy_reviewer='fixture',prior_model_viewing='no')
        self.write(intake,stage.INTAKE,rows);screen=self.root/'screen';stage.intake(intake,index,freeze,screen)
        semantic=self.root/'semantic.csv';self.write(semantic,completion.SEMANTIC,[dict(intake_id=r['intake_id'],decision='admit',template_group=r['intake_id'],semantic_overlap='no',evidence_verified='yes',reviewer_code='fiction',reviewed_at_utc='2001-02-02T00:00:00Z',reason='Synthetic fixture',language='en',source='synthetic') for r in rows])
        admitted=self.root/'admitted';completion.admit(intake,screen,semantic,freeze,admitted)
        # The same return workflow used above, using this frozen prospective source.
        self.responses()
        # Prepare an independent fixture cohort with the admitted source identity.
        review2=self.root/'fresh-review';stage.prepare(admitted/'dataset.json',review2)
        mapping=stage.read(review2/'coordinator/mapping.json')
        for who,path in (('a',self.a),('b',self.b)):
            self.write(path,stage.FIELDS,[dict(review_id=m[who],redacted_text=m['text'],decision='phishing' if i%2 else 'genuine',rationale='Synthetic',privacy_issue='no',reviewer_code='fiction-'+who,completed_at_utc='2001-02-03T00:00:00Z') for i,m in enumerate(mapping)])
        (review2/'coordinator/attestations.csv').write_bytes((self.review/'coordinator/attestations.csv').read_bytes())
        self.write(review2/'coordinator/privacy-release.csv',('review_id','redacted_text','release_status','privacy_reviewer','note'),[dict(review_id=m['a'],redacted_text=m['text'],release_status='verified',privacy_reviewer='fiction',note='Synthetic') for m in mapping])
        out=self.root/'fresh-agreement';stage.analyze(self.a,self.b,out,review2)
        queue=stage.read(out/'adjudication-basis.json')
        for r in queue:r.update(final_decision=r['decision_a'],adjudicator_code='fiction-third',final_rationale='Synthetic',resolved_privacy='yes',completed_at_utc='2001-02-04T00:00:00Z')
        self.write(out/'adjudication.csv',tuple(queue[0]),queue)
        dataset=self.root/'fresh-v1';completion.apply_labels(admitted/'dataset.json',out/'adjudication.csv',dataset)
        def scorer(rows,frozen):
            return ({name:np.array([.1,.9,.2,.8]) for name in frozen['models']},
                    {name:dict(threshold=.5,vocabulary=['meeting','password','water','prize']) for name in frozen['models']})
        report=self.root/'evaluation';completion.evaluate(dataset,freeze,report,scorer)
        self.assertEqual(len(stage.read(report/'comparison.json')['results']),4)
        self.assertTrue((report/'comparison.csv').is_file())
        with self.assertRaises(FileExistsError):completion.evaluate(dataset,freeze,self.root/'second-opening',scorer)


if __name__=='__main__':unittest.main()
