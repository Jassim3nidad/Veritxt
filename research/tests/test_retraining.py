"""Synthetic deterministic guards; these fixtures never enter reported experiments."""
from pathlib import Path
import json
import tempfile
import unittest
import zipfile
import numpy as np
from smishguard import retraining as r


class RetrainingTests(unittest.TestCase):
    def test_label_mapping_is_explicit_and_rejects_spam(self):
        for a,b in [('ham',0),('smishing',1),('0',0),('1',1),(0,0),(1,1)]:
            self.assertEqual(r.label_value(a),b)
        for value in ['spam','marketing',True,1.0,None,'phishing']:
            with self.assertRaises(ValueError):r.label_value(value)

    def test_conflict_and_flagged_labels_are_held(self):
        records=[dict(id='a',text='Same sms',label=0),dict(id='b',text='SAME sms',label=1),
            dict(id='c',text='pending',label=0,needs_review=True),dict(id='d',text='valid',label=0),
            dict(id='e',text='generic spam',label='spam')]
        rows,ledger,audit=r.audit_records(records)
        self.assertEqual([x['id'] for x in rows],['d'])
        self.assertEqual(audit['conflicting_exact_groups'],1)
        self.assertEqual(ledger[0]['reason'],'conflicting_exact_labels_requires_review')
        self.assertEqual(rows[0]['original_label'],0)
        self.assertEqual(audit['missing']['label'],0)

    def test_normalization_preserves_evidence(self):
        text='Paki\tverify PHP 5,000 sa https://example.invalid/?q=1!'
        self.assertEqual(r.normalized(text),'Paki verify PHP 5,000 sa https://example.invalid/?q=1!')
        rows,_,_=r.audit_records([dict(text=text,label=1)])
        self.assertEqual(rows[0]['raw_text'],text)

    def test_missing_encoding_csv_width_and_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'d.csv'
            with self.assertRaises(FileNotFoundError):r.read_input(p)
            p.write_bytes(b'text,label\n\xff,ham')
            with self.assertRaises(UnicodeDecodeError):r.read_input(p)
            p.write_text('text,label\nhello,ham,extra',encoding='utf-8')
            with self.assertRaises(ValueError):r.read_input(p)
        with self.assertRaises(ValueError):r.audit_records([dict(id='x',text='a',label=0),dict(id='x',text='b',label=1)])

    def test_zip_never_selects_unrelated_member_or_traversal(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'d.zip'
            with zipfile.ZipFile(p,'w') as z:z.writestr('../d.csv','text,label\nx,ham')
            with self.assertRaises(ValueError):r.read_input(p)
            with zipfile.ZipFile(p,'w') as z:
                z.writestr('a.csv','text,label\nx,ham');z.writestr('b.csv','text,label\ny,smishing')
            with self.assertRaises(ValueError):r.read_input(p)
            rows,meta=r.read_input(p,'b.csv');self.assertEqual(rows[0]['label'],'smishing');self.assertEqual(meta['member'],'b.csv')

    def test_near_exact_and_metadata_components(self):
        rows=[dict(text='Verify your bank account at https://one.invalid',source='s'),
            dict(text='Verify your bank account at https://two.invalid',source='t'),
            dict(text='Unrelated everyday lunch conversation',source='s',sender='sender-a'),
            dict(text='Please submit a financial receipt',source='s',sender='sender-a')]
        g=r.group_records(rows);self.assertEqual(g[0],g[1]);self.assertEqual(g[2],g[3])

    def test_split_disjoint_reproducible_and_infeasible_fails(self):
        rows=[dict(text=f'row {i}',label=i%2) for i in range(120)];g=np.arange(120)
        a=r.make_split(rows,g);self.assertEqual(a,r.make_split(rows,g))
        self.assertEqual([len(a[p]) for p in ('train','validation','test')],[84,18,18])
        bad=dict(a);bad['test']=a['validation']
        with self.assertRaises(ValueError):r.validate_split(rows,g,bad)
        with self.assertRaises(ValueError):r.make_split(rows,np.zeros(120))

    def fixture(self):
        rows=[dict(text=('safe ham chatting' if i%2==0 else 'phishing account verify')+' token'+chr(97+i//26)+chr(97+i%26),label=i%2) for i in range(60)]
        spec=dict(id='fixture',family='C',algorithm='svm',combined=True,min_df=1,max_features=None,word_ngrams=[1,2],char_ngrams=[3,5],value=1.,class_weight=None)
        return rows,np.arange(60),spec

    def test_fold_local_fit_excludes_validation_and_serializes(self):
        rows,g,spec=self.fixture();rows[59]['text']='reserveduniquechar token'
        a=r.fit(rows,g,list(range(48)),spec)
        vocab=a['pipe']['tfidf'].get_feature_names_out().tolist()
        self.assertFalse(any('reserveduniquechar' in term for term in vocab))
        for f in a['calibration_folds']:
            self.assertFalse(set(f['train'])&set(f['calibration']))
            self.assertTrue(set(f['train']+f['calibration'])<=set(range(48)))
        import pickle
        b=pickle.loads(pickle.dumps(a))
        np.testing.assert_array_equal(r.score(a,['safe ham','account verify'],'sigmoid'),r.score(b,['safe ham','account verify'],'sigmoid'))

    def test_positive_mapping_raw_margin_and_sigmoid(self):
        rows,g,spec=self.fixture();a=r.fit(rows,g,list(range(60)),spec)
        raw=r.score(a,['safe ham chatting','phishing account verify'],'raw')
        calibrated=r.score(a,['safe ham chatting','phishing account verify'],'sigmoid')
        self.assertLess(raw[0],raw[1]);self.assertTrue((calibrated>=0).all() and (calibrated<=1).all())
        a['pipe']['classifier'].classes_=np.array([1,0])
        with self.assertRaises(ValueError):r.score(a,['hello'],'raw')

    def test_threshold_policy_rejects_trivial_and_uses_score_boundary(self):
        y=[0]*100+[1]*10;s=np.r_[np.linspace(-3,-1,100),np.linspace(.1,.9,10)]
        op=r.choose_threshold(y,s,False)
        self.assertEqual(op['metrics']['recall'],1)
        self.assertNotEqual(op['threshold'],.5)
        self.assertIsNone(r.choose_threshold(y,np.zeros(110),True))
        self.assertEqual(r.metrics(y,s,op['threshold'],False)['brier'],None)

    def test_reproducible_fit_and_malformed_inputs(self):
        rows,g,spec=self.fixture();a=r.fit(rows,g,list(range(60)),spec);b=r.fit(rows,g,list(range(60)),spec)
        np.testing.assert_array_equal(r.score(a,['','???','verify'],'raw'),r.score(b,['','???','verify'],'raw'))
        with self.assertRaises(ValueError):r.score(a,[None],'raw')

    def test_matrix_paired_original_and_weighted_and_alpha_tuning(self):
        matrix=r.matrix();self.assertEqual({s['family'] for s in matrix},set('ABCDE'))
        self.assertTrue(all(s['class_weight'] is None for s in matrix[:sum(s['class_weight'] is None for s in matrix)]))
        self.assertGreater(len({s['value'] for s in matrix if s['family']=='E'}),1)
        self.assertTrue(all(s['word_ngrams']==[1,2] and s['char_ngrams'][0]==3 for s in matrix if s['family'] in ('C','D')))

    def test_freeze_detects_modified_artifact_and_dataset(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);d=p/'input';d.write_text('dataset');f=p/'model';f.write_text('weights')
            r.save(p/'freeze.json',dict(dataset_sha256=r.digest(d),source_sha256=r.digest(Path(r.__file__)),files={'model':r.digest(f)}))
            r.verify_freeze(d,p);f.write_text('tampered')
            with self.assertRaises(ValueError):r.verify_freeze(d,p)

    def test_holdout_marker_refuses_repeated_or_interrupted_evaluation(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);d=p/'input';d.write_text('private input')
            rows=[dict(text=f'fixture {i}',label=i%2) for i in range(120)]
            split=r.make_split(rows,np.arange(120))
            r.save(p/'dataset.json',rows)
            r.save(p/'splits.json',dict(partitions=split,groups=list(range(120))))
            r.save(p/'selection.json',dict(selected=None,family_winners={}))
            r.save(p/'freeze.json',dict(dataset_sha256=r.digest(d),source_sha256=r.digest(Path(r.__file__)),files={},history='previously_used'))
            r.evaluate(d,p)
            with self.assertRaises(FileExistsError):r.evaluate(d,p)

    def test_small_subgroups_report_counts_without_invented_scores(self):
        rows=[dict(label=0,language='Taglish',source='s',category='Unknown') for _ in range(5)]
        m=r.subgroup_metrics(rows,list(range(5)),[.1]*5,.5,True)
        self.assertEqual(m['language:Taglish']['records'],5)
        self.assertIsNone(m['language:Taglish']['metrics'])


if __name__=='__main__':unittest.main()
