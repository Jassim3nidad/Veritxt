"""Seeded cluster bootstrap of fixed predictions; no model selection or refitting."""
import numpy as np


def cluster_intervals(y, probabilities, groups, threshold, seed=20260923, repetitions=1000):
    from .evaluate import metrics
    y,p,g=np.asarray(y),np.asarray(probabilities),np.asarray(groups)
    if len(y)!=len(p) or len(y)!=len(g) or len(y)==0 or repetitions<1:
        raise ValueError('Invalid bootstrap inputs')
    unique=np.unique(g)
    if len(unique)<2:
        return dict(method='cluster percentile bootstrap',status='insufficient independent groups',intervals=None)
    rng=np.random.default_rng(seed)
    keys=('accuracy','precision','recall','f1','specificity','false_positive_rate','false_negative_rate','roc_auc','pr_auc')
    samples={k:[] for k in keys}
    for _ in range(repetitions):
        indices=np.concatenate([np.flatnonzero(g==group) for group in rng.choice(unique,len(unique),replace=True)])
        result=metrics(y[indices],p[indices],threshold)
        for k in keys:
            if result[k] is not None: samples[k].append(result[k])
    return dict(method='cluster percentile bootstrap; fixed model and threshold; 95% descriptive intervals',
        seed=seed,repetitions=repetitions,groups=len(unique),
        note='Does not cover training/selection uncertainty or source sampling bias. Undefined resamples omitted per metric.',
        intervals={k:dict(valid_replicates=len(v),low=float(np.quantile(v,.025)) if v else None,
                          high=float(np.quantile(v,.975)) if v else None) for k,v in samples.items()})
