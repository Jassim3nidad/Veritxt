"""Further validation of frozen BantayText candidate; no deployment or retuning.

Private fit/prediction artifacts stay ignored; public reports contain aggregates.
"""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import json
import importlib.metadata
import math
from pathlib import Path
import pickle
import re
import shutil
import time
import zipfile

import numpy as np
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
from . import bantaytext_workflow as w
from .convert_supplied import unicode_contract

ROOT=Path(__file__).resolve().parents[2]
SEED=20261013
PROTOCOL=ROOT/'docs/bantaytext-predeployment-protocol-20261013.md'


def now():return datetime.now(timezone.utc).isoformat()


def snapshot(run,archive,output):
    if output.exists():raise ValueError('Use a new validation directory')
    output.mkdir(parents=True)
    preservation=w.load(ROOT/'research/data/newdata-20261013/experiment-v2/new-package-preservation.json')
    if w.digest(archive)!=preservation['zip_sha256']:
        raise ValueError('Changed package requires a new source/privacy audit, not reuse of old validation')
    import hashlib
    with zipfile.ZipFile(archive) as z:
        members={Path(name).name:hashlib.sha256(z.read(name)).hexdigest() for name in z.namelist() if not name.endswith('/')}
    if members!=preservation['original_files']:raise ValueError('Original archive member mismatch')
    cfg=w.load(run/'configuration.json');splits=w.load(run/'splits.json');rows=w.load(run/'dataset.json')
    if any(importlib.metadata.version(name)!=version for name,version in cfg['versions'].items()):
        raise ValueError('Use the frozen candidate library versions for validation')
    if w.digest(run/'dataset.json')!=cfg['cleaned_sha256'] or w.digest(run/'splits.json')!=cfg['split_sha256']:
        raise ValueError('Dataset/split changed')
    selected=w.load(run/'improvement-freeze.json')
    if selected['selected']['grouped']!='svm-C-10.0':raise ValueError('Unexpected candidate')
    candidate=run/'grouped/svm-C-10.0/pipeline.pkl'
    frozen_files={name.replace('\\','/'):sha for name,sha in selected['files'].items()}
    if w.digest(candidate)!=frozen_files['grouped/svm-C-10.0/pipeline.pkl']:
        raise ValueError('Selected fit changed')
    shutil.copyfile(candidate,output/'selected-pipeline.pkl')
    shutil.copyfile(PROTOCOL,output/'protocol.md')
    w.save(output/'snapshot.json',dict(created_utc=now(),protocol_sha256=w.digest(PROTOCOL),
        archive_sha256=w.digest(archive),archive_identical_to_previous=True,members_verified=len(members),
        dataset_sha256=w.digest(run/'dataset.json'),split_sha256=w.digest(run/'splits.json'),
        candidate_sha256=w.digest(candidate),threshold=.37,
        previous_review=w.load(ROOT/'research/data/validation-20261006/review/coordinator/blank-agreement-final/final-summary.json'),
        package_review=w.load(ROOT/'research/data/newdata-20261013/experiment-v2/new-package-audit.json')['review_workbook'],
        prospective_intake_records=sum(1 for _ in csv.DictReader((ROOT/'research/data/validation-20261006/prospective/intake.csv').open(encoding='utf-8-sig'))),
        deployment='Not approved; unchanged active model retained',versions=cfg['versions']))
    return rows,np.array(splits['groups']),splits,pickle.loads(candidate.read_bytes())


def decision_metrics(y,pred):
    y=np.asarray(y);pred=np.asarray(pred)
    tp=int(np.sum((y==1)&pred));fp=int(np.sum((y==0)&pred));tn=int(np.sum((y==0)&~pred));fn=int(np.sum((y==1)&~pred))
    precision=tp/(tp+fp) if tp+fp else 0;recall=tp/(tp+fn) if tp+fn else 0
    return dict(precision=precision,recall=recall,f1=2*precision*recall/(precision+recall) if precision+recall else 0,
        false_positive_rate=fp/(fp+tn) if fp+tn else None,false_negative_rate=fn/(fn+tp) if fn+tp else None,
        confusion=dict(tn=tn,fp=fp,fn=fn,tp=tp))


