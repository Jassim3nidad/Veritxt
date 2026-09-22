"""Validate private blinded responses; emit aggregate agreement without text or IDs."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
from .intake import CATEGORIES
from .review_packets import ANNOTATION_FIELDS, private_output


def read_annotations(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != list(ANNOTATION_FIELDS):
            raise ValueError("Unexpected annotation schema")
        rows = list(reader)
    if not rows or any(None in r or any(v is None for v in r.values()) for r in rows):
        raise ValueError("Empty or malformed annotation file")
    if len({r['id'] for r in rows}) != len(rows) or any(not r['id'] for r in rows):
        raise ValueError("Missing or duplicate anonymous IDs")
    if any(r['category'] not in CATEGORIES or r['language'] not in {'en','fil','taglish'}
           or r['financial_scope'] not in {'true','false','uncertain'} or not r['text_redacted'].strip() for r in rows):
        raise ValueError("Incomplete or invalid annotation fields; values withheld")
    return {r['id']: r for r in rows}


def summarize(files, adjudication=None):
    if len(files) < 2 or len({p.resolve() for p in files}) != len(files):
        raise ValueError("At least two distinct annotator files required")
    sheets = [read_annotations(p) for p in files]
    ids = sorted(sheets[0])
    if any(set(s) != set(ids) for s in sheets):
        raise ValueError("Annotator IDs differ; missing responses must be resolved")
    if any(len({s[i]['text_redacted'] for s in sheets}) != 1 for i in ids):
        raise ValueError("Annotators received different text; investigate before agreement")
    n, raters = len(ids), len(sheets)
    counts = [Counter(s[i]['category'] for s in sheets) for i in ids]
    observed = sum(sum(v*(v-1) for v in c.values())/(raters*(raters-1)) for c in counts)/n
    if raters == 2:
        marginal = [Counter(s[i]['category'] for i in ids) for s in sheets]
        expected = sum(marginal[0][c]*marginal[1][c] for c in CATEGORIES)/n**2
    else:
        pooled = sum(counts, Counter())
        expected = sum((pooled[c]/(n*raters))**2 for c in CATEGORIES)
    result = dict(records=n, annotators=raters, raw_pairwise_agreement=observed,
        unanimous_records=sum(len(c)==1 for c in counts), disagreement_records=sum(len(c)>1 for c in counts),
        method="Cohen" if raters==2 else "Fleiss", kappa=(observed-expected)/(1-expected) if expected < 1 else None,
        note="Undefined kappa is null. Complete common cohort only; independence is a human attestation, not a software finding.",
        final_adjudicated_label_counts=None)
    if adjudication:
        with adjudication.open(encoding='utf-8-sig', newline='') as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames != ['id','final_category','adjudicator_id','reason']:
                raise ValueError('Unexpected adjudication schema')
            rows = list(reader)
        if len(rows)!=n or {r.get('id') for r in rows}!=set(ids):
            raise ValueError('Adjudication must cover each anonymous ID exactly once')
        if any(None in r or any(v is None for v in r.values()) or r['final_category'] not in CATEGORIES
               or not r['adjudicator_id'].strip() or not r['reason'].strip() for r in rows):
            raise ValueError('Incomplete adjudication; values withheld')
        result['final_adjudicated_label_counts'] = dict(Counter(r['final_category'] for r in rows))
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('files', type=Path, nargs='+')
    parser.add_argument('--adjudication', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args=parser.parse_args()
    private_output(args.output)
    result=summarize(args.files,args.adjudication)
    with args.output.open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2,allow_nan=False)
    print('Annotation files validated; aggregate report saved privately. No text logged.')


if __name__=='__main__': main()
