"""Private audit and coordinator queues. Never assigns consent, labels or eligibility."""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile
from difflib import SequenceMatcher

from .audit_package import REQUIRED
from .data import template_groups
from .preprocessing import normalize
from .review_packets import private_output, write_csv, ANNOTATION_FIELDS, REDACTION_FIELDS
from .source_matching import SOURCES, indexes, match, parse_member

ORIGIN_FIELDS = ("id", "candidate_sources", "confirmed_source_ref", "permitted_use_status",
                 "permitted_use_reference", "study_role", "consent_verified",
                 "annotation_access_status", "annotation_access_reference", "prior_use_status",
                 "prior_use_reference", "reviewer_id", "note")
PATTERNS = {
    "email": r"[\w.+-]+@[\w.-]+\.[a-z]{2,}",
    "long_digit_or_phone": r"\d(?:[ ()+.-]*\d){6,}",
    "url": r"https?://|www\.",
    "name_salutation": r"\b(?:hi|dear|hello|mr|ms|mrs)\.?\s+[A-Z][a-z]+",
    "obfuscated_link": r"hxxps?[:\[]|\[dot\]|\(dot\)|\[\.\]",
    "short_code_context": r"\b(?:otp|pin|code)\b[^\n]{0,30}\d{4,6}\b",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_rows(data, fields=None):
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
        raise ValueError("Missing or duplicate headers; contents withheld")
    if fields is not None and set(reader.fieldnames) != set(fields):
        raise ValueError("Unexpected CSV schema; contents withheld")
    rows = list(reader)
    if not rows or any(None in r or any(v is None for v in r.values()) for r in rows):
        raise ValueError("Empty or malformed CSV; contents withheld")
    return rows


def partition(rows, key):
    result = defaultdict(list)
    for i, row in enumerate(rows):
        result[key(row)].append(i)
    return list(result.values())


def group_stats(rows, groups):
    return dict(groups=len(groups), duplicate_groups=sum(len(g) > 1 for g in groups),
        excess_rows=sum(len(g) - 1 for g in groups),
        conflicting_label_groups=sum(len({rows[i]["label"] for i in g}) > 1 for g in groups),
        cross_source_groups=sum(len({rows[i]["source"] for i in g}) > 1 for g in groups))


def analyze(rows):
    assignments = template_groups([dict(text_redacted=r["message_text"]) for r in rows])
    templates = defaultdict(list)
    for i, group in enumerate(assignments):
        templates[group].append(i)
    exact = partition(rows, lambda r: r["message_text"])
    normalized = partition(rows, lambda r: normalize(r["message_text"]))
    flags = [{name: bool(re.search(pattern, row["message_text"], 0 if name == "name_salutation" else re.I))
              for name, pattern in PATTERNS.items()} for row in rows]
    return dict(rows=len(rows), duplicate_ids=len(rows) - len({r["id"] for r in rows}),
        missing={key: sum(not r[key].strip() for r in rows) for key in sorted(REQUIRED)},
        missing_labels=sum(not r["label"].strip() for r in rows),
        invalid_labels=sum(r["label"] not in {"ham", "smishing"} for r in rows),
        inherited_labels={label:sum(r["label"] == label for r in rows) for label in ("ham", "smishing")},
        exact=group_stats(rows, exact), normalized=group_stats(rows, normalized),
        templates=group_stats(rows, list(templates.values())),
        potential_identifiers={key: sum(f[key] for f in flags) for key in PATTERNS},
        any_identifier_candidate=sum(any(f.values()) for f in flags)), assignments, flags, templates


def pair_overlap(left, right):
    """Direct cross-corpus edges, not a claim that disjoint records are unseen."""
    exact = {r["message_text"] for r in left}
    normalized = {normalize(text) for text in exact}
    matches = []
    for row in right:
        text = normalize(row["message_text"])
        found = text in normalized
        if not found:
            for other in normalized:
                if 2 * min(len(text), len(other)) / max(1, len(text) + len(other)) < .85: continue
                matcher = SequenceMatcher(None, text, other, autojunk=False)
                if matcher.quick_ratio() >= .85 and matcher.ratio() >= .85:
                    found = True
                    break
        matches.append(found)
    return dict(left_rows=len(left), right_rows=len(right),
        exact_right_rows=sum(r["message_text"] in exact for r in right),
        normalized_right_rows=sum(normalize(r["message_text"]) in normalized for r in right),
        direct_template_match_right_rows=sum(matches),
        method="Direct cross-corpus sg-ascii-v1/SequenceMatcher >=0.85; no unseen-status inference")


def run(packet, source, snapshots, output, private_archive=None, exposed_archive=None):
    private_output(packet); private_output(output)
    if output.exists():
        raise ValueError("Use a new output directory; prior work will not be overwritten")
    source_bytes = source.read_bytes()
    rows = read_rows(source_bytes, REQUIRED)
    mapping_path = packet / "coordinator/mapping.json"
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    manifest = json.loads((packet / "coordinator/manifest.json").read_text(encoding="utf-8"))
    originals = {item["original"]["id"]: item for item in mapping}
    if (manifest["input_sha256"] != sha(source_bytes) or len(originals) != len(rows)
            or len({r["anonymous_id"] for r in mapping}) != len(rows)
            or any(r != originals.get(r["id"], {}).get("original") for r in rows)):
        raise ValueError("Source and existing coordinator mapping differ; do not regenerate identities")
    print("Auditing preserved primary records and template groups; no message contents logged.", flush=True)
    primary, groups, flags, templates = analyze(rows)
    expected = {item["anonymous_id"] for item in mapping}
    review = read_rows((packet / "redaction-review.csv").read_bytes(), REDACTION_FIELDS)
    if len(review) != len(expected) or {r["id"] for r in review} != expected:
        raise ValueError("Review cohort differs from existing mapping")
    packet_stats = dict(redaction_status=dict(Counter(r["redaction_status"] for r in review)),
                        redaction_reviewer_present=sum(bool(r["reviewer_id"].strip()) for r in review))
    for who in ("a", "b"):
        pending = read_rows((packet / f"annotator-{who}-pending.csv").read_bytes(), ANNOTATION_FIELDS)
        if len(pending) != len(expected) or {r["id"] for r in pending} != expected:
            raise ValueError("Pending annotation cohort mismatch")
        packet_stats[who] = dict(rows=len(pending), messages_present=sum(bool(r["text_redacted"]) for r in pending),
                                 categories_present=sum(bool(r["category"]) for r in pending))
    indices, snapshot_hashes = {}, {}
    for name, spec in SOURCES.items():
        with zipfile.ZipFile(snapshots / f"{name}.zip") as archive:
            data = archive.read(spec["member"])
        if sha(data) != spec["sha256"]:
            raise ValueError("Source snapshot changed; review version before matching")
        indices[name] = indexes(parse_member(data, spec["member"]))
        snapshot_hashes[name] = sha(data)
    hits = [{name: result for name, index in indices.items() if (result := match(row["message_text"], index))}
            for row in rows]
    old_hits = {r["id"]: r["matches"] for r in json.loads((packet / "coordinator/source-matches.json").read_text(encoding="utf-8"))}
    matches_unchanged = all(old_hits.get(originals[row["id"]]["anonymous_id"]) == hit for row, hit in zip(rows, hits))
    source_counts = dict(rows_with_candidate_match=sum(bool(h) for h in hits),
                         multiple_candidate_sources=sum(len(h) > 1 for h in hits),
                         matches_equal_prior_ledger=matches_unchanged,
                         candidates={name: dict(Counter(h[name]["kind"] for h in hits if name in h)) for name in SOURCES})
    uci = {i for i, r in enumerate(rows) if "uci sms spam" in r["source"].lower()}
    outside = {i for i, r in enumerate(rows) if r["claimed_institution"] == "NCAP/MMDA"}
    personal_social = {i for i, r in enumerate(rows) if r["source"] in {"Personal (received)", "Facebook", "Reddit r/ScammersPH"}}
    conflicts = {i for group in templates.values() if len({rows[j]["label"] for j in group}) > 1 for i in group}
    scenarios = {}
    for name, excluded in [("without_uci", uci), ("without_uci_explicit_other", uci | outside),
                            ("also_hold_personal_social", uci | outside | personal_social),
                            ("also_hold_mixed_label_templates", uci | outside | personal_social | conflicts)]:
        kept = set(range(len(rows))) - excluded
        scenarios[name] = dict(excluded=len(excluded), remaining_candidates=len(kept),
            exact_unique=len({rows[i]["message_text"] for i in kept}), template_groups=len({groups[i] for i in kept}),
            inherited_labels=dict(Counter(rows[i]["label"] for i in kept)), established_eligible_records=0)
    output.mkdir(parents=True)
    queue = []
    origins = []
    for i, row in enumerate(rows):
        anonymous = originals[row["id"]]["anonymous_id"]
        queue.append(dict(id=anonymous, template_group=f"GROUP_{groups[i]}",
            inherited_label_conflict=i in conflicts, supplementary_uci=i in uci,
            explicit_other_sector=i in outside, personal_social_hold=i in personal_social,
            identifier_candidates=";".join(key for key, flag in flags[i].items() if flag),
            candidate_sources=";".join(hits[i]), status="human_review_pending"))
        origins.append(dict(id=anonymous, candidate_sources=";".join(hits[i]),
            permitted_use_status="pending", annotation_access_status="pending", prior_use_status="unconfirmed"))
    write_csv(output / "coordinator-check-queue.csv", tuple(queue[0]), queue)
    write_csv(output / "origin-review.csv", ORIGIN_FIELDS, origins)
    # These IDs link to existing restricted redaction/mapping files, never to a public report.
    report = dict(schema_version=1, source_sha256=sha(source_bytes), mapping_sha256=sha(mapping_path.read_bytes()),
        primary=primary, existing_packets=packet_stats, source_snapshot_hashes=snapshot_hashes,
        source_overlap=source_counts, exclusion_scenarios=scenarios,
        established_eligible_records=0, eligibility_note="This audit clears no records; use the separately reviewed import report for actual eligibility. Zero cleared here is not proof all rows are unusable.",
        grouping="sg-ascii-v1 plus SequenceMatcher >=0.85 connected components; review candidates, not confirmed campaign identity",
        identifier_patterns=PATTERNS, review_note="Patterns overlap; candidates only. Names/obfuscation may be missed. No automatic redaction or review attestation.")
    extras = []
    if private_archive:
        with zipfile.ZipFile(private_archive) as archive:
            originals_in_archive = [n for n in archive.namelist() if n.endswith("/smishguard_dataset.csv")]
            if len(originals_in_archive) != 1 or sha(archive.read(originals_in_archive[0])) != sha(source_bytes):
                raise ValueError("Private handoff primary differs from preserved source")
            names = [n for n in archive.namelist() if n.endswith("/supplementary_everyday_ham.csv")]
            if len(names) != 1:
                raise ValueError("Expected one supplementary handoff CSV")
            data = archive.read(names[0])
        extras.append(("supplementary_everyday_ham", data, read_rows(data, REQUIRED)))
    if exposed_archive:
        with zipfile.ZipFile(exposed_archive) as archive:
            names = [n for n in archive.namelist() if n.endswith("/fresh_test_messages.csv")]
            if len(names) != 1:
                raise ValueError("Expected one previously exposed probe CSV")
            data = archive.read(names[0])
        probes = read_rows(data, {"group", "label", "message"})
        extra_rows = [dict.fromkeys(REQUIRED, "") for _ in probes]
        for i, (dest, probe) in enumerate(zip(extra_rows, probes)):
            dest.update(id=f"EXPOSED_{i}", message_text=probe["message"], label=probe["label"], source="exposed_handoff_probes")
        extras.append(("previously_exposed_probes", data, extra_rows))
    report["separate_handoffs"] = {}
    for name, data, extra in extras:
        print(f"Auditing separate {name}; not adding it to primary training or annotation packets.", flush=True)
        stats, _, _, _ = analyze(extra)
        combined_groups = template_groups([dict(text_redacted=r["message_text"]) for r in rows + extra])
        primary_groups = set(combined_groups[:len(rows)])
        exact_primary = {r["message_text"] for r in rows}
        norm_primary = {normalize(r["message_text"]) for r in rows}
        stats.update(sha256=sha(data), exact_overlap_primary=sum(r["message_text"] in exact_primary for r in extra),
            normalized_overlap_primary=sum(normalize(r["message_text"]) in norm_primary for r in extra),
            combined_template_overlap_primary=sum(g in primary_groups for g in combined_groups[len(rows):]),
            established_eligible_records=0, independently_unseen=False)
        report["separate_handoffs"][name] = stats
    if len(extras) == 2:
        report["supplement_to_exposed_probes"] = pair_overlap(extras[0][2], extras[1][2])
    (output / "aggregate-audit.json").write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
    print("Private queues and aggregate audit saved. No records newly cleared and no models trained.")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, default=Path("research/data/review-v1"))
    parser.add_argument("--source", type=Path, default=Path("research/data/supplied-original/smishguard_dataset.csv"))
    parser.add_argument("--snapshots", type=Path, default=Path("research/data/source-evidence-pinned"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--private-archive", type=Path)
    parser.add_argument("--exposed-archive", type=Path)
    args = parser.parse_args()
    run(args.packet, args.source, args.snapshots, args.output, args.private_archive, args.exposed_archive)


if __name__ == "__main__":
    main()
