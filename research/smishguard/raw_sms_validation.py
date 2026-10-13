"""Validate frozen SVM raw-input adaptation; no fitting or parameter changes."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import pickle
import re
import shutil
import sys
import unicodedata
import zipfile
import numpy as np
from . import bantaytext_workflow as w
from .expanded_prepare import clean
from .mbert_experiment import redacted_case_view
from .source_matching import SOURCES, parse_member

ROOT=Path(__file__).resolve().parents[2]
PROTOCOL=ROOT/'docs/bantaytext-raw-sms-protocol-20261013.md'


def raw_view(text):
    if not isinstance(text,str):raise ValueError('SMS text must be a string')
    return clean(redacted_case_view(clean(text)))


def adapter_contract():
    if unicodedata.unidata_version!='15.0.0':raise ValueError('Python Unicode 15.0.0 required')
    return dict(version='case-preserving-mask-v1',order=['clean','url','email','ascii_digits','clean'],
        placeholder_pattern=r'<(?:REAL NAME|NAME|REDACTED|BLANK|n)>|\[name redacted\]|\(full name\)|\[my name\]',
        url_pattern=r'(?:https?://|www\.)[^\s<>]+',url_case='ascii_insensitive',
        email_pattern=r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
        digit_pattern='[0-9]+',whitespace_codepoints=[cp for cp in range(sys.maxunicode+1) if chr(cp).isspace()],
        unicode_version='15.0.0',lowercase=False)


PROBES=[
    'Your OTP is 123456. Do not share it.',
    'GCash transaction 1234 completed. Check your official app.',
    'BDO statement available sa app. Account ending 4321.',
    'paki verify nyo ninyo na po at HTTPS://example.invalid/synthetic?otp=123',
    'Contact fictional@example.invalid about your account 1234.',
    'http://example.invalid/hello?otp=123<>account verify',
    'WWW.EXAMPLE.INVALID/synthetic\nYour OTP: 123456',
    'httpſ://example.invalid/synthetic 123',
    'http://example.invalid/a\u00a0verify account',
    'email fictional@example.invalid and www.example.invalid/synthetic',
    ' , <REAL NAME> Your OTP is 123456. , ',
    '<NAME> [name redacted] (full name) [my name] <REDACTED> <BLANK> <n> verify account',
    '<BLANK> kumusta po',
    '\u0085Hello\u001cpo\u2003kumusta\u2028account\u202fverify',
    'Arabic digits ١٢٣٤ and ASCII digits 1234',
    'Account_Verify OTP 12',
    'verify account at example.invalid/synthetic',
    'verify hxxps[:]//example[.]invalid/synthetic',
    'A I x ñ café İ ΟΣ ΟΣΑ Straße 𐐀𐐨',
    'account the verify',
    'account qzxvunknownword verify',
    'zzurlzz zzemailzz zznumberzz account',
    '', '   ', '<REAL NAME>', 'qzxvunknownword zzzqqq', 'asdfghjkl',
    '123456', 'https://example.invalid/synthetic', '\ud800',
    'x'*10001,
    'http://example.invalid/a\u180Everify account',
    'HtTpS://example.invalid/a\u200Bverify account',
]


def prepare(run,validation,output):
    if output.exists():raise ValueError('New private output directory required')
    output.mkdir(parents=True);parity=output/'parity';parity.mkdir();assets=parity/'android-test-assets';assets.mkdir()
    previous=w.load(validation/'snapshot.json');candidate=run/'grouped/svm-C-10.0/pipeline.pkl'
    if w.digest(candidate)!=previous['candidate_sha256']:raise ValueError('Frozen candidate changed')
    if w.digest(run/'dataset.json')!=previous['dataset_sha256']:raise ValueError('Frozen data changed')
    artifact=pickle.loads(candidate.read_bytes());rows=w.load(run/'dataset.json')
    ledger={r['id']:r for r in w.load(ROOT/'research/data/newdata-20261013/experiment-v2/private-intake-ledger.json')}
    sources={};source_hashes={}
    for name,spec in SOURCES.items():
        with zipfile.ZipFile(ROOT/'research/data/source-evidence-pinned'/f'{name}.zip') as z:payload=z.read(spec['member'])
        sha=hashlib.sha256(payload).hexdigest()
        if sha!=spec['sha256']:raise ValueError('Pinned source changed')
        sources[name]=parse_member(payload,spec['member']);source_hashes[name]=sha
    replayed=[];source_counts={name:0 for name in sources}
    for row in rows:
        item=ledger[row['id']]
        if item['hold_reason']:raise ValueError('Held source row found in frozen corpus')
        match=item['source_match'];raw=str(sources[match['source']][match['source_row']]['text'])
        view=raw_view(raw)
        if view!=row['text']:raise ValueError('Original-source preprocessing replay mismatch; content withheld')
        replayed.append(view);source_counts[match['source']]+=1
    expected=w.score(artifact,[r['text'] for r in rows]);actual=w.score(artifact,replayed)
    assert np.max(np.abs(actual-expected))<=1e-10
    contract=adapter_contract();w.save(parity/'raw-adapter.json',contract)
    views=[raw_view(t) for t in PROBES];v=artifact['pipe']['tfidf'];x=v.transform(views);scores=w.score(artifact,views)
    cases=[]
    for i,(raw,view) in enumerate(zip(PROBES,views)):
        features=x.getrow(i)
        cases.append(dict(raw=raw,view=view,score=float(scores[i]),suspicious=bool(scores[i]>=artifact['threshold']),
            terms=v.build_analyzer()(view),features={str(k):float(value) for k,value in zip(features.indices,features.data)},
            must_abstain=i in (22,23,24,25,26,27,28,29),overlong=i==30))
    (parity/'raw-cases.json').write_text(json.dumps(cases,ensure_ascii=True,allow_nan=False),encoding='utf-8')
    for name in ('selected-model.json','selected-cases.json','model.json','cases.json','active-model.json','active-cases.json'):
        shutil.copyfile(validation/'parity'/name,parity/name)
    for name in ('selected-svm-model.json','selected-svm-cases.json'):
        shutil.copyfile(validation/'parity/android-test-assets'/name,assets/name)
    shutil.copyfile(parity/'raw-adapter.json',assets/'raw-sms-adapter.json')
    shutil.copyfile(parity/'raw-cases.json',assets/'raw-sms-cases.json')
    result=dict(records_replayed=len(rows),source_counts=source_counts,source_hashes=source_hashes,
        candidate_sha256=w.digest(candidate),selected_export_sha256=w.digest(parity/'selected-model.json'),
        dataset_sha256=w.digest(run/'dataset.json'),python_score_max_error=float(np.max(np.abs(actual-expected))),
        raw_probe_cases=len(cases),adapter_sha256=w.digest(parity/'raw-adapter.json'),cases_sha256=w.digest(parity/'raw-cases.json'),
        protocol_sha256=w.digest(PROTOCOL),training_view='clean(mask(clean(raw)))',no_retraining=True,
        historical_label_status='Inherited source/rule labels; independent human review unavailable, limitation documented',
        physical_phone=dict(status='user_reported_complete',report_date='2026-10-13',
            tested_apk_model='not specified',measurement_details='not supplied; no values invented'),
        release='Raw preprocessing under engineering verification; original selected model/source-transfer evidence unchanged')
    w.save(output/'preparation.json',result);shutil.copyfile(PROTOCOL,output/'protocol.md')
    print('Exact raw-source replay:',len(rows),'records; synthetic raw probes:',len(cases),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('validation',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();prepare(a.run,a.validation,a.output)
