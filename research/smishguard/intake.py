"""Strict reviewed intake contract. No automatic labeling, approval or PII redaction."""
import csv
import re
from .preprocessing import normalize

CATEGORIES = ("financial_phishing", "legitimate", "other_spam_scam", "uncertain")
SOURCES = {"participant_donation", "team_donation", "institutional_publication",
           "aggregator", "public_archive", "social_post", "external_collection"}
URL_FIELDS = ("url_count", "url_max_host_length", "url_digit_fraction", "url_max_depth")
FIELDS = ("id", "text_redacted", "language", "source_type", "source_ref", "consent_verified",
          "permitted_use_status", "permitted_use_reference", "study_role",
          "redaction_verified", "financial_scope", "received_at", "annotator_1_id", "annotator_1", "annotator_2_id", "annotator_2", "adjudication_status", "adjudicator_id", "adjudicated_category", "adjudication_note", "template_group", *URL_FIELDS)
APPROVED_FIELDS = (*FIELDS, "label", "approval_reference")
TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}\Z")
# Conservative blockers only, never a claim of complete de-identification.
IDENTIFIER = re.compile(r"https?://|www\.|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|\d(?:[ ()+.-]*\d){6,}", re.I)


def read_csv(path, approved=False):
    expected = APPROVED_FIELDS if approved else FIELDS
    with open(path, encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None or len(set(reader.fieldnames)) != len(reader.fieldnames) or set(reader.fieldnames) != set(expected):
            raise ValueError("CSV headers must match the documented template exactly")
        rows = list(reader)
    if not rows:
        raise ValueError("CSV contains no records; blank templates are not datasets")
    if any(None in r or any(v is None for v in r.values()) for r in rows):
        raise ValueError("Malformed CSV row; quote embedded commas/newlines")
    if len({r["id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate record IDs")
    return rows


def validate_record(r):
    from .data import timestamp
    import math
    for key in ("id", "source_ref"):
        if not TOKEN.fullmatch(r[key]):
            raise ValueError("Use opaque nonidentifying tokens for record/source references")
    if r["source_type"] not in SOURCES:
        raise ValueError("Unknown source type; classify its origin accurately (synthetic fixtures stay separate)")
    if r["permitted_use_status"] not in {"pending", "documented", "not_permitted"}:
        raise ValueError("Permitted-use status must be pending, documented or not_permitted")
    if r["permitted_use_reference"] and not TOKEN.fullmatch(r["permitted_use_reference"]):
        raise ValueError("Use an opaque permitted-use evidence reference")
    if r["permitted_use_status"] == "documented" and not r["permitted_use_reference"]:
        raise ValueError("Documented permitted use requires its evidence reference")
    if r["study_role"] not in {"primary", "supplementary", "undecided"}:
        raise ValueError("Study role must be primary, supplementary or undecided")
    if r["language"] not in {"fil", "en", "taglish"}:
        raise ValueError("Unsupported language code")
    for key in ("consent_verified", "redaction_verified"):
        if r[key] not in {"true", "false"}:
            raise ValueError("Review flags must be explicitly true or false")
    if r["financial_scope"] not in {"true", "false", ""}:
        raise ValueError("Financial scope must be true, false, or blank pending review")
    if not r["text_redacted"].strip() or len(r["text_redacted"]) > 10000 or not normalize(r["text_redacted"]):
        raise ValueError("Empty, unsupported or overlong redacted text")
    if IDENTIFIER.search(r["text_redacted"]):
        raise ValueError("Possible unredacted URL/email/identifier; return to human review")
    if r["received_at"]:
        timestamp(r["received_at"])
    for key in ("annotator_1_id", "annotator_2_id", "adjudicator_id", "template_group"):
        if r[key] and not TOKEN.fullmatch(r[key]):
            raise ValueError("Annotator/group IDs must be opaque tokens")
    for number in (1, 2):
        if r[f"annotator_{number}"] not in {*CATEGORIES, ""}:
            raise ValueError("Unknown independent annotation category")
        if bool(r[f"annotator_{number}"]) != bool(r[f"annotator_{number}_id"]):
            raise ValueError("Each independent label requires its annotator ID")
    if r["annotator_1_id"] and r["annotator_1_id"] == r["annotator_2_id"]:
        raise ValueError("Independent annotations require distinct annotators")
    if r["adjudication_status"] not in {"pending", "agreed", "adjudicated"}:
        raise ValueError("Unknown adjudication status")
    if r["adjudicated_category"] not in {*CATEGORIES, ""}:
        raise ValueError("Unknown adjudicated category")
    if IDENTIFIER.search(r["adjudication_note"]) or len(r["adjudication_note"]) > 500:
        raise ValueError("Adjudication note must be short and nonidentifying")
    facts = [r[key] for key in URL_FIELDS]
    if any(facts):
        if not all(facts):
            raise ValueError("Provide all four URL facts or leave all blank")
        values = [float(v) for v in facts]
        if not all(math.isfinite(v) and v >= 0 for v in values) or values[2] > 1 or values[1] > 253:
            raise ValueError("Invalid URL facts")
        if any(not values[i].is_integer() for i in (0, 1, 3)) or (values[0] == 0 and any(values[1:])):
            raise ValueError("Inconsistent URL counts/lengths/depth")


def resolved_category(r):
    a, b = r["annotator_1"], r["annotator_2"]
    if r["adjudication_status"] == "pending":
        if r["adjudicated_category"]:
            raise ValueError("Pending cases cannot carry a final category")
        return None
    if not a or not b:
        raise ValueError("Resolution requires both independent annotations")
    if r["adjudication_status"] == "agreed":
        if a != b or a == "uncertain" or r["adjudicated_category"] != a:
            raise ValueError("Agreed status requires matching certain annotations and final category")
    elif not r["adjudicator_id"] or not r["adjudication_note"].strip() or not r["adjudicated_category"]:
        raise ValueError("Adjudication requires reviewer, final category and nonidentifying rationale")
    return r["adjudicated_category"]


def eligible_category(r, study_role="primary"):
    if study_role not in {"primary", "supplementary"}:
        raise ValueError("Unsupported import study role")
    category = resolved_category(r)
    if r["permitted_use_status"] != "documented":
        return None, "permitted_use_not_documented" if r["permitted_use_status"] == "pending" else "use_not_permitted"
    if r["study_role"] != study_role:
        return None, "study_role_not_selected"
    if r["source_type"] in {"participant_donation", "team_donation"} and r["consent_verified"] != "true":
        return None, "donation_consent_not_verified"
    if r["redaction_verified"] != "true":
        return None, "redaction_not_verified"
    if category is None or category == "uncertain":
        return None, "pending_or_uncertain"
    if category == "other_spam_scam" or r["financial_scope"] != "true":
        return None, "outside_financial_binary_scope"
    return category, None
