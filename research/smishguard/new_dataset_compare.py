"""Audit a supplied update without executing its scripts or changing old experiments.

This adapter deliberately refuses a changed eligible corpus: the historical audit
and reproduction diagnostics used here are valid only for identical fitting views.
A changed corpus requires its own general preparation adapter, never a quiet fallback.
"""
import argparse
from collections import Counter, defaultdict
import csv
from difflib import SequenceMatcher
import hashlib
import io
import importlib.metadata
import json
from pathlib import Path
import re
import shutil
import time
import xml.etree.ElementTree as ET
import zipfile

import numpy as np

from . import ensemble_compare as ensemble
from . import fair_compare as fair
from .data import split_rows, template_groups
from .expanded_prepare import ADDRESS, clean, counts, fingerprint
from .mbert_experiment import redacted_case_view
from .preliminary_compare import PERSON, OBFUSCATED
from .preprocessing import normalize
from .source_matching import SOURCES, parse_member
from .train import write_json

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / 'docs/new-dataset-comparison-protocol-20261013.md'
URL = re.compile(r'(https?://\S+|www\.\S+|\b[a-z0-9][a-z0-9-]*(?:\.[a-z0-9-]+)*\.[a-z]{2,8}(?:/\S*)?\b)', re.I)


def read_csv(path):
    payload = path.read_bytes()
    text = payload.decode('utf-8-sig', errors='strict')
    return list(csv.DictReader(io.StringIO(text, newline='')))


def template_key(text):
    value = re.sub(r'[0-9]+', '#', URL.sub(' ', text.lower()))
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z# ]', ' ', value)).strip()


def label_value(label):
    if label not in {'ham', 'smishing'}:
        raise ValueError('Unsupported binary label; preserve and hold, never infer a mapping')
    return int(label == 'smishing')


