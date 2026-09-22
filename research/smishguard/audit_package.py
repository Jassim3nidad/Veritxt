"""Local aggregate audit; never writes message examples into public reports."""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re
import shutil
import zipfile
from .data import template_groups
from .preprocessing import normalize
from .train import write_json

REQUIRED={"id","message_text","label","claimed_institution","spoofed_url","official_domain","language","attack_type","source","date_collected","notes"}


def audit(package, private, report):
    private.mkdir(parents=True,exist_ok=True)
    original=private/"original";original.mkdir(exist_ok=True)
    def preserve(path, data):
        if path.exists() and path.read_bytes()!=data:raise ValueError("Refusing to replace an existing original")
        if not path.exists():path.write_bytes(data)
    preserve(original/package.name,package.read_bytes())
    hashes={package.name:hashlib.sha256(package.read_bytes()).hexdigest()}
    with zipfile.ZipFile(package) as z:
        expected={"smishguard_dataset.csv","model_export_final.json","MODEL_INTEGRATION.md"}
        names=[n for n in z.namelist() if not n.endswith("/")]
        if len(names)!=3 or {Path(n).name for n in names}!=expected:raise ValueError("Unexpected package contents; review before extraction")
        for name in names:
            data=z.read(name);base=Path(name).name
            preserve(original/base,data);hashes[base]=hashlib.sha256(data).hexdigest()
    with (original/"smishguard_dataset.csv").open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        if set(reader.fieldnames or [])!=REQUIRED:raise ValueError("Unexpected dataset schema")
        rows=list(reader)
    if any(None in r or any(v is None for v in r.values()) for r in rows):raise ValueError("Malformed dataset CSV")
    exact=defaultdict(list);normalized=defaultdict(list)
    for i,r in enumerate(rows):
        exact[r["message_text"]].append(i);normalized[normalize(r["message_text"])].append(i)
    def duplicate_info(groups):
        groups=list(groups.values())
        return dict(unique_groups=len(groups),duplicate_groups=sum(len(g)>1 for g in groups),
            excess_rows=sum(len(g)-1 for g in groups),conflicting_groups=sum(len({rows[i]["label"] for i in g})>1 for g in groups))
    print("Computing label-blind template groups; message contents are not logged.",flush=True)
    groups=template_groups([dict(text_redacted=r["message_text"]) for r in rows])
    clusters=defaultdict(list)
    for i,g in enumerate(groups):clusters[g].append(i)
    source_label=defaultdict(Counter);language_label=defaultdict(Counter)
    for r in rows:source_label[r["source"]][r["label"]]+=1;language_label[r["language"]][r["label"]]+=1
    uci=[i for i,r in enumerate(rows) if "uci sms spam" in r["source"].lower()]
    non_uci=[i for i in range(len(rows)) if i not in set(uci)]
    explicit_other=[i for i in non_uci if rows[i]["claimed_institution"] in {"NCAP/MMDA"}]
    financial_claim=[i for i in non_uci if i not in explicit_other and rows[i]["claimed_institution"]]
    pii={"email":re.compile(r"[\w.+-]+@[\w.-]+\.[a-z]{2,}",re.I),
         "long_digit_or_phone":re.compile(r"\d(?:[ ()+.-]*\d){6,}"),
         "url":re.compile(r"https?://|www\.",re.I),
         "name_salutation":re.compile(r"\b(?:hi|dear|hello|mr|ms|mrs)\.?\s+[A-Z][a-z]+")}
    derived=private/"derived";derived.mkdir(exist_ok=True)
    for name,indices in [("external-uci.csv",uci),("non-uci-unverified.csv",non_uci)]:
        with (derived/name).open("w",encoding="utf-8",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows[i] for i in indices)
    with (derived/"review-ledger.csv").open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=["id","template_group","external_uci","explicit_other_sector","potential_identifier","review_status"]);writer.writeheader()
        for i,r in enumerate(rows):writer.writerow(dict(id=r["id"],template_group=f"GROUP_{groups[i]}",external_uci=i in uci,explicit_other_sector=i in explicit_other,potential_identifier=any(p.search(r["message_text"]) for p in pii.values()),review_status="unverified"))
    model=json.loads((original/"model_export_final.json").read_text(encoding="utf-8"))
    result=dict(package_sha256=hashes[package.name],files_sha256=hashes,rows=len(rows),columns=list(rows[0]),
        labels=dict(Counter(r["label"] for r in rows)),languages=dict(Counter(r["language"] for r in rows)),
        missing={k:sum(not r[k].strip() for r in rows) for k in rows[0]},duplicate_ids=len(rows)-len({r["id"] for r in rows}),
        invalid_labels=sum(r["label"] not in {"ham","smishing"} for r in rows),exact_duplicates=duplicate_info(exact),normalized_duplicates=duplicate_info(normalized),
        template_groups=duplicate_info(clusters),template_method="Label-blind sg-ascii-v1 normalization, exact equality + SequenceMatcher >=0.85 connected components; heuristic, requires review",
        source_label={k:dict(v) for k,v in source_label.items()},language_label={k:dict(v) for k,v in language_label.items()},
        eligibility=dict(external_uci=len(uci),non_uci_unverified=len(non_uci),explicit_other_sector=len(explicit_other),
            financial_institution_claim_unverified=len(financial_claim),financial_claim_unique_exact=len({rows[i]["message_text"] for i in financial_claim}),
            financial_claim_template_groups=len({groups[i] for i in financial_claim}),verified_primary_rows=None,verified_primary_groups=None,
            status="eligibility not yet verified",project_authorization_record="docs/project-authorization.json",
            reason="Source-specific permitted-use documentation and record-level label/redaction review remain unresolved; project/client authorization is recorded separately"),
        pii_candidate_rows={k:sum(bool(p.search(r["message_text"])) for r in rows) for k,p in pii.items()},
        learned_vocabulary_privacy=dict(long_numeric_feature_terms=sum(bool(re.search(r"\d{7,}",word)) for word in model["vocabulary"]),
            note="Learned vocabulary can retain training tokens; numeric terms are candidates, not confirmed personal identifiers. Review before broader distribution. No weights/terms altered."),
        pii_note="Heuristics are not proof of identity or complete redaction. No examples disclosed. URLs remain unopened.",
        date_collected=dict(nonempty=sum(bool(r["date_collected"]) for r in rows),
            iso_date_only=sum(bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}",r["date_collected"])) for r in rows),
            meaning="Unverified; collection versus receipt undefined; no timezone or receipt provenance; do not use for chronology"),
        claims_status="No training scripts, CV splits, seed records, licenses/permissions, consent, or calibration report in package. Guide performance/CI/realistic-traffic claims not reproducible from these files.")
    report.parent.mkdir(parents=True,exist_ok=True);write_json(report,result)
    print(f"Audit written with aggregate counts only: {report}")
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument("package",type=Path);p.add_argument("--private-dir",type=Path,default=Path("research/data/package-audit"));p.add_argument("--report",type=Path,default=Path("docs/dataset-audit.json"));a=p.parse_args();audit(a.package,a.private_dir,a.report)


if __name__ == "__main__":main()
