"""Private, blinded review packets. Never assigns labels or declares redaction complete."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import random
import secrets
import uuid
from .intake import IDENTIFIER, TOKEN

ANNOTATION_FIELDS = ("id", "text_redacted", "category", "language", "financial_scope", "note")
REDACTION_FIELDS = ("id", "text_for_review", "text_redacted", "redaction_status", "reviewer_id", "note")


def write_csv(path, fields, rows):
    # Prevent spreadsheet formula execution; never use this escaped display copy for fitting.
    def cell(value):
        value = str(value)
        return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k:cell(r.get(k, "")) for k in fields} for r in rows)


def private_output(path):
    private = Path("research/data").resolve()
    if not path.resolve().is_relative_to(private):
        raise ValueError("Review packets contain private data; output must be inside ignored research/data")


def prepare(source, output):
    private_output(output)
    with source.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows or any(not r.get("id") or not r.get("message_text") for r in rows):
        raise ValueError("Expected supplied CSV with unique id and message_text")
    if len({r['id'] for r in rows}) != len(rows):
        raise ValueError("Duplicate input IDs")
    output.mkdir(parents=True, exist_ok=False)
    coordinator = output / "coordinator"; coordinator.mkdir()
    mapped = [dict(anonymous_id="SG_" + uuid.uuid4().hex, original=r) for r in rows]
    # Full mapping stays coordinator-only; annotators never receive original IDs or source labels.
    (coordinator / "mapping.json").write_text(json.dumps(mapped, ensure_ascii=False), encoding="utf-8")
    seed_a, seed_b = secrets.randbits(64), secrets.randbits(64)
    (coordinator / "manifest.json").write_text(json.dumps(dict(
        input_sha256=hashlib.sha256(source.read_bytes()).hexdigest(), rows=len(rows),
        seed_a=seed_a, seed_b=seed_b, status="awaiting_human_redaction", labels_assigned=0)), encoding="utf-8")
    queue = [dict(id=r['anonymous_id'], text_for_review=r['original']['message_text'],
                  text_redacted="", redaction_status="pending", reviewer_id="", note="") for r in mapped]
    random.Random(seed_a).shuffle(queue)
    write_csv(output / "redaction-review.csv", REDACTION_FIELDS, queue)
    # Safe ID-only preparation sheets; release() supplies text only after review.
    for who, seed in [('a', seed_a), ('b', seed_b)]:
        order = [dict(id=r['anonymous_id']) for r in mapped]
        random.Random(seed).shuffle(order)
        write_csv(output / f"annotator-{who}-pending.csv", ANNOTATION_FIELDS, order)
    (output / "README.txt").write_text(
        "PRIVATE: do not commit or publish this directory. Coordinator mapping and redaction queue are restricted.\n"
        "Pending annotation sheets contain anonymous IDs but no message text or labels; do not annotate them.\n"
        "A human reviewer must fill text_redacted, redaction_status=verified and reviewer_id, then run release.\n"
        "Annotators receive only their released file and labeling guide, never source/old labels/model outputs.\n"
        "Spreadsheet-dangerous display cells are prefixed with an apostrophe. Original bytes remain in mapping.json.\n"
        "No dates, independent labels, consent or permitted-use decisions were inferred.\n", encoding="utf-8")
    return len(rows)


def release(packet, output):
    private_output(packet); private_output(output)
    mapping = json.loads((packet / "coordinator/mapping.json").read_text(encoding="utf-8"))
    manifest = json.loads((packet / "coordinator/manifest.json").read_text(encoding="utf-8"))
    expected = {r['anonymous_id'] for r in mapping}
    with (packet / "redaction-review.csv").open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != list(REDACTION_FIELDS): raise ValueError("Unexpected review schema")
        rows = list(reader)
    if len(rows) != len(expected) or {r['id'] for r in rows} != expected:
        raise ValueError("Review IDs must match the coordinator ledger exactly once")
    reviewed = []
    for r in rows:
        if r['redaction_status'] not in {'pending', 'verified', 'excluded'}:
            raise ValueError("Unknown redaction status")
        if r['redaction_status'] != 'verified': continue
        text = r['text_redacted']
        if not TOKEN.fullmatch(r['reviewer_id']) or not text.strip() or len(text) > 10000 or IDENTIFIER.search(text):
            raise ValueError("Verified row needs reviewer and reviewed text without residual URL/email/long identifiers")
        if text.lstrip().startswith(("=", "+", "-", "@", "'")):
            raise ValueError("Review spreadsheet escaping before releasing text; no formulas or escape prefixes")
        reviewed.append(dict(id=r['id'], text_redacted=text))
    if not reviewed: raise ValueError("No human-verified redactions; no annotation text released")
    output.mkdir(parents=True, exist_ok=False)
    for who in ('a', 'b'):
        order = list(reviewed); random.Random(manifest[f'seed_{who}']).shuffle(order)
        write_csv(output / f"annotator-{who}.csv", ANNOTATION_FIELDS, order)
    (output / "release.json").write_text(json.dumps(dict(rows=len(reviewed), withheld=len(rows)-len(reviewed),
        redaction_review_sha256=hashlib.sha256((packet/'redaction-review.csv').read_bytes()).hexdigest(),
        scope="Blinded annotation preparation only; not data-use clearance or training eligibility")), encoding="utf-8")
    return len(reviewed)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=['prepare', 'release'])
    parser.add_argument("source", type=Path); parser.add_argument("output", type=Path)
    args = parser.parse_args()
    count = (prepare if args.operation == 'prepare' else release)(args.source, args.output)
    print(f"Prepared {count} private review records; no labels or research approval inferred.")


if __name__ == '__main__': main()
