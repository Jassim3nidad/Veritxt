"""Restricted, retrospective development experiment; never clears thesis intake."""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import pickle
import re
import zipfile

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score

from . import fair_compare as fair
from .data import template_groups, split_rows
from .evaluate import metrics
from .linear_export import export_linear
from .parity import predict
from .preprocessing import normalize, tokens
from .review_packets import private_output
from .source_matching import SOURCES, parse_member, indexes, match
from .train import margin, write_json
from .uncertainty import cluster_intervals
from .vocabulary_policy import screen

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT/'docs/preliminary-comparison-protocol-20261001.md'
SUPPORTED = ('tagalog','marketing')
PROBES = ['Hello po', 'Bayad na po', 'Your payment is received.',
          'Your account is suspended. Verify your password at https://account.example now.',
          '', 'qwerty', 'xqzvplmkj', '!!!', 'https://example.invalid', 'HELLO hello account',
          'Walang link dito. Pakisuri ang account.', '🌟 ñ Á İ hello', 'bayad '*1000]
LATENCY_PROBES = PROBES[:4]
LINKS = re.compile(r'(?i)(?:https?://|www\.)\S+|\b[\w-]+(?:\.[\w-]+)+[/\w?=&%#.-]*')
PERSON = re.compile(r'\b(?:hi|dear|hello|mr|ms|mrs)\.?\s+[A-Z][a-z]+|\b(?:received by|released to|picked up by|delivered to)\s+\S+',re.I)
OBFUSCATED = re.compile(r'hxxps?[:\[]|\[dot\]|\(dot\)|\[\.\]',re.I)


def assessable(text, vocabulary):
    if len(text.encode('utf-16-le'))//2 > 10000: return False
    for word in tokens(LINKS.sub(' ',text)):
        if (len(word)<2 or not word.isalpha() or (len(word)>=4 and len(set(word))==1)
                or (len(word)>=4 and any(word in row or word in row[::-1] for row in ('qwertyuiop','asdfghjkl','zxcvbnm')))):
            continue
        if word in vocabulary: return True
    return False


def deployment_metrics(texts,y,scores,threshold,vocabulary):
    keep=np.array([assessable(t,vocabulary) for t in texts]); y=np.asarray(y);scores=np.asarray(scores)
    return dict(records=len(y),scored=int(keep.sum()),abstained=int((~keep).sum()),coverage=float(keep.mean()),
        abstained_labels=dict(ham=int(((~keep)&(y==0)).sum()),smishing=int(((~keep)&(y==1)).sum())),
        conditional_metrics=metrics(y[keep],scores[keep],threshold) if keep.any() else None,
        interpretation='Abstentions excluded from conditional metrics, never counted as correct negatives')


def prepare(primary,snapshots,output):
    for p in (primary,snapshots,output): private_output(p)
    if output.exists(): raise ValueError('Preserve existing experiment; use a new directory')
    output.mkdir(parents=True)
    source_rows={}; source_indexes={}
    for name in SUPPORTED:
        spec=SOURCES[name]
        with zipfile.ZipFile(snapshots/(name+'.zip')) as archive: data=archive.read(spec['member'])
        if hashlib.sha256(data).hexdigest() != spec['sha256']: raise ValueError('Source snapshot changed')
        source_rows[name]=parse_member(data,spec['member']);source_indexes[name]=indexes(source_rows[name])
    with primary.open(encoding='utf-8-sig',newline='') as stream: original=list(csv.DictReader(stream))
    held=Counter(); candidates=[]; ledger=[]
    for r in original:
        hits={name:match(r['message_text'],source_indexes[name]) for name in SUPPORTED}
        hits={k:v for k,v in hits.items() if v}
        if any(word in r['source'].lower() for word in ('personal','facebook','reddit','uci')):
            held['personal_social_or_uci']+=1;continue
        if not hits: held['no_supported_source_match']+=1;continue
        name=next(iter(hits)); source_row=hits[name]['candidate_rows'][0]-2
        text=str(source_rows[name][source_row]['text'])
        # Use licensed snapshot text, not an asserted original acquisition chain.
        if PERSON.search(text) or OBFUSCATED.search(text): held['automated_privacy_hold']+=1;continue
        cleaned=normalize(text)
        if not cleaned or len(cleaned)>10000: held['empty_or_overlong']+=1;continue
        if r['label'] not in ('ham','smishing'): held['unsupported_label']+=1;continue
        candidates.append(dict(id=r['id'],text_redacted=cleaned,label=str(int(r['label']=='smishing')),
                               source_matches=hits,label_status='inherited_unconfirmed',exposure='previously_used'))
    duplicate=defaultdict(list)
    for r in candidates: duplicate[r['text_redacted']].append(r)
    rows=[]
    for members in duplicate.values():
        if len({r['label'] for r in members})>1: held['conflicting_normalized_labels']+=len(members);continue
        ordered=sorted(members,key=lambda r:r['id']);rows.append(ordered[0]);held['normalized_duplicates']+=len(members)-1
    rows.sort(key=lambda r:r['id'])
    write_json(output/'dataset.json',rows)
    groups=np.asarray(template_groups(rows));splits=split_rows(rows,groups,'group',fair.SEED)
    train=splits['train']; y=np.array([int(rows[i]['label']) for i in train])
    folds=fair.training_folds(y,groups[train])
    assert all(not (set(groups[splits[a]]) & set(groups[splits[b]])) for a in splits for b in splits if a<b)
    write_json(output/'splits.json',dict(partitions=splits,groups=groups.tolist(),
        inner_folds=[dict(train=a.tolist(),validation=b.tolist()) for a,b in folds]))
    support={part:dict(records=len(ids),groups=len(set(groups[ids])),ham=sum(rows[i]['label']=='0' for i in ids),
        smishing=sum(rows[i]['label']=='1' for i in ids)) for part,ids in splits.items()}
    write_json(output/'preparation.json',dict(protocol_sha256=fair.digest(PROTOCOL),code_sha256=fair.digest(Path(__file__)),
        primary_sha256=fair.digest(primary),dataset_sha256=fair.digest(output/'dataset.json'),split_sha256=fair.digest(output/'splits.json'),
        source_evidence_sha256=fair.digest(ROOT/'docs/source-match-summary.json'),source_credits={name:SOURCES[name] for name in SUPPORTED},
        original_records=len(original),retained_records=len(rows),held=dict(held),partition_support=support,
        label_status='inherited labels, not independently confirmed; user-authorized preliminary development only',
        permission_basis='Direct text from hash-pinned CC0 / CC BY source snapshots; attribution retained; no original acquisition or donor-consent attestation',
        human_redaction='pending; automated minimization only',history='previously_used; internal retrospective test',seed=fair.SEED))
    print('Supported subset prepared; private records retained, aggregate support:',support,flush=True)