def intervals(y,candidate,baseline,groups,repetitions=2000):
    rng=np.random.default_rng(SEED);unique=np.unique(groups)
    members={g:np.flatnonzero(groups==g) for g in unique};samples={k:[] for k in ('precision','recall','f1','false_positive_rate','false_negative_rate')};deltas=[]
    for _ in range(repetitions):
        ii=np.concatenate([members[g] for g in rng.choice(unique,len(unique),replace=True)])
        if len(set(y[ii]))<2:continue
        chosen=decision_metrics(y[ii],candidate[ii]);standard=decision_metrics(y[ii],baseline[ii])
        for k in samples:samples[k].append(chosen[k])
        deltas.append(chosen['f1']-standard['f1'])
    samples['paired_f1_delta_vs_baseline']=deltas
    return dict(method='Paired whole-template percentile bootstrap, fixed models/thresholds; no selection/training/label uncertainty',
        seed=SEED,repetitions=repetitions,groups=len(unique),
        intervals={k:dict(low=float(np.quantile(v,.025)),high=float(np.quantile(v,.975)),valid_draws=len(v)) for k,v in samples.items()})


def nested_sources(rows,groups,output):
    result={};configs=[dict(algorithm=a,features='word',ngrams=[1,2],stop_words='english',
        alpha=.1,C=10.0,class_weight=None,calibrated=a=='svm') for a in ('nb','lr','svm')]
    for source in sorted({r['source'] for r in rows}):
        test=np.array([i for i,r in enumerate(rows) if r['source']==source]);held=set(groups[test])
        eligible=np.array([i for i,r in enumerate(rows) if r['source']!=source and groups[i] not in held])
        y=np.array([rows[i]['label'] for i in eligible])
        a,b=next(StratifiedGroupKFold(n_splits=5,shuffle=True,random_state=SEED).split(eligible,y,groups[eligible]))
        train=eligible[a].tolist();val=eligible[b].tolist();assert not set(groups[train])&set(groups[val])
        assert not set(groups[train])&held and not set(groups[val])&held
        folder=output/'source-heldout'/source;folder.mkdir(parents=True)
        w.save(folder/'partitions.json',dict(train=train,validation=val,test=test.tolist(),outer_related_records_purged=len(rows)-len(test)-len(eligible)))
        result[source]={}
        for spec in configs:
            artifact=w.fit_candidate(rows,groups,train,spec)
            pv=w.score(artifact,[rows[i]['text'] for i in val]);yv=[rows[i]['label'] for i in val]
            threshold,trials,feasible=w.threshold_policy(yv,pv)
            artifact['threshold']=threshold
            path=folder/(spec['algorithm']+'-pipeline.pkl');path.write_bytes(pickle.dumps(artifact))
            # Outer labels/scores do not enter calibration/threshold selection.
            w.save(folder/(spec['algorithm']+'-freeze.json'),dict(pipeline_sha256=w.digest(path),threshold=threshold,
                validation=w.calculate_metrics(yv,pv,threshold),criterion_met=feasible,outer_test_opened=False))
            pp=w.score(artifact,[rows[i]['text'] for i in test]);yt=[rows[i]['label'] for i in test]
            w.save(folder/(spec['algorithm']+'-predictions.json'),dict(indices=test.tolist(),labels=yt,scores=pp.tolist()))
            result[source][spec['algorithm']]=dict(train=w.class_counts([rows[i] for i in train]),validation=w.class_counts([rows[i] for i in val]),
                test=w.class_counts([rows[i] for i in test]),threshold=threshold,validation_criterion_met=feasible,
                validation_metrics=w.calculate_metrics(yv,pv,threshold),test_metrics=w.calculate_metrics(yt,pp,threshold),
                note='Source-complement-only calibration/operating threshold. Fixed historical settings: retrospective, not unbiased model-selection validation')
            print('Source held out:',source,spec['algorithm'],'F1',round(result[source][spec['algorithm']]['test_metrics']['f1'],4),flush=True)
    w.save(output/'nested-source-results.json',result);return result


