"""Audit/convert lr-calibrated-4 without training or opening its private data ZIP."""
import argparse
import ast
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import statistics

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from .convert_supplied import convert, portable, validate, PROBES
from .review_packets import private_output
from .train import write_json
from .vocabulary_policy import screen

VERSION = "lr-calibrated-4"
SOURCE_HASH = "d91f010a004e1fcfef6e4567389007cb81d16e1f6d0f258c263483b2b60d0d77"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_folded(model):
    validate(model)
    calibration = model.get('calibration', {})
    if (model.get('model_version') != VERSION or calibration.get('method') != 'platt'
            or calibration.get('folded_into_coef_and_intercept') is not True):
        raise ValueError('Expected explicitly folded lr-calibrated-4 export')
    if any(type(calibration.get(k)) not in (int, float) or not math.isfinite(calibration[k]) for k in ('a', 'b')):
        raise ValueError('Invalid calibration provenance')
    if calibration['a'] <= 0:
        raise ValueError('Unsupported calibration orientation')
    if screen(model['vocabulary'])['identifier_pattern_features']:
        raise ValueError('Identifier-pattern content check failed; no terms were removed')
    return model


def audit(private_training, public_training, output, report):
    for path in (private_training, public_training, output):
        private_output(path)
    output.mkdir(parents=True, exist_ok=True)
    source = private_training/'model_export_calibrated.json'
    if sha(source) != SOURCE_HASH:
        raise ValueError('Source identity changed; review the new candidate separately')
    model = validate_folded(json.loads(source.read_text(encoding='utf-8')))
    guide = private_training/'MODEL_INTEGRATION_calibrated.md'
    refs = re.findall(r'\| "(.+?)" \| (ham|smishing) \| ([0-9.]+) \|', guide.read_text(encoding='utf-8-sig'))
    convert(source, guide, output/'model.json', output/'base-probes.json', output/'conversion.json')
    converted = json.loads((output/'model.json').read_text(encoding='utf-8'))
    converted.update(schema_version=4, model_version=VERSION, algorithm='lr',
                     calibration_status='fitted_unvalidated', calibration_encoding='folded_into_parameters')
    # Source a/b are provenance ONLY. Do not emit executable calibration parameters.
    assert 'calibration' not in converted
    write_json(output/'model.json', converted)
    wrong_guide_rejected = False
    try:
        convert(source, private_training/'MODEL_INTEGRATION.md', output/'wrong-model.json',
                output/'wrong-cases.json', output/'wrong-report.json')
    except ValueError:
        wrong_guide_rejected = True
    if not wrong_guide_rejected:
        raise ValueError('Wrong guide was not rejected')
    supplied = json.loads((public_training/'candidate_parity_cases.json').read_text(encoding='utf-8'))
    if supplied['model_version'] != VERSION:
        raise ValueError('Parity set model identity mismatch')
    supplied_errors = [abs(portable(model, row['message'])-row['expected']) for row in supplied['cases']]
    if max(supplied_errors) > 1e-10:
        raise ValueError('Supplied full-precision parity mismatch; contents withheld')
    texts = [text for text, _, _ in refs] + [r['message'] for r in supplied['cases']] + PROBES
    # Independent TF-IDF matrix implementation; no fit, downloads, or source execution.
    vec = TfidfVectorizer(vocabulary=model['vocabulary'], ngram_range=(1, 2), lowercase=True,
                          token_pattern=r'(?u)\b\w+\b')
    vec.idf_ = np.array(model['idf'])
    margins = vec.transform(texts) @ np.array(model['coef']) + model['intercept']
    expected = 1 / (1 + np.exp(-margins))
    errors = [abs(portable(model, t)-p) for t, p in zip(texts, expected)]
    if max(errors) > 1e-10:
        raise ValueError('Independent scoring mismatch')
    doubled = 1 / (1 + np.exp(-(model['calibration']['a']*margins+model['calibration']['b'])))
    cases = [dict(text=t, score=float(p), suspicious=bool(p>.5), tokens=re.findall(r'\b\w+\b',t.lower()))
             for t, p in zip(texts, expected)]
    write_json(output/'cases.json', cases)
    android = output/'android-test-assets'; android.mkdir(exist_ok=True)
    write_json(android/'folded-private-cases.json', cases)
    metrics = list(csv.DictReader((public_training/'calibration_metrics.csv').open(encoding='utf-8')))
    aggregates = {}
    for key in sorted({(r['protocol'], r['variant'], r['model']) for r in metrics}):
        rows = [r for r in metrics if (r['protocol'],r['variant'],r['model']) == key]
        if sorted(int(r['seed']) for r in rows) != [7, 42, 99, 123, 2024]:
            raise ValueError('Unexpected metric seeds')
        aggregates[' / '.join(key)] = {k:dict(mean=statistics.mean(float(r[k]) for r in rows),
            sample_sd=statistics.stdev(float(r[k]) for r in rows)) for k in
            ('precision','recall','f1','brier','everyday_false_alarm_rate')}
        aggregates[' / '.join(key)].update(added_scams_held_out=sum(int(r['added_scams_held_out']) for r in rows),
            added_scams_caught=sum(int(r['added_scams_caught']) for r in rows))
    for name in ('train_calibrated_lr.py','build_supplementary_reviewed.py','build_supplementary_ham.py'):
        ast.parse((public_training/name).read_text(encoding='utf-8'))
    exposed_probes = {}
    for name in ('fresh_test_messages.csv','fresh_test_messages_v2.csv'):
        with (public_training/name).open(encoding='utf-8',newline='') as stream:
            rows=list(csv.DictReader(stream))
        if any(r['label'] not in {'ham','smishing'} for r in rows):
            raise ValueError('Unexpected diagnostic label')
        decisions=[portable(model,r['message'])>.5 for r in rows]
        exposed_probes[name] = dict(records=len(rows),
            correct_against_supplied_labels=sum(pred==(r['label']=='smishing') for pred,r in zip(decisions,rows)),
            false_positives=sum(pred and r['label']=='ham' for pred,r in zip(decisions,rows)),
            false_negatives=sum(not pred and r['label']=='smishing' for pred,r in zip(decisions,rows)),
            status='exposed diagnostic messages; supplied labels; not independent performance; mathematical scorer before Android abstention')
    conversion = json.loads((output/'conversion.json').read_text(encoding='utf-8'))
    summary = dict(model_version=VERSION, source_sha256=sha(source), converted_sha256=sha(output/'model.json'),
        matching_guide_sha256=sha(guide), source_bytes=source.stat().st_size, converted_bytes=(output/'model.json').stat().st_size,
        content_screen=screen(model['vocabulary']), human_review='not recorded; no acceptance fabricated',
        training_rows_supplied=model['trained_on_rows'], training_data_supplied=model['training_data'],
        calibration_encoding='folded coefficients and intercept; runtime sigmoid once; original fitted objects absent',
        threshold=dict(value=.5, comparison='strict_greater', basis='matching guide/default evaluation; provisional, not optimized on exposed test table'),
        guide_references=len(refs), guide_max_rounded_error=max(r['absolute_error'] for r in conversion['guide_references']),
        wrong_guide_rejected=wrong_guide_rejected, supplied_full_precision_cases=len(supplied_errors),
        supplied_max_error=max(supplied_errors), independent_cases=len(cases), independent_max_error=float(max(errors)),
        double_calibration_max_deviation=float(np.max(np.abs(doubled-expected))),
        source_hashes={name:sha(public_training/name) for name in ('train_calibrated_lr.py','build_supplementary_reviewed.py','calibration_report.md')},
        recalculated_supplied_metrics=aggregates, private_data_archive_opened=False, training_executed=False,
        exposed_diagnostic_sets=exposed_probes,
        implemented_scope='financial-institution impersonation plus institution-branded casino ads; adviser confirmation not established',
        report_conflict='stale write_report literals claim casino exclusion; build_supplementary_reviewed retains 47 primary casino IDs and promotes branded additions',
        candidate_review='automated technical/content screen supports private experiment only; research labels and scope remain provisional')
    for kind in ('jvm','android'):
        result = output/f'{kind}-folded-aggregate.json'
        if result.exists():
            record = json.loads(result.read_text(encoding='utf-8'))
            if record.get('model_sha256') == sha(output/'model.json') and record.get('cases_sha256') == sha(output/'cases.json'):
                summary[kind] = record
    write_json(report, summary)
    print('Folded candidate audit passed. Only aggregates published; private data archive unopened.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('private_training','public_training','output','report'):
        parser.add_argument(name,type=Path)
    args=parser.parse_args(); audit(args.private_training,args.public_training,args.output,args.report)


if __name__ == '__main__': main()
