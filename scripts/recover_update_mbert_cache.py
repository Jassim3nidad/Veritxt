"""Recover verified mBERT OOF reuse after a CRLF-only cache false rejection.

Keep raw artifact/source hashes intact. Verify original frozen snapshots and
universal-newline source equality instead of comparing old LF to checkout CRLF.
No fitting settings, thresholds or predictions are selected by this recovery.
"""
import argparse
import ast
import hashlib
import importlib.metadata
from pathlib import Path
import shutil
import subprocess
import sys
import time

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research'))
from smishguard import ensemble_compare as e
from smishguard import fair_compare as fair
from smishguard.train import write_json


def recover(run,previous):
    if (run/'selection.json').exists() or (run/'test-started.json').exists():
        raise ValueError('Recovery forbidden after selection or test opening')
    cfg,rows,m=e.context(run)
    oldcfg=e.load(previous/'configuration.json')
    oldrows=e.load(previous/'dataset.json')
    oldm=e.load(previous/'splits.json')
    if rows!=oldrows or m!=oldm:
        raise ValueError('Cache fitting inputs/labels/groups/folds differ')
    for key in ('baseline_seed','mbert_seed','versions'):
        if cfg[key]!=oldcfg[key]:
            raise ValueError('Cache seed/dependencies differ')
    source_proof={}
    for name,h in oldcfg['code_sha256'].items():
        filename=Path(name).name
        saved=previous/'code'/filename
        live=ROOT/'research/smishguard'/filename
        if fair.digest(saved)!=h:
            raise ValueError('Original source snapshot hash mismatch')
        old=saved.read_bytes();new=live.read_bytes()
        if old.replace(b'\r\n',b'\n')!=new.replace(b'\r\n',b'\n'):
            raise ValueError('Cache source content differs: '+filename)
        oldtext=saved.read_text(encoding='utf-8');newtext=live.read_text(encoding='utf-8')
        if ast.dump(ast.parse(oldtext),include_attributes=False)!=ast.dump(ast.parse(newtext),include_attributes=False):
            raise ValueError('Cache Python syntax differs')
        source_proof[filename]=dict(original_raw_sha256=h,current_raw_sha256=fair.digest(live),
            normalized_source_sha256=hashlib.sha256(new.replace(b'\r\n',b'\n')).hexdigest(),
            universal_newline_text_identical=True,syntax_identical=True,raw_bytes_identical=old==new)
    oldenv=(previous/'environment.txt').read_text(encoding='utf-8').splitlines()
    currentenv=subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True).splitlines()
    if set(oldenv)!=set(currentenv):
        raise ValueError('Complete dependency lock differs, including direct wheel references')
    versions={}
    for name in ('torch','transformers','tokenizers','huggingface-hub','safetensors','numpy','scipy','scikit-learn'):
        version=importlib.metadata.version(name)
        direct=[line for line in oldenv if line.startswith(name+' @ ')]
        if name+'=='+version not in oldenv and not direct:
            raise ValueError('Cache dependency version differs')
        versions[name]=version
    base=Path(cfg['base'])
    expected=e.load(base.parent/'base-file-hashes.json')
    if any(fair.digest(base/name)!=h for name,h in expected.items()):
        raise ValueError('Pinned base/tokenizer changed')
    frozen=e.load(previous/'freeze.json')['files']
    files={name:h for name,h in frozen.items() if name.replace('\\','/').startswith('mbert-oof-')
           or name.replace('\\','/') in {'mbert-oof.npz','mbert-oof-timing.json'}}
    if not files:
        raise ValueError('Missing frozen cache')
    for name,h in files.items():
        if fair.digest(previous/name)!=h:
            raise ValueError('Cached fitted artifact changed')
    train=np.array(m['partitions']['train'])
    mb=dict(np.load(previous/'mbert-oof.npz'))
    np.testing.assert_array_equal(mb['train_indices'],train)
    for k,fold in enumerate(m['inner_folds']):
        folder=previous/f'mbert-oof-{k}'
        c=e.load(folder/'configuration.json');summary=e.load(folder/'training-summary.json')
        np.testing.assert_array_equal(c['train_indices'],train[fold['train']])
        expected_settings=dict(seed=20261005,epochs=2,learning_rate=2e-5,weight_decay=.01,optimizer='Adafactor',
            microbatch=1,gradient_accumulation=8,wall_budget_seconds=2700)
        if any(c[key]!=v for key,v in expected_settings.items()):
            raise ValueError('Cached fold fitting settings changed')
        if c['checkpoint_validation_indices'] is not None or c['checkpoint_policy']!='fixed_epoch_2':
            raise ValueError('Cached OOF checkpoint uses outer validation')
        if not summary['complete'] or summary['fixed_epoch']!=2 or len(summary['history'])!=2:
            raise ValueError('Cached fold incomplete')
        if any(h['validation_average_precision'] is not None for h in summary['history']):
            raise ValueError('Cached OOF validation selection detected')
        saved=dict(np.load(folder/'oof.npz'))
        np.testing.assert_array_equal(saved['indices'],train[fold['validation']])
        np.testing.assert_array_equal(saved['positions'],fold['validation'])
        np.testing.assert_array_equal(saved['probabilities'],mb['mbert'][fold['validation']])
        modelcfg=e.load(folder/summary['final_path']/'config.json')
        if modelcfg['id2label']!={'0':'ham','1':'smishing'}:
            raise ValueError('Cached mBERT class order differs')
    started=time.perf_counter()
    for k in range(5):
        shutil.copytree(previous/f'mbert-oof-{k}',run/f'mbert-oof-{k}')
    for name in ('mbert-oof.npz','mbert-oof-timing.json'):
        shutil.copy2(previous/name,run/name)
    for name,h in files.items():
        if fair.digest(run/name)!=h:
            raise ValueError('Copied cache integrity failed')
    write_json(run/'cache-source-equivalence.json',source_proof)
    write_json(run/'mbert-oof-reuse.json',dict(status='verified_reuse_after_line_ending_false_rejection',source=str(previous.resolve()),
        identical_ordered_fitting_views_labels_groups_and_folds=True,versions_exact=True,
        complete_dependency_lock_identical_including_direct_references=True,versions=versions,
        fitting_code_universal_newline_text_and_syntax_exact=True,fixed_epochs_no_outer_validation_selection=True,
        source_frozen_files_verified=len(files),files=files,copy_and_integrity_seconds=time.perf_counter()-started,
        historical_measured_required_oof_seconds=e.load(run/'mbert-oof-timing.json')['seconds'],
        newly_trained_oof_folds=0,historical_validation_or_test_predictions_read=False,
        excludes_interrupted_fallback_attempt=True,interrupted_fallback_fit_seconds=None))
    amendment='''# Cache verification amendment before selection

The original raw-code gate rejected LF source snapshots against an otherwise
identical CRLF checkout. All original saved-source hashes remain verified, and all
current/saved Python source text is identical after universal-newline decoding;
ASTs are also identical. The full pip-freeze lock is identical, including the
original torch direct wheel reference (which is not a torch==version entry).
Original fitted artifact hashes, ordered inputs, labels,
groups/folds, dependencies, seeds, fitting settings and pinned base/tokenizer hashes
match. Recovery therefore accepts these identical OOF fits without changing any
modeling implementation, fitting setting, threshold, configuration-selection rule
or prediction. The fresh fallback fold was interrupted and preserved; no partial
fit or prediction is used. Its duration is unavailable, excluded rather than invented.
This amendment concerns cache identity checks only and precedes final selection/test.
'''
    (run/'cache-verification-amendment.md').write_text(amendment,encoding='utf-8')
    shutil.copy2(Path(__file__),run/'workflow-code'/Path(__file__).name)
    history=e.load(run/'attempt-history.json') if (run/'attempt-history.json').exists() else []
    if (run/'mbert-cache-rejection.json').exists():
        history.append(dict(status='cache_metadata_check_rejected_before_copy',reason='First recovery required version== lines; historical torch is an identical direct wheel reference',
            dependency_lock_changed=False,fitting_configuration_changed=False))
    history.append(dict(status='recovered_complete',experiment='mbert_oof_verified_cache',
        successful_cached_folds=5,modeling_code_changed=False,source_difference='CRLF/LF only'))
    write_json(run/'attempt-history.json',history)
    print('All five mBERT OOF caches verified/copied; LF/CRLF differences only. No test predictions opened.',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('run',type=Path)
    p.add_argument('--previous',type=Path,default=ROOT/'research/data/ensemble-20261011/experiment-v1')
    a=p.parse_args()
    recover(a.run,a.previous)
