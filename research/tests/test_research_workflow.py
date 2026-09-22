"""Synthetic in-memory software checks. No real records/approval or research results."""
import csv
import hashlib
import json
import pickle
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from smishguard.intake import FIELDS, validate_record, eligible_category
from smishguard.import_data import import_records, agreement
from smishguard.data import read_dataset, template_groups, split_rows
from smishguard.train import fit_candidate, write_json, main as train_main
from smishguard.compare import seals, verify_selection
from smishguard.evaluate import evaluate_selected
from smishguard.linear_export import export_linear


def record(**updates):
    row=dict.fromkeys(FIELDS, "")
    row.update(id="SOFTWARE_TEST_ONLY", text_redacted="hello kumusta", language="en",
        source_type="participant_donation",source_ref="SOFTWARE_TEST_ONLY",
        consent_verified="true",redaction_verified="true",financial_scope="true",
        permitted_use_status="documented",permitted_use_reference="SOFTWARE_TEST_ONLY",study_role="primary",
        annotator_1_id="TEST_A",annotator_2_id="TEST_B",annotator_1="legitimate",annotator_2="legitimate",
        adjudication_status="agreed",adjudicated_category="legitimate")
    row.update(updates)
    return row


def write_intake(path, rows):
    with path.open("w",encoding="utf-8",newline="") as file:
        writer=csv.DictWriter(file,fieldnames=FIELDS)
        writer.writeheader();writer.writerows(rows)


def fit_rows():
    rows=[]
    splits={}
    for part, words in [("train",["hello kumusta", "urgent verify"]), ("validation",["hello validationonly", "verify validationonly"]), ("calibration",["hello calibrationonly", "urgent calibrationonly"]), ("test",["UNTOUCHED_TEST_ONLY", "UNTOUCHED_TEST_ONLY"])]:
        splits[part]=[]
        for label, text in enumerate(words):
            splits[part].append(len(rows))
            rows.append(dict(id=f"TEST_{len(rows)}",text_redacted=text,label=str(label),annotator_1="",annotator_2=""))
    return rows,splits


