"""Gate blinded release and prepare adjudication from frozen independent responses."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil

from .annotation_results import read_annotations, summarize
from .intake import CATEGORIES, TOKEN
from .prepare_team_data import ORIGIN_FIELDS, read_rows
from .review_packets import private_output, release, write_csv, ANNOTATION_FIELDS

ADJUDICATION_FIELDS = ("id", "text_redacted", "a_category", "a_language", "a_financial_scope",
    "b_category", "b_language", "b_financial_scope", "review_reasons", "final_category",
    "final_language", "final_financial_scope", "adjudicator_id", "reason")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def release_for_team(packet, origins, output):
    private_output(origins); private_output(output)
    rows = read_rows(origins.read_bytes(), ORIGIN_FIELDS)
    mapping = json.loads((packet / "coordinator/mapping.json").read_text(encoding="utf-8"))
    expected = {r["anonymous_id"] for r in mapping}
    if len(rows) != len(expected) or {r["id"] for r in rows} != expected:
        raise ValueError("Access review must cover each existing packet ID once")
    allowed = set()
    for row in rows:
        status = row["annotation_access_status"]
        if status not in {"pending", "documented", "not_permitted"}:
            raise ValueError("Invalid annotation-access status")
        if status == "documented":
            if not all(TOKEN.fullmatch(row[key]) for key in ("annotation_access_reference", "reviewer_id")):
                raise ValueError("Documented annotation access requires evidence and reviewer references")
            allowed.add(row["id"])
    if not allowed:
        raise ValueError("No documented annotation access; no messages released")
    count = release(packet, output, accessible_ids=allowed)
    record = json.loads((output / "release.json").read_text(encoding="utf-8"))
    record["access_review_sha256"] = digest(origins)
    (output / "release.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    return count


def prepare_adjudication(released, a, b, output, annotator_a, annotator_b):
    for path in (released, a, b, output):
        private_output(path)
    if not all(TOKEN.fullmatch(value) for value in (annotator_a, annotator_b)) or annotator_a == annotator_b:
        raise ValueError("Use distinct opaque annotator IDs")
    manifest = json.loads((released / "release.json").read_text(encoding="utf-8"))
    if not manifest.get("annotation_access_filtered") or not manifest.get("access_review_sha256"):
        raise ValueError("Use the access-reviewed team release")
    originals = []
    for who in ("a", "b"):
        path = released / f"annotator-{who}.csv"
        if digest(path) != manifest["sheets_sha256"][who]:
            raise ValueError("Released blank sheet changed; preserve original and submit a separate response copy")
        originals.append({r["id"]: r["text_redacted"] for r in read_rows(path.read_bytes(), ANNOTATION_FIELDS)})
    if originals[0] != originals[1]:
        raise ValueError("Released text differs between annotators")
    sheets = [read_annotations(path) for path in (a, b)]
    for sheet in sheets:
        if {key: row["text_redacted"] for key, row in sheet.items()} != originals[0]:
            raise ValueError("Response cohort or text differs from frozen release")
    aggregate = summarize([a, b])
    queue = []
    for key in originals[0]:
        x, y = (sheet[key] for sheet in sheets)
        reasons = [field for field in ("category", "language", "financial_scope") if x[field] != y[field]]
        if x["category"] == "uncertain" or y["category"] == "uncertain": reasons.append("uncertain_category")
        if x["financial_scope"] == "uncertain" or y["financial_scope"] == "uncertain": reasons.append("uncertain_scope")
        queue.append(dict(id=key, text_redacted=x["text_redacted"],
            a_category=x["category"], a_language=x["language"], a_financial_scope=x["financial_scope"],
            b_category=y["category"], b_language=y["language"], b_financial_scope=y["financial_scope"],
            review_reasons=";".join(reasons) or "confirm_agreement"))
    output.mkdir(parents=True, exist_ok=False)
    frozen = output / "frozen-responses"; frozen.mkdir()
    for who, path in (("a", a), ("b", b)):
        shutil.copyfile(path, frozen / f"annotator-{who}.csv")
    write_csv(output / "adjudication.csv", ADJUDICATION_FIELDS, queue)
    (output / "agreement-before-adjudication.json").write_text(json.dumps(aggregate, indent=2), encoding="utf-8")
    (output / "response-freeze.json").write_text(json.dumps(dict(
        release_sha256=digest(released / "release.json"), annotator_a=annotator_a, annotator_b=annotator_b,
        response_sha256={who:digest(frozen / f"annotator-{who}.csv") for who in ("a", "b")},
        independence_status="requires separate human attestation; distinct files/IDs do not prove independence"), indent=2), encoding="utf-8")
    return len(queue)


def validate_adjudication(directory, output):
    private_output(directory); private_output(output)
    freeze = json.loads((directory / "response-freeze.json").read_text(encoding="utf-8"))
    sheets = []
    for who in ("a", "b"):
        path = directory / f"frozen-responses/annotator-{who}.csv"
        if digest(path) != freeze["response_sha256"][who]:
            raise ValueError("Frozen independent response changed")
        sheets.append(read_annotations(path))
    rows = read_rows((directory / "adjudication.csv").read_bytes(), ADJUDICATION_FIELDS)
    if len(rows) != len(sheets[0]) or {r["id"] for r in rows} != set(sheets[0]):
        raise ValueError("Adjudication must cover the complete cohort exactly once")
    for row in rows:
        for who, sheet in zip(("a", "b"), sheets):
            old = sheet[row["id"]]
            if row["text_redacted"] != old["text_redacted"] or any(row[f"{who}_{field}"] != old[field]
                for field in ("category", "language", "financial_scope")):
                raise ValueError("Adjudication changed original independent responses")
        if (row["final_category"] not in CATEGORIES or row["final_language"] not in {"en", "fil", "taglish"}
                or row["final_financial_scope"] not in {"true", "false", "uncertain"}
                or not TOKEN.fullmatch(row["adjudicator_id"]) or not row["reason"].strip()
                or row["adjudicator_id"] in {freeze["annotator_a"], freeze["annotator_b"]}):
            raise ValueError("Incomplete resolution or adjudicator is not distinct from A/B")
    output.mkdir(parents=True, exist_ok=False)
    write_csv(output / "adjudication-core.csv", ("id", "final_category", "adjudicator_id", "reason"), rows)
    stats = summarize([directory / f"frozen-responses/annotator-{who}.csv" for who in ("a", "b")],
                      output / "adjudication-core.csv")
    stats["unresolved_scope_records"] = sum(r["final_financial_scope"] == "uncertain" for r in rows)
    stats["training_eligible_records"] = None
    stats["next_step"] = "Coordinator merges reviewed source/consent/redaction/scope and original A/B labels into intake, then runs import_data; this is not training clearance"
    (output / "resolution-summary.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    return len(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    p = sub.add_parser("release")
    p.add_argument("packet", type=Path); p.add_argument("origins", type=Path); p.add_argument("output", type=Path)
    p = sub.add_parser("adjudicate")
    for key in ("released", "a", "b", "output"): p.add_argument(key, type=Path)
    p.add_argument("--annotator-a", required=True); p.add_argument("--annotator-b", required=True)
    p = sub.add_parser("validate")
    p.add_argument("directory", type=Path); p.add_argument("output", type=Path)
    args = vars(parser.parse_args()); operation = args.pop("operation")
    count = {"release":release_for_team, "adjudicate":prepare_adjudication, "validate":validate_adjudication}[operation](**args)
    print(f"Prepared or checked {count} private records. No consent, independence or training eligibility inferred.")


if __name__ == "__main__": main()
