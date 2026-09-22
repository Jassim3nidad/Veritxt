"""Future supplied-model evaluation on reviewed independent inputs; never same-data scoring."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from datetime import datetime, timezone
import csv
import unicodedata
import numpy as np
from .convert_supplied import validate, portable
from .data import read_dataset, template_groups
from .evaluate import metrics
from .review_packets import private_output
from .uncertainty import cluster_intervals


def independent_groups(training_texts, rows):
    groups=template_groups([dict(text_redacted=t) for t in training_texts]+rows)
    if set(groups[:len(training_texts)]) & set(groups[len(training_texts):]):
        raise ValueError('Exact/near-template overlap with supplied training corpus; evaluation refused')
    return groups[len(training_texts):]


def main():
    p=argparse.ArgumentParser()
    p.add_argument('reviewed_dataset',type=Path);p.add_argument('model',type=Path)
    p.add_argument('training_csv',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--independent-cohort-reference',required=True)
    a=p.parse_args();private_output(a.output)
    if unicodedata.unidata_version != '15.0.0':
        raise ValueError('Supplied preprocessing requires Python Unicode 15.0.0')
    from .intake import TOKEN
    if not TOKEN.fullmatch(a.independent_cohort_reference): raise ValueError('Use an opaque evidence reference')
    audit=json.loads(Path('docs/dataset-audit.json').read_text(encoding='utf-8'))
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    if sha(a.model)!=audit['files_sha256']['model_export_final.json'] or sha(a.training_csv)!=audit['files_sha256']['smishguard_dataset.csv']:
        raise ValueError('Expected frozen supplied model and training corpus')
    rows=read_dataset(a.reviewed_dataset)
    with a.training_csv.open(encoding='utf-8-sig',newline='') as f: training=[r['message_text'] for r in csv.DictReader(f)]
    groups=independent_groups(training,rows)
    model=validate(json.loads(a.model.read_text(encoding='utf-8-sig')))
    probabilities=[portable(model,r['text_redacted']) for r in rows]
    # >= next representable double implements the supplied strict > 0.5 decision.
    threshold=float(np.nextafter(.5,1))
    result=metrics([int(r['label']) for r in rows],probabilities,threshold)
    result.update(model_version='supplied-lr-schema2-0.2.0-dev',model_sha256=sha(a.model),
        training_data_sha256=sha(a.training_csv),evaluation_data_sha256=sha(a.reviewed_dataset),
        preprocessing_version='python-unicode-word-v2',features='raw TF-IDF L2 word unigrams/bigrams',
        threshold=.5,threshold_comparison='strict_greater',independent_cohort_reference=a.independent_cohort_reference,
        evaluation_timestamp_utc=datetime.now(timezone.utc).isoformat(),
        git_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        independence_note='Evidence reference requires human verification; heuristic overlap checks cannot prove unseen lineage.',
        confidence_intervals=cluster_intervals([int(r['label']) for r in rows],probabilities,groups,threshold),
        errors=[dict(id=r['id'],label=int(r['label']),predicted=int(score>.5)) for r,score in zip(rows,probabilities) if int(score>.5)!=int(r['label'])])
    with a.output.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2,allow_nan=False)
    print('Private fixed-model evaluation saved. Deployment approval unchanged.')


if __name__=='__main__':main()