class ResearchWorkflowTests(unittest.TestCase):
    def test_aggregators_assessed_by_evidence_not_source_name(self):
        for source in ("aggregator", "public_archive", "social_post", "external_collection", "institutional_publication"):
            row = record(source_type=source, consent_verified="false")
            validate_record(row)
            self.assertEqual(eligible_category(row), ("legitimate", None))
            row["permitted_use_status"] = "pending"
            self.assertEqual(eligible_category(row)[1], "permitted_use_not_documented")
        self.assertEqual(eligible_category(record(consent_verified="false"))[1], "donation_consent_not_verified")

    def test_supplementary_cannot_enter_primary_training(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/"input.csv"; output=Path(d)/"supplementary"
            write_intake(source,[record(source_type="external_collection",study_role="supplementary",consent_verified="false")])
            self.assertEqual(import_records(source,output,"SOFTWARE_TEST_ONLY", "supplementary"),(1,0))
            self.assertEqual(len(read_dataset(output/"approved.csv", "supplementary")),1)
            with self.assertRaises(ValueError): read_dataset(output/"approved.csv")

    def test_permitted_use_documentation_is_specific(self):
        row=record(permitted_use_reference="")
        with self.assertRaises(ValueError): validate_record(row)
        self.assertEqual(eligible_category(record(permitted_use_status="not_permitted"))[1], "use_not_permitted")
        self.assertEqual(eligible_category(record(study_role="undecided"))[1], "study_role_not_selected")
    def test_language_support_suppresses_small_or_one_class_estimates(self):
        from smishguard.evaluate import language_metrics
        rows=[dict(language="en",label="0") for _ in range(25)] + [dict(language="taglish",label=str(i%2)) for i in range(30)]
        report=language_metrics(rows,[.4]*len(rows),.5)
        self.assertIsNone(report["en"]["metrics"])
        self.assertIsNotNone(report["taglish"]["metrics"])
        self.assertEqual(report["taglish"]["support"],dict(ham=15,smishing=15))
        self.assertIsNone(report["fil"]["metrics"])
    def test_annotation_metadata_never_enters_features(self):
        rows,splits=fit_rows();a,_=fit_candidate(rows,splits)
        for r in rows:r.update(source="NEVER_A_FEATURE",notes="NEVER_A_FEATURE",attack_type="NEVER_A_FEATURE")
        b,_=fit_candidate(rows,splits)
        self.assertEqual(a["vectorizer"].vocabulary_,b["vectorizer"].vocabulary_)
        self.assertEqual(a["model"].coef_.tolist(),b["model"].coef_.tolist())
    def test_supplied_export_validation_and_unicode_math(self):
        import copy
        from smishguard.convert_supplied import validate,portable
        from sklearn.feature_extraction.text import TfidfVectorizer
        import numpy as np
        m=dict(model_type="logistic_regression",classes=["ham","smishing"],ngram_range=[1,2],lowercase=True,vocabulary={"a":0,"ñ":1,"a ñ":2},idf=[1.,1.5,2.],coef=[.1,-.2,.3],intercept=-.4)
        validate(m)
        v=TfidfVectorizer(vocabulary=m["vocabulary"],lowercase=True,ngram_range=(1,2),token_pattern=r"(?u)\b\w+\b");v.idf_=np.array(m["idf"])
        for text in ["A Ñ", "a unknown ñ", "á _ a ñ", ""]:
            margin=float((v.transform([text])@np.array(m["coef"]))[0]+m["intercept"])
            self.assertAlmostEqual(portable(m,text),float(1/(1+np.exp(-margin))),places=12)
        for key,value in [("classes",["smishing","ham"]),("ngram_range",[1,1]),("vocabulary",{"a":0,"b":0,"c":2}),("idf",[1]),("coef",[float("nan"),0,0])]:
            bad=copy.deepcopy(m);bad[key]=value
            with self.assertRaises(ValueError):validate(bad)
    def test_import_quarantines_uncertain_disagreements_and_other_scams(self):
        rows=[record(),record(id="TEST_UNCERTAIN",annotator_1="uncertain",annotator_2="uncertain",adjudication_status="pending",adjudicated_category=""),
              record(id="TEST_OTHER",annotator_1="other_spam_scam",annotator_2="other_spam_scam",adjudicated_category="other_spam_scam"),
              record(id="TEST_DISPUTED",annotator_2="financial_phishing",adjudication_status="pending",adjudicated_category="")]
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/"input.csv";output=Path(d)/"import"
            write_intake(source,rows)
            self.assertEqual(import_records(source,output,"SOFTWARE_TEST_ONLY"),(1,3))
            approved=read_dataset(output/"approved.csv")
            self.assertEqual([r["label"] for r in approved],["0"])
            report=json.loads((output/"import-report.json").read_text())
            self.assertEqual(report["agreement"]["paired_records"],4)
            self.assertEqual(report["agreement"]["observed_agreement"],.75)
            self.assertNotIn("text_redacted",(output/"import-report.json").read_text())
    def test_adjudication_preserves_original_labels(self):
        r=record(annotator_1="uncertain",annotator_2="financial_phishing",adjudication_status="adjudicated",adjudicated_category="financial_phishing",adjudicator_id="TEST_C",adjudication_note="Synthetic software-only resolution")
        validate_record(r)
        self.assertEqual(eligible_category(r),("financial_phishing",None))
        self.assertEqual(r["annotator_1"],"uncertain")
        r["adjudicator_id"]=""
        with self.assertRaises(ValueError): eligible_category(r)
    def test_bad_provenance_pii_and_annotation_contracts_fail(self):
        for change in [dict(source_type="synthetic"),dict(source_type="unknown"),dict(text_redacted="https://example.com/private"),dict(text_redacted="contact 09123456789"),dict(annotator_2_id="TEST_A"),dict(received_at="2025-01-01"),dict(url_count="0",url_max_host_length="10",url_digit_fraction="0",url_max_depth="0")]:
            with self.subTest(change=change),self.assertRaises(ValueError): validate_record(record(**change))
        self.assertIsNone(eligible_category(record(redaction_verified="false"))[0])
    def test_malformed_and_blank_csv_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"input.csv"
            for text in [",".join(FIELDS)+"\n", "id,id\nx,x\n", ",".join(FIELDS)+"\nshort,row\n"]:
                p.write_text(text)
                with self.assertRaises(ValueError): import_records(p,Path(d)/"out","SOFTWARE_TEST_ONLY")
    def test_undefined_agreement_is_null(self):
        self.assertIsNone(agreement([record()])["cohen_kappa"])
        self.assertEqual(agreement([record()])["observed_agreement"],1)
        self.assertIsNone(agreement([])["observed_agreement"])
    def test_manual_templates_and_normalized_duplicates_union(self):
        rows=[dict(text_redacted="abc 123",template_group="GROUP_A"),dict(text_redacted="abc 999"),dict(text_redacted="different language",template_group="GROUP_A"),dict(text_redacted="!!!!"),dict(text_redacted="????")]
        groups=template_groups(rows)
        self.assertEqual(groups[0],groups[1]);self.assertEqual(groups[0],groups[2]);self.assertEqual(groups[3],groups[4])
    def test_temporal_group_purge_and_permissive_overlap(self):
        # Artificial clock values used ONLY to exercise software ordering.
        rows=[dict(id=f"T{i}",label=str(i%2),received_at=(datetime(2000,1,1,tzinfo=timezone.utc)+timedelta(hours=i)).isoformat()) for i in range(200)]
        groups=list(range(200));groups[-1]=groups[0]
        temporal=split_rows(rows,groups,"time",42)
        self.assertIn(0,temporal["train"]);self.assertIn(199,temporal["test"])
        purged=split_rows(rows,groups,"time-group",42)
        self.assertEqual(set(purged["excluded"]),{0,199})
        partitions=[purged[k] for k in ("train","validation","calibration","test")]
        for a,b in zip(partitions,partitions[1:]): self.assertLess(max(a),min(b))
        random=split_rows(rows,[0]*200,"random",42)
        self.assertTrue(all(random.values())) # Intentionally permits one template in every partition.
        with self.assertRaises(ValueError): split_rows(rows,[0]*200,"group",42)
    def test_fit_never_reads_final_test_and_fits_vocabulary_only_on_train(self):
        rows,splits=fit_rows()
        class Forbidden(dict):
            def __getitem__(self,key): raise AssertionError("Final-test record accessed while fitting")
        for i in splits["test"]:rows[i]=Forbidden(rows[i])
        for name in ("lr","nb","svm"):
            artifact,_=fit_candidate(rows,splits,name)
            vocab=artifact["vectorizer"].vocabulary_
            self.assertNotIn("validationonly",vocab);self.assertNotIn("calibrationonly",vocab)
    def test_final_labels_cannot_change_calibration_or_threshold(self):
        rows,splits=fit_rows()
        before,_=fit_candidate(rows,splits)
        for i in splits["test"]:rows[i].update(text_redacted="completely different",label="1")
        after,_=fit_candidate(rows,splits)
        self.assertEqual(before["threshold"],after["threshold"])
        self.assertEqual(before["calibrator"].coef_.tolist(),after["calibrator"].coef_.tolist())
    def test_minimum_is_not_bypassed(self):
        rows,_=fit_rows()
        with patch("smishguard.train.read_dataset",return_value=rows),self.assertRaisesRegex(ValueError,"1,200"):
            train_main(["unused.csv","unused-output","--data-history","previously_used"])
    def test_sealed_selection_final_once_and_dataset_hash(self):
        rows,splits=fit_rows();artifact,_=fit_candidate(rows,splits)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);run=root/"lr";run.mkdir();dataset=root/"fixture.csv"
            dataset.write_text("SOFTWARE_FIXTURE_ONLY")
            write_json(run/"splits.json",{**{k:[rows[i]["id"] for i in v] for k,v in splits.items()},'groups':{r['id']:i for i,r in enumerate(rows)}})
            for r in rows: r['source_ref']='fixture_source'
            write_json(run/"run.json",dict(dataset_sha256=hashlib.sha256(dataset.read_bytes()).hexdigest(),evaluation_scope="synthetic_software_test_only",seed=42,preprocessing_version='sg-ascii-v1',condition='deployment',analyzer='word'))
            with (run/"research-model.pkl").open("wb") as f:pickle.dump(artifact,f)
            write_json(run/"model.json",export_linear(artifact["vectorizer"],artifact["model"],artifact["calibrator"],artifact["threshold"],synthetic=True))
            selection=root/"selection.json";write_json(selection,dict(selected_run="lr",sha256=seals(run),split="group"))
            with patch("smishguard.evaluate.read_dataset",return_value=rows):
                evaluate_selected(dataset,run,selection)
                with self.assertRaisesRegex(ValueError,"already exists"):evaluate_selected(dataset,run,selection)
            (run/"final-test.json").unlink();dataset.write_text("CHANGED_FIXTURE")
            with self.assertRaisesRegex(ValueError,"Dataset changed"):evaluate_selected(dataset,run,selection)
            (run/"model.json").write_text("{}")
            with self.assertRaisesRegex(ValueError,"changed"):verify_selection(run,selection)


if __name__ == "__main__":unittest.main()