def check_preparation(output):
    prep=json.loads((output/'preparation.json').read_text())
    for path,key in ((PROTOCOL,'protocol_sha256'),(Path(__file__),'code_sha256'),(output/'dataset.json','dataset_sha256'),(output/'splits.json','split_sha256')):
        if fair.digest(path)!=prep[key]: raise ValueError('Prepared protocol/code/data/split changed')
    return prep


def train(output):
    private_output(output);prep=check_preparation(output)
    with (output/'training-started.json').open('x') as stream:json.dump({'preparation_sha256':fair.digest(output/'preparation.json')},stream)
    rows=json.loads((output/'dataset.json').read_text());manifest=json.loads((output/'splits.json').read_text())
    splits=manifest['partitions']; train_ids=splits['train']
    texts=[rows[i]['text_redacted'] for i in train_ids];y=np.array([int(rows[i]['label']) for i in train_ids])
    folds=[(np.array(f['train']),np.array(f['validation'])) for f in manifest['inner_folds']]
    validation={}; hashes={}
    for name in fair.NAMES:
        pipe,trials,chosen=fair.tune(texts,y,folds,name);v=pipe['tfidf'];model=pipe['classifier']
        def part(key):
            ids=splits[key];return v.transform([rows[i]['text_redacted'] for i in ids]),np.array([int(rows[i]['label']) for i in ids])
        xc,yc=part('calibration');cal=LogisticRegression(random_state=fair.SEED).fit(margin(model,xc).reshape(-1,1),yc)
        xv,yv=part('validation');scores=cal.predict_proba(margin(model,xv).reshape(-1,1))[:,1]
        threshold=float(max(np.linspace(.05,.95,91),key=lambda t:(f1_score(yv,scores>=t),t)))
        export=export_linear(v,model,cal,threshold,synthetic=False)
        export.update(model_version=f'prelim-20261001-{name}-{prep["dataset_sha256"][:8]}',
            evaluation_status='preliminary_retrospective',label_status='inherited_unconfirmed',
            protocol_sha256=prep['protocol_sha256'],dataset_sha256=prep['dataset_sha256'],split_sha256=prep['split_sha256'],
            positive_class='suspicious',threshold_comparison='greater_or_equal',score_transform='fitted_sigmoid',
            calibration_fit_partition='calibration',threshold_fit_partition='validation',automatic_warnings_approved=False,
            preprocessing=dict(version='sg-ascii-v1',lowercase='ASCII A-Z only',term_frequency='raw',ngram_range=[1,1],normalization='l2',idf='fitted training only; smooth_idf=true'))
        if screen(export['vocabulary'])['identifier_pattern_features']: raise ValueError('Model content screen failed')
        run=output/name;run.mkdir()
        write_json(run/'model.json',export)
        (run/'research-model.pkl').write_bytes(pickle.dumps(dict(vectorizer=v,model=model,calibrator=cal,threshold=threshold,condition='deployment')))
        validation[name]=dict(chosen_parameter=chosen,trials=trials,threshold=threshold,validation_f1=float(f1_score(yv,scores>=threshold)),
            model_version=export['model_version'],content_screen=screen(export['vocabulary']),human_review='not_recorded')
        for file in ('model.json','research-model.pkl'): hashes[f'{name}/{file}']=fair.digest(run/file)
    write_json(output/'freeze.json',dict(preparation=prep,validation=validation,files=hashes,final_test_opened=False,
        protocol_sha256=prep['protocol_sha256'],dataset_sha256=prep['dataset_sha256'],seed=fair.SEED))
    print('All three candidates frozen. Internal test not yet opened.',flush=True)