def wilson(successes,n):
    if not n:return None
    z=1.959963984540054;p=successes/n;den=1+z*z/n
    center=(p+z*z/(2*n))/den;half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return dict(low=max(0,center-half),high=min(1,center+half),method='95% Wilson interval; inherited labels, sample selection/group correlation not covered')


def stress(artifact,rows,ids):
    texts=[rows[i]['text'] for i in ids];p=w.score(artifact,texts);threshold=artifact['threshold']
    transforms=dict(uppercase=lambda t:t.upper(),whitespace=lambda t:re.sub(r'\s+',' \n\t ',t),
        punctuation=lambda t:re.sub(r'\s+',' ... ',t),remove_url_marker=lambda t:re.sub(r'\bzzurlzz\b',' ',t),
        add_taglish=lambda t:t+' po paki nyo ninyo na',
        bank_obfuscation=lambda t:re.sub(r'\b(?:gcash|bdo|bpi|maya)\b',lambda m:' '.join(m[0]),t,flags=re.I))
    results={}
    for name,change in transforms.items():
        pp=w.score(artifact,[change(t) for t in texts]);delta=np.abs(pp-p)
        results[name]=dict(records=len(texts),changed_decisions=int(np.sum((pp>=threshold)!=(p>=threshold))),
            mean_absolute_score_change=float(delta.mean()),maximum_absolute_score_change=float(delta.max()),all_finite=bool(np.isfinite(pp).all()),
            interpretation='Fixed-prediction stress; altered content is not new labeled ground truth')
    # Whitespace only must leave sklearn token features intact; Unicode uppercase
    # can change sharp-s expansion/contextual sigma, so it is measured, not asserted.
    if results['whitespace']['maximum_absolute_score_change']>1e-10:raise ValueError('Unexpected whitespace dependence')
    return results


def export_selected(artifact,rows,ids,output,reference_parity=None):
    import unicodedata
    if unicodedata.unidata_version!='15.0.0':raise ValueError('Use Python 3.12 / Unicode 15.0.0')
    pipe=artifact['pipe'];v=pipe['tfidf'];model=pipe['classifier'];cal=artifact['calibrator']
    assert v.analyzer=='word' and v.ngram_range==(1,2) and v.norm=='l2' and not v.sublinear_tf
    assert model.classes_.tolist()==[0,1] and cal.classes_.tolist()==[0,1]
    assert v.token_pattern==r'(?u)\b\w\w+\b' and v.stop_words=='english'
    exported=dict(schema_version=6,research_contract='unicode-stopword-svm-v1',algorithm='svm',
        input_view='already_masked_case_preserving_text',preprocessing_version='python-unicode-15-word-min2-english-v1',
        unicode=unicode_contract(),stop_words=sorted(ENGLISH_STOP_WORDS),minimum_token_codepoints=2,
        vocabulary=v.get_feature_names_out().tolist(),idf=v.idf_.tolist(),weights=model.coef_[0].tolist(),bias=float(model.intercept_[0]),
        classes=['ham','smishing'],positive_class='smishing',ngram_range=[1,2],normalization='l2',term_frequency='raw',
        calibration=dict(a=float(cal.coef_[0,0]),b=float(cal.intercept_[0])),threshold=artifact['threshold'],threshold_comparison='greater_or_equal',
        evaluation_status='retrospective_unverified_labels',calibration_status='fitted_unvalidated',
        automatic_warnings_approved=False,probability_approved=False)
    directory=output/'parity';directory.mkdir();w.save(directory/'selected-model.json',exported)
    probes=['Hello po, kumusta?', 'Your OTP is zznumberzz . Do not share it.', 'BDO statement available sa app.',
        'GCash transaction completed sa official app.', 'paki verify nyo ninyo na po', 'Verify account at zzurlzz',
        'account the verify', 'account qzxvunknownword verify', 'A I x ñ café İ ΟΣ ΟΣΑ Straße 𐐀𐐨',
        '', '   ', 'qzxvunknownword zzzqqq', 'asdfghjkl', 'zznumberzz', 'zzurlzz', '\ud800', 'x'*10001]
    texts=[rows[i]['text'] for i in ids]+probes;x=v.transform(texts);scores=w.score(artifact,texts);analyzer=v.build_analyzer()
    cases=[]
    for i,text in enumerate(texts):
        row=x.getrow(i);features={str(index):float(value) for index,value in zip(row.indices,row.data)}
        cases.append(dict(text=text,terms=analyzer(text),features=features,score=float(scores[i]),suspicious=bool(scores[i]>=artifact['threshold']),
            is_synthetic=i>=len(ids),must_abstain=text in ('','   ','qzxvunknownword zzzqqq','asdfghjkl','zznumberzz','zzurlzz','\ud800')))
    # Escape malformed surrogates; no message content appears in public reports.
    (directory/'selected-cases.json').write_text(json.dumps(cases,ensure_ascii=True,allow_nan=False),encoding='utf-8')
    assets=directory/'android-test-assets';assets.mkdir()
    shutil.copyfile(directory/'selected-model.json',assets/'selected-svm-model.json')
    shutil.copyfile(directory/'selected-cases.json',assets/'selected-svm-cases.json')
    if reference_parity is not None:
        # The shared -PmodelParityDir also runs existing active/comparator tests.
        for name in ('model.json','cases.json','active-model.json','active-cases.json'):
            shutil.copyfile(reference_parity/name,directory/name)
    meta=dict(model_sha256=w.digest(directory/'selected-model.json'),cases_sha256=w.digest(directory/'selected-cases.json'),
        feature_count=len(exported['vocabulary']),model_bytes=(directory/'selected-model.json').stat().st_size,cases=len(cases),
        real_masked_test_cases=len(ids),synthetic_probes=len(probes),contract='Test-only; production ModelLoader must reject schema 6',
        input_limitation='Frozen fit expects masked views. Raw SMS masking/integration is not silently added.')
    w.save(output/'export-summary.json',meta);return meta


