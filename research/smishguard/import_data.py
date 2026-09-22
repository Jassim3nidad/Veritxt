"""Import reviewed records; quarantine metadata only, never silently relabel."""
import argparse
import csv
import hashlib
from collections import Counter
from pathlib import Path
import numpy as np
from sklearn.metrics import cohen_kappa_score, confusion_matrix
from .intake import read_csv, validate_record, eligible_category, CATEGORIES, APPROVED_FIELDS, TOKEN
from .train import write_json


def agreement(rows):
    pairs = [(r["annotator_1"], r["annotator_2"]) for r in rows if r["annotator_1"] and r["annotator_2"]]
    a, b = zip(*pairs) if pairs else ([], [])
    value = float(cohen_kappa_score(a, b, labels=list(CATEGORIES))) if pairs and len(set(a) | set(b)) > 1 else None
    return dict(paired_records=len(pairs), missing_pairs=len(rows)-len(pairs),
        observed_agreement=sum(x == y for x, y in pairs)/len(pairs) if pairs else None,
        cohen_kappa=value if value is not None and np.isfinite(value) else None,
        category_order=list(CATEGORIES), confusion=confusion_matrix(a,b,labels=list(CATEGORIES)).tolist() if pairs else None,
        scope="Original independent labels before filtering/adjudication; uncertain included; no model accuracy")


def import_records(source, output, approval_reference, study_role="primary"):
    if not TOKEN.fullmatch(approval_reference):
        raise ValueError("Supply a controlled intake review reference token; this is not project authorization or ethics clearance")
    rows = read_csv(source)
    approved, held = [], []
    for number, row in enumerate(rows, start=2):
        try:
            validate_record(row)
            category, reason = eligible_category(row, study_role)
        except ValueError as error:
            raise ValueError(f"CSV row {number}: {error}") from None
        if reason:
            held.append(dict(id=row["id"], reason=reason))
        else:
            approved.append(dict(row, label="1" if category == "financial_phishing" else "0", approval_reference=approval_reference))
    output.mkdir(parents=True, exist_ok=False)
    with (output/"approved.csv").open("w",encoding="utf-8",newline="") as file:
        writer=csv.DictWriter(file,fieldnames=APPROVED_FIELDS)
        writer.writeheader(); writer.writerows(approved)
    write_json(output/"import-report.json", dict(input_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        review_reference=approval_reference, study_role=study_role, input_records=len(rows), eligible_records=len(approved),
        held_records=held, held_counts=dict(Counter(r["reason"] for r in held)), agreement=agreement(rows),
        note="Operation-specific data review only; project authorization is recorded separately. Legacy approval_reference column stores this intake review reference, not ethics clearance. Held rows have eligibility not yet verified for this operation, or a specific documented exclusion; no held text copied"))
    return len(approved), len(held)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("source",type=Path); p.add_argument("output",type=Path)
    p.add_argument("--review-reference", "--approval-reference", dest="review_reference", required=True,
                   help="Intake review record; legacy option retained, not an ethics/project approval gate")
    p.add_argument("--study-role", choices=["primary", "supplementary"], default="primary")
    args=p.parse_args()
    accepted,held=import_records(args.source,args.output,args.review_reference,args.study_role)
    print(f"Imported {accepted} eligible records; held {held}. No model trained and no approval inferred.")


if __name__ == "__main__": main()
