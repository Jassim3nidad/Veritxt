"""Fresh fixed-setting standalones, then strictly verified equivalent mBERT OOF reuse."""
import argparse
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research'))
from smishguard import ensemble_compare as e
from recover_update_mbert_cache import recover


def train(run,previous):
    e.context(run)
    if (run/'selection.json').exists() or (run/'test-started.json').exists():
        raise ValueError('No fitting after selection/test')
    with (run/'training-started.json').open('x',encoding='utf-8') as f:
        json.dump(dict(started=time.time()),f)
    e.train_classical(run)
    try:
        e.train_mbert(run)
    except (RuntimeError,ImportError,ValueError,MemoryError) as error:
        e.record_failure(run,'mbert',error)
        return
    try:
        recover(run,previous)
    except (RuntimeError,ImportError,ValueError,MemoryError,AssertionError) as error:
        e.record_failure(run,'mbert_cache',error)
        if any((run/f'mbert-oof-{k}').exists() for k in range(5)):
            return
        try:
            e.train_mbert_oof(run)
        except (RuntimeError,ImportError,ValueError,MemoryError) as fitting_error:
            e.record_failure(run,'mbert_stacking',fitting_error)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('run',type=Path)
    p.add_argument('--previous',type=Path,default=ROOT/'research/data/ensemble-20261011/experiment-v1')
    a=p.parse_args()
    train(a.run,a.previous)