def validate(run,archive,output):
    rows,groups,splits,artifact=snapshot(run,archive,output)
    ids=splits['partitions']['grouped']['test'];candidate=w.load(run/'grouped/svm-C-10.0/test-predictions.json');baseline=w.load(run/'grouped/baseline-svm/test-predictions.json')
    assert candidate['indices']==baseline['indices']==ids and candidate['labels']==baseline['labels']
    y=np.array(candidate['labels']);pred=np.array(candidate['scores'])>=artifact['threshold'];base=np.array(baseline['scores'])>=0
    bootstrap=intervals(y,pred,base,groups[ids]);w.save(output/'confidence-intervals.json',bootstrap)
    nested=nested_sources(rows,groups,output);robustness=stress(artifact,rows,ids);w.save(output/'robustness.json',robustness)
    targets=w.load(ROOT/'docs/bantaytext-comparison-20261013.json')['targeted_evaluation']['grouped']
    targeted={k:dict(v,wilson_fpr=wilson(v['fp'],v['ham'])) if 'ham' in v else v for k,v in targets.items()}
    export=export_selected(artifact,rows,ids,output,run/'parity')
    reliability=w.load(ROOT/'docs/bantaytext-comparison-20261013.json')['score_reliability']['grouped']
    aggregate=dict(snapshot=w.load(output/'snapshot.json'),confidence_intervals=bootstrap,nested_source=nested,robustness=robustness,
        targeted=targeted,calibration_reliability=reliability,export=export,
        deployment='Not approved: ZIP previously used, zero independent human labels/new intake; nested transfer and engineering checks cannot establish prospective validity')
    w.save(output/'aggregate.json',aggregate)
    w.save(output/'prospective-candidate-freeze.json',dict(created_utc=now(),candidate_sha256=w.digest(output/'selected-pipeline.pkl'),
        export_sha256=export['model_sha256'],protocol_sha256=w.digest(PROTOCOL),threshold=artifact['threshold'],
        prospective_records_received=0,independently_reviewed_records_received=0,
        policy='No model/threshold/calibration change. Future intake requires independent labels, privacy/use review and exclusion of historical overlaps before prediction.'))
    print('Additional retrospective validation completed; release remains unapproved',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('archive',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();validate(a.run,a.archive,a.output)
