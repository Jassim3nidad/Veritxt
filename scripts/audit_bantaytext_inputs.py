"""Aggregate-only source/active-model audit. Never writes raw SMS to public reports."""
from collections import Counter
import csv
import json
from pathlib import Path
import sys
import zipfile
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research'))
from smishguard.bantaytext_workflow import digest,save,load,calculate_metrics
from smishguard.source_matching import SOURCES,parse_member
from smishguard.expanded_prepare import clean
from smishguard.convert_supplied import validate,portable


def main():
    current=ROOT/'research/data/newdata-20261013/experiment-v2'
    package=ROOT/'research/data/newdata-20261013/original/smishguard_dataset_2026-10-12'
    rows=list(csv.DictReader((package/'smishguard_dataset.csv').open(encoding='utf-8-sig',newline='')))
    prior=load(current/'new-package-audit.json')
    assert digest(package/'smishguard_dataset.csv') == prior['package_files']['smishguard_dataset.csv']
    sources={}
    for name,spec in SOURCES.items():
        with zipfile.ZipFile(ROOT/'research/data/source-evidence-pinned'/f'{name}.zip') as z:
            payload=z.read(spec['member'])
        import hashlib
        assert hashlib.sha256(payload).hexdigest() == spec['sha256']
        source=parse_member(payload,spec['member'])
        columns=sorted({k for r in source for k in r if isinstance(k,str)})
        text_field=next((k for k in ('text','message','Message','SMS','sms') if k in columns),None)
        label_fields=[k for k in columns if any(t in k.lower() for t in ('label','category','intent','type'))]
        # Source free-form categories can contain content; only known low-cardinality
        # categorical fields are summarized, never sender/URL or message values.
        labels={k:dict(Counter(r.get(k,'') for r in source)) for k in label_fields if len({r.get(k,'') for r in source})<=50}
        sources[name]=dict(**spec,records=len(source),columns=columns,
            missing={k:sum(not str(r.get(k) or '').strip() for r in source) for k in columns},original_categories=labels,
            malformed_overflow_rows=sum(None in r for r in source),
            text_field=text_field,placeholder_modified_records=sum(clean(r.get(text_field,''))!=r.get(text_field,'') for r in source) if text_field else None,
            empty_after_known_placeholder_clean=sum(not clean(r.get(text_field,'')) for r in source) if text_field else None,
            interpretation='Source taxonomy is not independently verified financial-smishing truth; package rule labels inherited')
    eligible=load(current/'dataset.json');ledger=load(current/'private-intake-ledger.json')
    eligible_ids={r['id'] for r in eligible}; ledger_by_id={r['id']:r for r in ledger}
    assert len(ledger_by_id)==len(rows)
    assert all(not ledger_by_id[i]['hold_reason'] for i in eligible_ids)
    assert eligible_ids=={r['id'] for r in ledger if not r['hold_reason']}
    lineage={source:dict(source_categories=dict(Counter(r['source_category'] for r in rows if r['source']==source)),
                        binary_mapping_by_original_category={cat:dict(Counter(r['label'] for r in rows if r['source']==source and r['source_category']==cat)) for cat in sorted({r['source_category'] for r in rows if r['source']==source})}) for source in sorted({r['source'] for r in rows})}
    # Supplied active weights are fitted on this entire original corpus. This
    # baseline is deliberately labeled resubstitution, never held-out accuracy.
    original=ROOT/'research/data/package-audit/original'
    model=validate(load(original/'model_export_final.json'))
    old=list(csv.DictReader((original/'smishguard_dataset.csv').open(encoding='utf-8-sig',newline='')))
    scores=[portable(model,r['message_text']) for r in old]
    y=[int(r['label']=='smishing') for r in old]
    threshold=float(np.nextafter(.5,1.0))
    active=dict(algorithm='Logistic Regression',features=len(model['vocabulary']),
        source_sha256=digest(original/'model_export_final.json'),
        asset_sha256=digest(ROOT/'android/app/src/development/assets/model.json'),
        original_dataset_sha256=digest(original/'smishguard_dataset.csv'),
        score='Uncalibrated sigmoid model score, not fraud probability',threshold=.5,comparison='strict_greater',
        baseline=calculate_metrics(y,scores,threshold),evaluation='Resubstitution on claimed full training corpus; unsuitable for model selection',
        reproducible_existing_comparison='Saved 17-model evaluation rechecked from finalized predictions before changes; output/bantaytext-existing-baseline-recheck.md',
        training_procedure='Supplied evidence reports C=2, liblinear, L2, balanced, max_features=5000, word(1,2). Exact original artifact reproduction and original environment unavailable; source export converted unchanged.',
        permissions='No INTERNET; SMS receiver/consent/report controls untouched. Original supplied automatic warnings already enabled by prior team decision; metadata still unapproved.',
        runtime='SmishGuardApp selects asset by build type; development uses ModelLoader/SuppliedDetector v2; ordinary debug has no fitted asset')
    protected=[ROOT/'android/app/src/main/AndroidManifest.xml',ROOT/'android/app/src/main/java/ph/smishguard/sms/IncomingSmsReceiver.kt',
        ROOT/'android/app/src/main/java/ph/smishguard/model/SuppliedDetector.kt',ROOT/'android/app/src/main/java/ph/smishguard/privacy/Reports.kt']
    protected+=list((ROOT/'android/app/src').glob('*/assets/model.json'))
    result=dict(package=dict(schema=prior['schema'],records=prior['included_records'],labels=prior['labels'],
        source_counts=prior['source_counts'],missing=prior['missing'],held=prior['held'],retained=prior['retained'],
        label_methods=prior['label_methods'],review=prior['review_workbook'],
        exact_duplicates=prior['duplicate_exact_text'],normalized_duplicate_records=prior['normalized_duplicate_records'],
        mixed_label_groups=prior['mixed_label_computed_groups'],raw_build_reproduced=False),
        pinned_sources=sources,source_category_mapping=lineage,active_model=active,
        protected_hashes={p.relative_to(ROOT).as_posix():digest(p) for p in protected},
        exposure=load(current/'exposure-summary.json'),
        limitations=['All eligible inputs previously exposed; final test cannot be claimed prospective',
            'Source/rule mappings already used content, sender and URL rules; source label prediction can reproduce rule shortcuts',
            'No complete independent review, reliable receipt timestamps, confirmed financial-only scope or unbiased target prevalence',
            'Raw-source build lacks some upstream files; do not invent its reproduction',
            'URLs masked upstream; host/shortener ablation unavailable. Sender not included in model input. No campaign identity confirmed'],
        notebook='New notebook uses existing authorized masked fitting view; holds flagged records and deduplicates before split')
    save(ROOT/'docs/bantaytext-input-audit-20261013.json',result)
    print('Aggregate source and active-model audit saved; no raw messages disclosed')


if __name__=='__main__':main()