def evaluate(output):
    private_output(output);prep=check_preparation(output)
    freeze=json.loads((output/'freeze.json').read_text())
    for file,expected in freeze['files'].items():
        if fair.digest(output/file)!=expected:raise ValueError('Frozen model changed')
    with (output/'internal-test-started.json').open('x') as stream:json.dump({'freeze_sha256':fair.digest(output/'freeze.json')},stream)
    rows=json.loads((output/'dataset.json').read_text());m=json.loads((output/'splits.json').read_text());ids=m['partitions']['test']
    texts=[rows[i]['text_redacted'] for i in ids];y=np.array([int(rows[i]['label']) for i in ids]);groups=np.array(m['groups'])[ids]
    results={};predictions={}
    for name in fair.NAMES:
        run=output/name;export=json.loads((run/'model.json').read_text());artifact=pickle.loads((run/'research-model.pkl').read_bytes())
        # Only hash-bound artifacts generated above; never deserialize supplied pickles.
        x=artifact['vectorizer'].transform(texts);raw=margin(artifact['model'],x);p=artifact['calibrator'].predict_proba(raw.reshape(-1,1))[:,1]
        t=artifact['threshold'];predictions[name]=p>=t
        result=metrics(y,p,t);result.update(deployment=deployment_metrics(texts,y,p,t,set(export['vocabulary'])),
            model_json_bytes=(run/'model.json').stat().st_size,full_pipeline_pickle_bytes=(run/'research-model.pkl').stat().st_size,
            confidence_intervals=cluster_intervals(y,p,groups,t,seed=fair.SEED,repetitions=2000) if fair.adequate_groups(y,groups) else {'status':'insufficient groups','intervals':None})
        results[name]=result
        cases=[];alltexts=PROBES+texts
        xp=artifact['vectorizer'].transform([normalize(text) for text in alltexts]);margins=margin(artifact['model'],xp)
        expected=artifact['calibrator'].predict_proba(margins.reshape(-1,1))[:,1]
        for text,score,rawmargin in zip(alltexts,expected,margins):
            got,label=predict(export,text)
            if abs(got-score)>1e-10:raise ValueError('Full pipeline Python/export parity failed')
            cases.append(dict(text=text,normalized=normalize(text),score=float(score),margin=float(rawmargin),suspicious=label,assessable=assessable(text,set(export['vocabulary']))))
        parity=run/'parity';parity.mkdir();(parity/'model.json').write_bytes((run/'model.json').read_bytes());write_json(parity/'cases.json',cases)
        assets=parity/'android-test-assets';assets.mkdir();write_json(assets/'comparison-private-cases.json',cases)
        write_json(run/'parity-summary.json',dict(cases=len(cases),model_sha256=fair.digest(run/'model.json'),cases_sha256=fair.digest(parity/'cases.json'),
            python_max_error=max(abs(predict(export,text)[0]-float(score)) for text,score in zip(alltexts,expected))))
        version=export['model_version'];modelhash=fair.digest(run/'model.json')
        (run/'review.properties').write_text(f'algorithm={name}\nmodelVersion={version}\nsha256={modelhash}\nreviewKind=automated-pattern-screen\nhumanReview=not_recorded\nreviewReference=preliminary-comparison-20261001\nprotocolSha256={prep["protocol_sha256"]}\n')
    write_json(output/'comparison-aggregate.json',dict(status='preliminary retrospective internal evaluation; inherited labels unconfirmed',
        results=results,test_records=len(y),test_groups=len(set(groups)),paired_f1=fair.paired_f1_intervals(y,predictions,groups),
        highest_observed_f1=[name for name in fair.NAMES if results[name]['f1']==max(r['f1'] for r in results.values())],
        freeze_sha256=fair.digest(output/'freeze.json'),preparation=prep,validation=freeze['validation'],physical_device='pending',prospective_test='not available'))
    print('Internal comparison and actual-model parity fixtures recorded privately; no retuning.',flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('prepare');p.add_argument('primary',type=Path);p.add_argument('snapshots',type=Path);p.add_argument('output',type=Path)
    for name in ('train','evaluate'):sub.add_parser(name).add_argument('output',type=Path)
    args=parser.parse_args()
    if args.command=='prepare':prepare(args.primary,args.snapshots,args.output)
    elif args.command=='train':train(args.output)
    else:evaluate(args.output)

if __name__=='__main__':main()
