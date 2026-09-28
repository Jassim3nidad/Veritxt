"""Synthetic packets only; no real labels or permissions created by these tests."""
import csv
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from smishguard.prepare_team_data import read_rows, analyze, pair_overlap, REQUIRED, ORIGIN_FIELDS
from smishguard.review_packets import prepare, ANNOTATION_FIELDS, REDACTION_FIELDS, write_csv
from smishguard.team_review import release_for_team, prepare_adjudication, validate_adjudication, ADJUDICATION_FIELDS


class TeamPreparationTests(unittest.TestCase):
    def test_cross_corpus_overlap_is_not_unseen_evidence(self):
        result=pair_overlap([dict(message_text="hello account 123")],
            [dict(message_text="hello account 123"),dict(message_text="hello account 456"),dict(message_text="different")])
        self.assertEqual(result['exact_right_rows'],1)
        self.assertEqual(result['normalized_right_rows'],2)
        self.assertEqual(result['direct_template_match_right_rows'],2)

    def test_reserved_test_assignments_reject_random_claim_and_group_leakage(self):
        from smishguard.fair_compare import prepare, reviewed_assignments
        from smishguard.train import main as legacy_train
        with self.assertRaisesRegex(ValueError,"reviewed --assignments"):
            legacy_train(["unused","unused","--data-history","prospectively_reserved"])
        with self.assertRaisesRegex(ValueError,"requires reviewed frozen"):
            prepare(Path("unused"),Path("unused"),"prospectively_reserved",Path("unused"))
        rows=[dict(id=f"TEST_{i}",label=str(i%2)) for i in range(8)]
        record=dict(reservation_reference="SYNTHETIC_EVIDENCE",train=["TEST_0","TEST_1"],
            validation=["TEST_2","TEST_3"],calibration=["TEST_4","TEST_5"],test=["TEST_6","TEST_7"])
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"assignments.json";path.write_text(json.dumps(record))
            self.assertEqual(reviewed_assignments(path,rows,list(range(8)))["test"],[6,7])
            with self.assertRaisesRegex(ValueError,"crossing template"):
                reviewed_assignments(path,rows,[0,1,2,3,4,5,0,7])
            record["test"]=["TEST_0","TEST_7"];path.write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError,"exactly once"):
                reviewed_assignments(path,rows,list(range(8)))

    def test_group_optimization_preserves_exhaustive_policy(self):
        from difflib import SequenceMatcher
        from smishguard.data import template_groups
        from smishguard.preprocessing import normalize
        import random
        rng=random.Random(31)
        rows=[dict(text_redacted="".join(rng.choices("abcd xyz",k=rng.randrange(0,35)))) for _ in range(100)]
        rows += [dict(text_redacted="hello account",template_group="MANUAL"),dict(text_redacted="other",template_group="MANUAL"),dict(text_redacted="hello account 123")]
        for similarity in (.4,.85,1.):
            parent=list(range(len(rows)))
            def root(i):
                while parent[i]!=i:i=parent[i]
                return i
            texts=[normalize(r['text_redacted']) for r in rows]
            for i in range(len(rows)):
                for j in range(i):
                    if texts[i]==texts[j] or (rows[i].get('template_group') and rows[i].get('template_group')==rows[j].get('template_group')) or SequenceMatcher(None,texts[i],texts[j],autojunk=False).ratio()>=similarity:
                        parent[root(i)]=root(j)
            self.assertEqual(template_groups(rows,similarity),[root(i) for i in range(len(rows))])

    def test_schema_and_candidate_checks_do_not_infer_privacy(self):
        for raw in (b"id,id\na,b\n", b"id,message_text\na\n"):
            with self.assertRaises(ValueError): read_rows(raw)
        rows=[]
        for i, label in enumerate(("ham", "smishing")):
            row=dict.fromkeys(REQUIRED, "")
            row.update(id=f"FIXTURE_{i}",message_text="hello account code 1234567",label=label,source=f"SOURCE_{i}")
            rows.append(row)
        report, groups, flags, _ = analyze(rows)
        self.assertEqual(report["exact"]["conflicting_label_groups"], 1)
        self.assertEqual(report["exact"]["cross_source_groups"], 1)
        self.assertTrue(flags[0]["long_digit_or_phone"])
        self.assertEqual(groups[0],groups[1])
        self.assertNotIn("message_text\": \"hello", json.dumps(report))

    def test_access_gate_blinding_immutable_responses_and_adjudication(self):
        with tempfile.TemporaryDirectory() as directory, patch("smishguard.review_packets.private_output"), patch("smishguard.team_review.private_output"):
            root=Path(directory); packet=root/"packet"; released=root/"release"
            source=root/"fixture.csv"
            write_csv(source, ("id","message_text","label","source"), [dict(id="ORIGINAL",message_text="hello account",label="HIDDEN",source="HIDDEN")])
            prepare(source, packet)
            mapping=json.loads((packet/"coordinator/mapping.json").read_text())
            key=mapping[0]["anonymous_id"]
            origins=root/"origin.csv"
            origin=dict(id=key,annotation_access_status="pending")
            write_csv(origins,ORIGIN_FIELDS,[origin])
            with self.assertRaisesRegex(ValueError,"No documented"): release_for_team(packet,origins,released)
            self.assertFalse(released.exists())
            origin.update(annotation_access_status="documented",annotation_access_reference="TEST_EVIDENCE",reviewer_id="TEST_REVIEWER")
            write_csv(origins,ORIGIN_FIELDS,[origin])
            with self.assertRaisesRegex(ValueError,"No human-verified"): release_for_team(packet,origins,released)
            review=dict(id=key,text_for_review="hello account",text_redacted="hello account",redaction_status="verified",reviewer_id="TEST_REDACTOR")
            write_csv(packet/"redaction-review.csv",REDACTION_FIELDS,[review])
            self.assertEqual(release_for_team(packet,origins,released),1)
            for who in ("a","b"):
                text=(released/f"annotator-{who}.csv").read_text()
                self.assertNotIn("HIDDEN",text);self.assertNotIn("ORIGINAL",text)
            a=root/"response-a.csv";b=root/"response-b.csv"
            response=dict(id=key,text_redacted="hello account",category="legitimate",language="en",financial_scope="true")
            write_csv(a,ANNOTATION_FIELDS,[response]);write_csv(b,ANNOTATION_FIELDS,[dict(response,language="taglish")])
            out=root/"adjudication"
            self.assertEqual(prepare_adjudication(released,a,b,out,"TEST_A","TEST_B"),1)
            queue=read_rows((out/"adjudication.csv").read_bytes(),ADJUDICATION_FIELDS)
            self.assertEqual(queue[0]["review_reasons"],"language")
            self.assertEqual(queue[0]["final_category"],"")
            with self.assertRaisesRegex(ValueError,"Incomplete"): validate_adjudication(out,root/"checked")
            queue[0].update(final_category="legitimate",final_language="en",final_financial_scope="true",adjudicator_id="TEST_C",reason="Synthetic fixture only")
            write_csv(out/"adjudication.csv",ADJUDICATION_FIELDS,queue)
            self.assertEqual(validate_adjudication(out,root/"checked"),1)
            # Even matching edits by BOTH raters cannot replace the released text.
            response["text_redacted"]="changed text"
            write_csv(a,ANNOTATION_FIELDS,[response]);write_csv(b,ANNOTATION_FIELDS,[response])
            with self.assertRaisesRegex(ValueError,"frozen release"): prepare_adjudication(released,a,b,root/"bad","TEST_A","TEST_B")
            self.assertFalse((root/"bad").exists())

    def test_no_private_output_in_public_docs(self):
        with self.assertRaises(ValueError):
            release_for_team(Path("unused"),Path("docs/origin.csv"),Path("docs/release"))


if __name__ == "__main__": unittest.main()
