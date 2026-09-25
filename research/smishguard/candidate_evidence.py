"""Validate supplied aggregate tables, without importing trainers or loading models."""
import csv
import math
import statistics
from pathlib import Path

EVIDENCE = Path(__file__).resolve().parents[1] / 'candidate_review'
METRICS = ('accuracy', 'precision', 'recall', 'f1', 'brier', 'log_loss', 'ece',
           'avg_score_legit', 'avg_score_scam', 'everyday_false_alarm_rate', 'everyday_avg_score')
SEEDS = {42, 7, 123, 2024, 99}


def read_table(path, columns):
    with path.open(encoding='utf-8-sig', newline='') as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != list(columns):
            raise ValueError('Unexpected aggregate schema')
        rows = list(reader)
    if any(None in row or any(v is None for v in row.values()) for row in rows):
        raise ValueError('Malformed aggregate row')
    return rows


def validate_metrics(rows):
    expected = {(p, v, s, m) for p, v in [('grouped', 'primary only'),
                ('grouped', 'with everyday'), ('random', 'with everyday')]
                for s in SEEDS for m in ('raw', 'calibrated')}
    seen = set()
    for row in rows:
        key = (row['protocol'], row['variant'], int(row['seed']), row['model'])
        if key not in expected or key in seen:
            raise ValueError('Unexpected or duplicate experimental cell')
        seen.add(key)
        values = {k: float(row[k]) for k in METRICS}
        if any(not math.isfinite(v) or v < 0 or (k != 'log_loss' and v > 1)
               for k, v in values.items()):
            raise ValueError('Invalid metric range')
        p, r = values['precision'], values['recall']
        f1 = 2*p*r/(p+r) if p+r else 0
        if not math.isclose(f1, values['f1'], abs_tol=1e-12):
            raise ValueError('F1 does not agree with precision and recall')
    if seen != expected:
        raise ValueError('Incomplete experimental grid')


def validate_reliability(rows):
    seen, totals = set(), {}
    for row in rows:
        model, band = row['model'], row['band']
        bands = [f'{i/10:.1f}-{(i+1)/10:.1f}' for i in range(10)]
        if model not in ('raw', 'calibrated') or band not in bands or (model, band) in seen:
            raise ValueError('Unexpected or duplicate reliability cell')
        seen.add((model, band))
        n = int(row['messages'])
        score, rate = float(row['avg_score']), float(row['actual_scam_rate'])
        lo, hi = map(float, band.split('-'))
        if n <= 0 or not (math.isfinite(score) and lo <= score <= hi and 0 <= rate <= 1):
            raise ValueError('Invalid reliability range')
        positives = n*rate
        if not math.isclose(positives, round(positives), abs_tol=1e-9):
            raise ValueError('Nonintegral reliability event count')
        count, events = totals.get(model, (0, 0))
        totals[model] = (count+n, events+round(positives))
    if len(seen) != 20 or totals['raw'] != totals['calibrated']:
        raise ValueError('Reliability cohorts do not agree')
    return totals


def review(directory=EVIDENCE):
    rows = read_table(directory/'calibration_metrics.csv', ('protocol', 'variant', 'seed', 'model', *METRICS))
    reliability = read_table(directory/'reliability.csv', ('model', 'band', 'messages', 'avg_score', 'actual_scam_rate'))
    validate_metrics(rows)
    totals = validate_reliability(reliability)
    summary = {}
    for protocol, variant in [('grouped', 'primary only'), ('grouped', 'with everyday'), ('random', 'with everyday')]:
        for model in ('raw', 'calibrated'):
            part = [r for r in rows if (r['protocol'], r['variant'], r['model']) == (protocol, variant, model)]
            summary[f'{protocol}/{variant}/{model}'] = {
                k: {'mean': statistics.mean(float(r[k]) for r in part),
                    'sample_sd': statistics.stdev(float(r[k]) for r in part)} for k in METRICS}
    return {'status': 'supplied aggregates checked; no inference or training reproduced',
            'metric_rows': len(rows), 'reliability_rows': len(reliability),
            'pooled_observations_not_unique_messages': totals, 'summary': summary}


if __name__ == '__main__':
    import json
    print(json.dumps(review(), indent=2, allow_nan=False))
