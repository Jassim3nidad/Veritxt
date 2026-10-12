"""Supplemental validation-only lineage/parity checks; never opens test predictions."""
import argparse
import json
from pathlib import Path
import pickle
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research'))
from smishguard.fair_compare import digest
from smishguard.parity import predict
from smishguard.train import margin,write_json


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def audit(run):
    cfg=load(run/'configuration.json')
    source=Path(cfg['source'])
    rows=load(source/'dataset.json')
    manifest=load(source/'splits.json')
    ledger=load(source/'private-intake-ledger.json')
    index={r['id']:r for r in ledger}
    if len(index)!=len(ledger) or {r['label'] for r in ledger}!={'ham','smishing'}:
        raise ValueError('Invalid source ledger labels/IDs')
    for r in rows:
        original=index[r['id']]
        if r['label']!=int(original['label']=='smishing') or r['content_sha256']!=original['original_sha256'] or original['hold_reason'] is not None:
            raise ValueError('Label/content lineage mismatch')
    write_json(run/'label-lineage-audit.json',dict(records=len(rows),inherited_binary_mapping_exact=True,
        original_content_fingerprints_exact=True,held_records_admitted=0,
        independent_label_review='pending; consistency is not ground-truth confirmation'))
    texts=[rows[i]['text_redacted'] for i in manifest['partitions']['validation']]
    result={}
    baseline_reproduction={}
    for name in ('lr','nb','svm'):
        a=pickle.loads((source/name/'research-model.pkl').read_bytes())
        new=pickle.loads((run/'classical'/(name+'.pkl')).read_bytes())
        model=new['pipeline']['classifier']
        if a['model'].get_params()!=model.get_params():
            raise ValueError('Baseline estimator settings changed')
        if a['vectorizer'].get_params()!=new['pipeline']['tfidf'].get_params():
            raise ValueError('Baseline feature settings changed')
        for attr in ('classes_','coef_','intercept_','feature_log_prob_','class_log_prior_'):
            if hasattr(a['model'],attr):
                np.testing.assert_array_equal(getattr(a['model'],attr),getattr(model,attr))
        np.testing.assert_array_equal(a['calibrator'].coef_,new['calibrator'].coef_)
        np.testing.assert_array_equal(a['calibrator'].intercept_,new['calibrator'].intercept_)
        if a['threshold']!=new['threshold']:
            raise ValueError('Baseline threshold changed')
        baseline_reproduction[name]=dict(estimator_settings_identical=True,feature_settings_identical=True,
            fitted_parameters_identical=True,calibrator_parameters_identical=True,threshold_identical=True)
        export=load(source/name/'model.json')
        p=a['calibrator'].predict_proba(margin(a['model'],a['vectorizer'].transform(texts)).reshape(-1,1))[:,1]
        q=np.array([predict(export,t)[0] for t in texts])
        same=bool(np.array_equal(p>=a['threshold'],q>=a['threshold']))
        error=float(np.max(abs(p-q)))
        if error>1e-10 or not same:
            raise ValueError('Export parity failure')
        result[name]=dict(max_export_probability_error=error,decisions_equal=same)
    write_json(run/'validation-export-audit.json',result)
    write_json(run/'classical-reproduction-audit.json',baseline_reproduction)
    if (run/'mbert/calibrator.pkl').exists():
        old=load(source/'mbert/configuration.json')
        new=load(run/'mbert/configuration.json')
        keys=['seed','epochs','learning_rate','weight_decay','optimizer','microbatch','gradient_accumulation','max_length','wall_budget_seconds']
        same={k:old[k]==new[k] for k in keys}
        if not all(same.values()):
            raise ValueError('Baseline mBERT settings changed')
        write_json(run/'mbert-settings-audit.json',dict(preserved_settings={k:old[k] for k in keys},exact_match=same,
            model_id=old['model_id'],revision=old['revision'],
            base_weights_sha256=digest(Path(cfg['base'])/'model.safetensors'),tokenizer_vocab_sha256=digest(Path(cfg['base'])/'vocab.txt')))
        a=load(run/'mbert/training-summary.json')
        b=load(source/'mbert/training-summary.json')
        cal=pickle.loads((run/'mbert/calibrator.pkl').read_bytes())
        oldcal=load(source/'mbert/freeze.json')['calibration']
        h=digest(run/'mbert'/a['selected_path']/'model.safetensors')
        write_json(run/'mbert-reproduction-audit.json',dict(selected_epoch_equal=a['selected_epoch']==b['selected_epoch'],
            weights_sha256_identical=h==digest(source/'mbert/selected/model.safetensors'),weights_sha256=h,
            validation_ap_equal=all(x['validation_average_precision']==y['validation_average_precision'] for x,y in zip(a['history'],b['history'])),
            calibrator_coefficient_difference=float(cal.coef_[0,0]-oldcal['a']),calibrator_intercept_difference=float(cal.intercept_[0]-oldcal['b'])))
    print('Supplemental lineage and validation export checks passed.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('run',type=Path)
    a=p.parse_args()
    audit(a.run)
