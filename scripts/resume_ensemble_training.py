"""Recover interrupted mBERT OOF work without changing the sealed experiment.

Completed fold weights are reused. An interrupted fit without optimizer state is
preserved in an attempts directory and restarted from the same seed/base weights.
No validation or test prediction is used by this recovery path.
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys
import time

import numpy as np
from scipy.special import softmax

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research'))
from smishguard.ensemble_compare import context, load, probability
from smishguard import ensemble_mbert as bert
from smishguard import fair_compare as fair
from smishguard.train import write_json


def resume(run):
    run=run.resolve()
    if (run/'selection.json').exists() or (run/'test-started.json').exists():
        raise ValueError('Cannot fit after selection/test opening')
    cfg,rows,m=context(run)
    if not (run/'mbert/calibrator.pkl').exists():
        raise ValueError('This recovery expects completed standalone baselines')
    train=np.array(m['partitions']['train'])
    p=np.full(len(train),np.nan)
    timings=[]
    history_path=run/'attempt-history.json'
    history=load(history_path) if history_path.exists() else []
    for k,fold in enumerate(m['inner_folds']):
        folder=run/f'mbert-oof-{k}'
        a,b=train[fold['train']],train[fold['validation']]
        completed=(folder/'training-summary.json').exists()
        if folder.exists() and not completed:
            # Verify both absolute targets remain under this exact private run.
            archive=run/'interrupted-attempts'/(folder.name+'-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
            if not folder.resolve().is_relative_to(run) or not archive.resolve().is_relative_to(run):
                raise ValueError('Archive target escapes run')
            archive.parent.mkdir(exist_ok=True)
            folder.rename(archive)
            history.append(dict(fold=k,status='interrupted',preserved_at=str(archive.relative_to(run)),
                reason='Prior process no longer running; no completed checkpoint or resumable optimizer state',
                recovery='Restart from identical base weights, seed and settings; completed folds retained',
                interrupted_fit_seconds=None))
            write_json(history_path,history)
        if completed:
            result=load(folder/'training-summary.json')
            foldcfg=load(folder/'configuration.json')
            if not result['complete'] or result['fixed_epoch']!=2 or foldcfg['checkpoint_validation_indices'] is not None:
                raise ValueError('Invalid completed fold')
            np.testing.assert_array_equal(foldcfg['train_indices'],a)
            print('Reusing completed fold',k+1,flush=True)
        else:
            print('Training fold',k+1,'of 5 with unchanged settings',flush=True)
            result=bert.fit(Path(cfg['base']),rows,a,folder)
        # Save each OOF prediction timing durably. The original interrupted driver
        # held timings in memory; a completed fold with missing timing is re-scored.
        if (folder/'oof-timing.json').exists():
            saved=dict(np.load(folder/'oof.npz'))
            np.testing.assert_array_equal(saved['positions'],fold['validation'])
            np.testing.assert_array_equal(saved['indices'],b)
            values=saved['probabilities']
            timing=load(folder/'oof-timing.json')
        else:
            raw,seconds=bert.logits(folder/result['final_path'],[rows[i]['text'] for i in b],result['max_length'],'cuda')
            values=probability(softmax(raw,axis=1))[:,1]
            if (folder/'oof.npz').exists():
                saved=dict(np.load(folder/'oof.npz'))
                np.testing.assert_array_equal(saved['positions'],fold['validation'])
                np.testing.assert_array_equal(saved['indices'],b)
                np.testing.assert_array_equal(saved['probabilities'],values)
            else:
                np.savez(folder/'oof.npz',positions=np.array(fold['validation']),indices=b,probabilities=values)
            timing=dict(fit_seconds=result['seconds'],oof_prediction_seconds=seconds,
                prediction_timing_remeasured_after_interruption=completed,
                checkpoint_sha256=fair.digest(folder/result['final_path']/'model.safetensors'))
            write_json(folder/'oof-timing.json',timing)
        if not np.isfinite(values).all() or ((values<0)|(values>1)).any():
            raise ValueError('Invalid saved OOF probabilities')
        p[fold['validation']]=values
        timings.append(timing)
    if not np.isfinite(p).all():
        raise ValueError('Incomplete recovered OOF matrix')
    np.savez(run/'mbert-oof.npz',mbert=p,train_indices=train)
    write_json(run/'mbert-oof-timing.json',dict(folds=timings,
        seconds=sum(t['fit_seconds']+t['oof_prediction_seconds'] for t in timings),
        excludes_interrupted_attempt=True,interrupted_fit_seconds=None))
    history.append(dict(status='recovered_complete',completed_at=datetime.now(timezone.utc).isoformat()))
    write_json(history_path,history)
    print('All five mBERT OOF folds complete; no validation/test predictions used.',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('run',type=Path)
    a=p.parse_args()
    resume(a.run)