def workbook_review(path):
    ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
          'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
    result = {}
    with zipfile.ZipFile(path) as z:
        shared = []
        if 'xl/sharedStrings.xml' in z.namelist():
            shared = [''.join(n.text or '' for n in si.findall('.//s:t', ns))
                      for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si', ns)]
        rels = {r.get('Id'): r.get('Target') for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        for sheet in ET.fromstring(z.read('xl/workbook.xml')).findall('s:sheets/s:sheet', ns):
            target = rels[sheet.get('{'+ns['r']+'}id')]
            member = target.lstrip('/') if target.startswith('/') else 'xl/'+target
            values = []
            for row in ET.fromstring(z.read(member)).findall('s:sheetData/s:row', ns):
                record = {}
                for cell in row.findall('s:c', ns):
                    v = cell.find('s:v', ns)
                    value = v.text if v is not None else ''.join(n.text or '' for n in cell.findall('.//s:t', ns))
                    record[re.sub(r'\d', '', cell.get('r'))] = shared[int(value)] if cell.get('t') == 's' else value
                values.append(record)
            if not values:
                continue
            headers = values[0]
            relevant = {k: v for k, v in headers.items() if v and any(s in v.lower() for s in ('labeler', 'final_label', 'annotator', 'final label'))}
            result[sheet.get('name')] = dict(records=len(values)-1,
                review_nonblank={v: sum(bool((r.get(k) or '').strip()) for r in values[1:]) for k,v in relevant.items()})
    return result


def exposure(package_rows, output, new_root):
    """Inventory all available old SMS corpora; compare content, never record IDs."""
    data_root = ROOT/'research/data'
    history = defaultdict(set)
    inventory = {}
    history_labels = defaultdict(set)
    candidates = set(data_root.rglob('dataset.json')) | set(data_root.rglob('case-view.json'))
    candidates |= {p for p in data_root.rglob('*.csv')
                   if any(s in p.name.lower() for s in ('dataset', 'fresh_test', 'external-uci', 'non-uci', 'intake'))}
    for path in sorted(candidates):
        if path.resolve().is_relative_to(new_root.resolve()):
            continue
        rows = ensemble.load(path) if path.suffix == '.json' else read_csv(path)
        if not isinstance(rows, list):
            continue
        split_path = path.parent/'splits.json'
        parts = ensemble.load(split_path).get('partitions', {}) if split_path.exists() else {}
        memberships = {i: part for part, indices in parts.items() for i in indices} if all(isinstance(i,int) for indices in parts.values() for i in indices) else {}
        file_key = path.relative_to(data_root).as_posix()
        record_count = 0
        for i,r in enumerate(rows):
            text = next((r.get(k) for k in ('text', 'message_text', 'message', 'text_redacted', 'redacted_text') if r.get(k)), None)
            if not text:
                continue
            view = normalize(redacted_case_view(clean(text)))
            if not view:
                continue
            tag = file_key+'::'+memberships.get(i, 'partition_unknown')
            history[view].add(tag)
            if r.get('label') in ('0', 0, 'ham', '1', 1, 'smishing'):
                history_labels[view].add(int(r.get('label') in ('1', 1, 'smishing')))
            record_count += 1
        inventory[file_key] = dict(sha256=fair.digest(path), records_with_text=record_count,
            membership_known=bool(memberships), reason='Available historical corpus; participation may be incompletely documented')
    texts = sorted(history)
    chars = sorted(set(''.join(texts)))
    hist = np.array([[t.count(c) for c in chars] for t in texts], dtype=np.int32)
    lengths = np.array([len(t) for t in texts])
    ledger = []
    cache = {}
    for n,r in enumerate(package_rows):
        view = normalize(redacted_case_view(clean(r['text'])))
        if view not in cache:
            exact = history.get(view, set())
            near = set()
            matches = []
            vector = np.array([view.count(c) for c in chars])
            bounds = 2*np.minimum(hist,vector).sum(axis=1)/np.maximum(1,lengths+len(view))
            for i in np.flatnonzero(bounds >= .85):
                needed = history[texts[i]]-exact-near
                if needed and SequenceMatcher(None,view,texts[i],autojunk=False).ratio() >= .85:
                    near.update(needed)
                    matches.append(int(i))
            cache[view] = dict(normalized_exact=sorted(exact), near_only=sorted(near), historical_match_indices=matches)
        ledger.append(dict(id=r['id'],**cache[view],
            conflicting_historical_binary_labels=sorted(history_labels.get(view,set())-{label_value(r['label'])}) if r['label'] in {'ham','smishing'} else []))
        if (n+1)%500 == 0:
            print('All-source historical overlap',n+1,'/',len(package_rows),flush=True)
    write_json(output/'historical-inventory.json',inventory)
    write_json(output/'exposure-ledger.json',ledger)
    by_source = {}
    for source in sorted({r['source'] for r in package_rows}):
        ii = [i for i,r in enumerate(package_rows) if r['source']==source]
        by_source[source] = dict(records=len(ii),exact=sum(bool(ledger[i]['normalized_exact']) for i in ii),
            near_only=sum(not ledger[i]['normalized_exact'] and bool(ledger[i]['near_only']) for i in ii),
            no_detected_overlap=sum(not ledger[i]['normalized_exact'] and not ledger[i]['near_only'] for i in ii))
    summary = dict(records=len(ledger),historical_files=len(inventory),historical_unique_normalized_texts=len(texts),
        exact=sum(bool(r['normalized_exact']) for r in ledger),
        near_only=sum(not r['normalized_exact'] and bool(r['near_only']) for r in ledger),
        no_detected_overlap=sum(not r['normalized_exact'] and not r['near_only'] for r in ledger),
        any_known_overlap=sum(bool(r['normalized_exact'] or r['near_only']) for r in ledger),by_source=by_source,
        historical_binary_label_disagreement_records=sum(bool(r['conflicting_historical_binary_labels']) for r in ledger),
        method='All discovered historical dataset/case-view/intake and supplied SMS CSVs; normalized exact and SequenceMatcher >=0.85; lossless multiset bound',
        limitations='Old membership is not always available; possible-corpus overlap is conservative exposure evidence, not proof every old row was fitted. No detected overlap is not proof of prospective independence.')
    write_json(output/'exposure-summary.json',summary)
    return ledger, summary


def audit(package, output, source, base, snapshots):
    if output.exists():
        raise ValueError('New versioned output required')
    output.mkdir(parents=True)
    original = read_csv(package/'smishguard_dataset.csv')
    excluded = read_csv(package/'smishguard_excluded.csv')
    required = {'id','text','label','category','language','source','source_category','sender','date','template_group','label_method','confidence','needs_review'}
    if not original or set(original[0]) != required or any(None in r for r in original):
        raise ValueError('Unsupported schema')
    if len({r['id'] for r in original}) != len(original) or any(not r['id'] or not r['text'].strip() for r in original):
        raise ValueError('Missing/duplicate identity or empty message')
    indexes = {}
    for name, spec in SOURCES.items():
        with zipfile.ZipFile(snapshots/(name+'.zip')) as z:
            raw = z.read(spec['member'])
        if hashlib.sha256(raw).hexdigest() != spec['sha256']:
            raise ValueError('Pinned source mismatch')
        index = defaultdict(list)
        for i,r in enumerate(parse_member(raw,spec['member'])):
            text = clean(r.get('text',''))
            index[text.lower()].append((i,text))
        indexes[name] = index
    exact = defaultdict(list)
    normalized = defaultdict(list)
    supplied = defaultdict(list)
    for r in original:
        exact[clean(r['text']).lower()].append(r)
        normalized[normalize(redacted_case_view(r['text']))].append(r)
        supplied[r['template_group']].append(r)
    conflicts = {k for k,v in normalized.items() if len({r['label'] for r in v}) > 1}
    held, ledger, usable = Counter(), [], []
    for r in original:
        reason, matched, view = None, None, None
        if r['label'] not in {'ham','smishing'}:
            reason = 'unsupported_binary_label_'+r['label']
        elif r['source'].startswith('GitHub'):
            reason = 'github_permission_unresolved'
        elif r['source'].startswith('Team'):
            reason = 'team_origin_consent_use_unresolved'
        elif r['source'].startswith('Kaggle'):
            name = 'tagalog' if 'Tagalog-SMS' in r['source'] else 'marketing' if 'Chua' in r['source'] else 'bwandowando'
            hits = indexes[name].get(clean(r['text']).lower(),[])
            if not hits:
                reason = 'no_cleaned_exact_pinned_source_match'
            else:
                matched = dict(source=name,source_row=hits[0][0])
                text = hits[0][1]
                if PERSON.search(text) or OBFUSCATED.search(text) or ADDRESS.search(text):
                    reason = 'automated_privacy_hold'
                view = redacted_case_view(text)
                if normalize(view) in conflicts:
                    reason = 'conflicting_redacted_labels'
                if not normalize(view) or len(view)>10000:
                    reason = 'empty_or_overlong'
        else:
            reason = 'unsupported_source'
        record = dict(**r,original_sha256=fingerprint(r['text']),source_match=matched,hold_reason=reason,
            human_label_review='pending',human_privacy_review='pending')
        ledger.append(record)
        if reason:
            held[reason] += 1
        else:
            usable.append(dict(id=r['id'],text=view,text_redacted=normalize(view),label=label_value(r['label']),
                template_group=r['template_group'],source=matched['source'],language=r['language'],category=r['category'],
                needs_review=r['needs_review'],content_sha256=record['original_sha256']))
    write_json(output/'private-intake-ledger.json',ledger)
    old = ensemble.load(source/'dataset.json')
    if usable != old:
        write_json(output/'unsupported-preparation.json',dict(held=dict(held),retained=counts(usable),
            reason='Eligible fitting views changed; historical reproduction adapter cannot be used'))
        raise ValueError('Changed eligible corpus requires a general preparation adapter')
    print('Eligible fitting views exactly equal historical corpus:',len(usable),'; holds:',dict(held),flush=True)
    groups = np.array(template_groups(usable))
    parts = split_rows(usable,groups,'group',fair.SEED)
    train = parts['train']
    folds = fair.training_folds(np.array([usable[i]['label'] for i in train]),groups[train])
    manifest = dict(partitions=parts,groups=groups.tolist(),inner_folds=[dict(train=a.tolist(),validation=b.tolist()) for a,b in folds])
    if manifest != ensemble.load(source/'splits.json'):
        raise ValueError('Recreated deterministic split differs; cannot claim reproduction')
    print('Deterministic template groups/splits recreated exactly; full-package grouping begins.',flush=True)
    full_views = [dict(text_redacted=normalize(redacted_case_view(r['text'])),template_group=r['template_group']) for r in original]
    full_groups = template_groups(full_views)
    write_json(output/'full-package-template-groups.json',dict(ids=[r['id'] for r in original],groups=full_groups,similarity=.85,label_blind=True))
    exposure_ledger, exposure_summary = exposure(original,output,output.parent)
    new_index = {r['id']:r for r in original}
    previous = read_csv(source.parent/'original/smishguard_dataset_2026-10-04/smishguard_dataset.csv')
    changes = Counter(k for r in previous for k in r if r[k]!=new_index[r['id']][k])
    ase = read_csv(package/'asea_ready.csv')
    if ase != [r for r in original if r['id'].startswith('SG-A')]:
        raise ValueError('ASEA auxiliary/final inconsistency')
    raw_audit = dict(included_records=len(original),labels=dict(Counter(r['label'] for r in original)),
        schema=sorted(required),encoding='strict UTF-8; optional BOM',missing={k:sum(not r[k].strip() for r in original) for k in required},
        duplicate_ids=0,duplicate_exact_text=sum(len(v)-1 for v in exact.values()),
        normalized_duplicate_records=sum(len(v)-1 for v in normalized.values()),normalized_conflict_groups=len(conflicts),
        normalized_conflict_records=sum(len(normalized[k]) for k in conflicts),
        supplied_template_groups=len(supplied),computed_template_groups=len(set(full_groups)),
        mixed_label_computed_groups=sum(len({r['label'] for r,g in zip(original,full_groups) if g==group})>1 for group in set(full_groups)),
        supplied_template_key_mismatches=sum(template_key(r['text'])!=r['template_group'] for r in original),
        source_counts={s:dict(Counter(r['label'] for r in original if r['source']==s)) for s in sorted({r['source'] for r in original})},
        label_methods=dict(Counter(r['label_method'] for r in original)),confidence=dict(Counter(r['confidence'] for r in original)),
        flagged_records=sum(r['needs_review']=='True' for r in original),excluded_records=len(excluded),
        excluded_labels=dict(Counter(r['excluded_as'] for r in excluded)),
        included_excluded_exact_overlap=len({clean(r['text']).lower() for r in original}&{clean(r['text']).lower() for r in excluded}),
        previous_row_count=len(previous),previous_rows_all_present=True,previous_field_changes=dict(changes),
        asea_auxiliary_duplicate_copy=True,review_workbook=workbook_review(package/'smishguard_dataset_review.xlsx'),
        raw_build_reproduced=False,raw_build_reason='Supplied scripts contain hardcoded paths and lack all raw input sources; scripts inspected, never executed',
        package_files={p.name:fair.digest(p) for p in package.iterdir() if p.is_file()},held=dict(held),retained=counts(usable,groups),
        eligible_dataset_unchanged=True,deterministic_split_recreated_exactly=True,
        confirmed_input_problems=['Third label gambling_ad has no binary mapping; held unchanged',
            'README mixes old/new counts and says binary schema although CSV contains three labels',
            'ASEA source permission explicitly pending; team source-use/privacy evidence unresolved',
            'Independent human reviews absent; supplied labels are source/rule-derived',
            'New eligible fitting corpus has no newly admitted records; every eligible record has historical exposure'],
        confirmed_training_implementation_bugs=[],label_orientation={'ham':0,'smishing':1},
        status='Retrospective reproduction under existing source/privacy policy; no newly eligible data')
    write_json(output/'new-package-audit.json',raw_audit)
    # Historical audit checks all original fitting artifacts, never historical test scores.
    temp = output.parent/'historical-preflight'
    ensemble.audit(source,temp,base)
    for path in temp.iterdir():
        if path.name in {'preflight-seal.json','protocol.md','exposure-summary.json','configuration.json','audit.json'}:
            continue
        if path.is_dir():
            shutil.copytree(path,output/path.name)
        else:
            shutil.copy2(path,output/path.name)
    cfg = ensemble.load(temp/'configuration.json')
    shutil.copy2(PROTOCOL,output/'protocol.md')
    cfg.update(protocol_sha256=fair.digest(PROTOCOL),status=raw_audit['status'],new_package_sha256=raw_audit['package_files'],
        newly_eligible_records=0,previous_eligible_dataset_identical=True,previous_deterministic_split_identical=True,
        new_package_audit_sha256=fair.digest(output/'new-package-audit.json'))
    cfg['code_sha256']['code/new_dataset_compare.py'] = fair.digest(Path(__file__))
    historical_audit = ensemble.load(temp/'audit.json')
    historical_audit.update(new_package=raw_audit,exposure=exposure_summary,
        current_reserved_test_prior_exact_overlap=sum(bool(exposure_ledger[[r['id'] for r in original].index(usable[i]['id'])]['normalized_exact']) for i in parts['test']))
    write_json(output/'configuration.json',cfg)
    write_json(output/'audit.json',historical_audit)
    write_json(output/'splits.json',manifest)
    write_json(output/'new-package-preservation.json',dict(original_files=raw_audit['package_files'],zip_sha256=fair.digest(output.parent/'smishguard_dataset_2026-10-12.zip')))
    write_json(output/'preflight-seal.json',dict(files={str(p.relative_to(output)):fair.digest(p) for p in output.rglob('*') if p.is_file()}))
    print('New-package audit sealed; no model has been fitted or test predictions opened.',flush=True)


def reuse_mbert_oof(output, previous):
    """Reuse only hash-verified fits on identical ordered rows/folds and settings."""
    cfg,rows,m = ensemble.context(output)
    oldcfg,oldrows,oldm = ensemble.context(previous)
    if rows != oldrows or m != oldm:
        raise ValueError('OOF cache inputs or fold assignments differ')
    for key in ('baseline_seed','mbert_seed','versions'):
        if cfg[key] != oldcfg[key]:
            raise ValueError('OOF cache settings/environment differ: '+key)
    for name in ('ensemble_mbert.py','mbert_experiment.py','preprocessing.py'):
        if fair.digest(Path(__file__).parent/name) != fair.digest(previous/'code'/name):
            raise ValueError('OOF fitting/tokenizing code differs: '+name)
    # Compare exact package versions, rather than silently accepting a new torch.
    oldenv = (previous/'environment.txt').read_text(encoding='utf-8').splitlines()
    for name in ('torch','transformers','tokenizers','huggingface-hub','safetensors','numpy','scipy','scikit-learn'):
        if name+'=='+importlib.metadata.version(name) not in oldenv:
            raise ValueError('OOF package version differs: '+name)
    for name in ('model.safetensors','vocab.txt','config.json','tokenizer_config.json'):
        if fair.digest(Path(cfg['base'])/name) != fair.digest(Path(oldcfg['base'])/name):
            raise ValueError('OOF base/tokenizer mismatch')
    frozen = ensemble.load(previous/'freeze.json')['files']
    files = {name:h for name,h in frozen.items() if name.replace('\\','/').startswith('mbert-oof-')
             or name.replace('\\','/') in {'mbert-oof.npz','mbert-oof-timing.json'}}
    if not files:
        raise ValueError('No sealed OOF cache')
    for name,h in files.items():
        if fair.digest(previous/name) != h:
            raise ValueError('OOF cached artifact modified: '+name)
    train = np.array(m['partitions']['train'])
    mb = dict(np.load(previous/'mbert-oof.npz'))
    np.testing.assert_array_equal(mb['train_indices'],train)
    for k,fold in enumerate(m['inner_folds']):
        folder = previous/f'mbert-oof-{k}'
        c = ensemble.load(folder/'configuration.json')
        summary = ensemble.load(folder/'training-summary.json')
        np.testing.assert_array_equal(c['train_indices'],train[fold['train']])
        if c['checkpoint_validation_indices'] is not None or c['checkpoint_policy'] != 'fixed_epoch_2':
            raise ValueError('Cached OOF checkpoint used outer validation')
        expected = dict(seed=20261005,epochs=2,learning_rate=2e-5,weight_decay=.01,optimizer='Adafactor',
            microbatch=1,gradient_accumulation=8,wall_budget_seconds=2700)
        if any(c[key]!=value for key,value in expected.items()) or not summary['complete'] or summary['fixed_epoch'] != 2:
            raise ValueError('Cached OOF settings or completion mismatch')
        if any(h['validation_average_precision'] is not None for h in summary['history']):
            raise ValueError('Cached OOF used validation checkpoint selection')
        saved = dict(np.load(folder/'oof.npz'))
        np.testing.assert_array_equal(saved['indices'],train[fold['validation']])
        np.testing.assert_array_equal(saved['positions'],fold['validation'])
        np.testing.assert_array_equal(saved['probabilities'],mb['mbert'][fold['validation']])
    started = time.perf_counter()
    for k in range(5):
        shutil.copytree(previous/f'mbert-oof-{k}',output/f'mbert-oof-{k}')
    for name in ('mbert-oof.npz','mbert-oof-timing.json'):
        shutil.copy2(previous/name,output/name)
    for name,h in files.items():
        if fair.digest(output/name) != h:
            raise ValueError('OOF copied artifact integrity failure')
    write_json(output/'mbert-oof-reuse.json',dict(status='verified_reuse',source=str(previous.resolve()),
        identical_ordered_fitting_views_labels_groups_and_folds=True,versions_exact=True,fitting_code_exact=True,
        fixed_epochs_no_outer_validation_selection=True,source_frozen_files_verified=len(files),files=files,
        copy_and_integrity_seconds=time.perf_counter()-started,
        historical_measured_required_oof_seconds=ensemble.load(output/'mbert-oof-timing.json')['seconds'],
        newly_trained_oof_folds=0,historical_validation_or_test_predictions_read=False))
    print('Reused five verified identical mBERT OOF fits; no historical test predictions read.',flush=True)


def train(output, previous):
    ensemble.context(output)
    with (output/'training-started.json').open('x',encoding='utf-8') as f:
        json.dump(dict(started=time.time()),f)
    ensemble.train_classical(output)
    try:
        ensemble.train_mbert(output)
    except (RuntimeError,ImportError,ValueError,MemoryError) as error:
        ensemble.record_failure(output,'mbert',error)
        return
    try:
        reuse_mbert_oof(output,previous)
    except (RuntimeError,ImportError,ValueError,MemoryError,AssertionError) as error:
        # Invalid caches are rejected, not repaired or used as partial results.
        write_json(output/'mbert-cache-rejection.json',dict(reason=str(error),status='rejected'))
        if any((output/f'mbert-oof-{k}').exists() for k in range(5)):
            ensemble.record_failure(output,'mbert_stacking',error)
            return
        try:
            ensemble.train_mbert_oof(output)
        except (RuntimeError,ImportError,ValueError,MemoryError) as fitting_error:
            ensemble.record_failure(output,'mbert_stacking',fitting_error)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['audit','train'])
    p.add_argument('package',type=Path)
    p.add_argument('output',type=Path)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--base',type=Path,required=True)
    p.add_argument('--snapshots',type=Path,required=True)
    p.add_argument('--previous-ensemble',type=Path,default=ROOT/'research/data/ensemble-20261011/experiment-v1')
    a=p.parse_args()
    if a.command=='audit':
        audit(a.package,a.output,a.source,a.base,a.snapshots)
    else:
        train(a.output,a.previous_ensemble)


if __name__=='__main__':
    main()
