"""Complete reviewed datasets and prospective evaluation using the existing frozen scorers."""
import argparse
import csv
from datetime import timedelta
from pathlib import Path
import shutil
import importlib.metadata
import numpy as np
from sklearn.metrics import f1_score
from . import validation_stage as stage
from .review_packets import private_output


def table(path, fields):
    with path.open(encoding='utf-8-sig',newline='') as stream:
        reader=csv.DictReader(stream)
        if reader.fieldnames!=list(fields):raise ValueError('Unexpected review columns')
        rows=list(reader)
    if any(None in r or any(v is None for v in r.values()) for r in rows):raise ValueError('Malformed review row')
    return rows


def apply_labels(source, adjudication, output):
    private_output(output)
    if output.resolve().is_relative_to(source.parent.resolve()) or output.resolve().is_relative_to(adjudication.parent.resolve()):
        raise ValueError('New dataset version must be outside its source/evidence directories')
    rows,mapping,manifest=stage.validated_adjudication(adjudication)
    if stage.sha(source)!=manifest['source_sha256']:raise ValueError('Source dataset differs from packet version')
    originals=stage.read(source);by_id={r['id']:r for r in originals}
    if len(by_id)!=len(originals) or set(by_id)!={r['source_id'] for r in mapping}:raise ValueError('Source membership changed')
    evidence=adjudication.parent/'evidence'
    attestations=table(evidence/'attestations.csv',('packet','reviewer_code','independent_without_labels_or_predictions','signed_at_utc'))
    if len(attestations)!=2 or {r['packet'] for r in attestations}!={'a','b'}:raise ValueError('Two signed independence attestations required')
    reviewers={}
    for row in attestations:
        if not row['reviewer_code'].strip() or row['independent_without_labels_or_predictions']!='yes':raise ValueError('Independent reviewer attestation unresolved')
        signed=stage.utc(row['signed_at_utc'])
        if signed>stage.utc(stage.now()):raise ValueError('Future attestation')
        who=row['packet'];reviewers[who]=row['reviewer_code']
        responses=stage.read_responses(evidence/f'{who}.csv',{r[who]:r['text'] for r in mapping})
        if any(not r['decision'] or r['reviewer_code']!=row['reviewer_code'] for r in responses.values()):raise ValueError('Incomplete returns or reviewer assignment mismatch')
    if len(set(reviewers.values()))!=2:raise ValueError('Distinct independent reviewers required')
    privacy=table(evidence/'privacy-release.csv',('review_id','redacted_text','release_status','privacy_reviewer','note'))
    released={r['review_id']:r for r in privacy};mapped={r['a']:r for r in mapping}
    if len(released)!=len(privacy) or set(released)!=set(mapped):raise ValueError('Privacy release must cover assigned cohort exactly once')
    admitted=[];excluded=[]
    for row in rows:
        decision=row['final_decision'];m=mapped[row['adjudication_id']];release=released[m['a']]
        if not decision:raise ValueError('All final decisions must be explicit before versioning')
        if row['adjudicator_code'] in reviewers.values():raise ValueError('A third adjudicator is required')
        if release['redacted_text']!=stage.display(m['text']):raise ValueError('Privacy view changed')
        reasons=[]
        if decision not in ('phishing','genuine'):reasons.append(decision)
        if row['resolved_privacy']!='yes' or release['release_status']!='verified' or not release['privacy_reviewer'].strip():reasons.append('privacy_unresolved')
        original=by_id[m['source_id']]
        if original['text']!=m['text']:raise ValueError('Source text changed')
        if reasons:excluded.append(dict(id=original['id'],reasons=reasons));continue
        admitted.append({**original,'historical_label':original.get('label'),
                         'label':int(decision=='phishing'),'label_status':'independently_reviewed_adjudicated'})
    if not admitted:raise ValueError('No eligible adjudicated binary records')
    output.mkdir(parents=True,exist_ok=False)
    stage.save(output/'dataset.json',admitted);stage.save(output/'excluded.json',excluded)
    shutil.copyfile(source,output/'parent-dataset.json')
    shutil.copytree(adjudication.parent,output/'review-evidence')
    # Adjudication may have a coordinator-chosen filename; identify it explicitly.
    result=dict(schema_version=1,created_utc=stage.now(),scope='all SMS phishing',
        title_status='Pending finalization',parent_sha256=stage.sha(source),
        adjudication_file=adjudication.name,records=len(admitted),excluded=len(excluded),
        kind='retrospective_reviewed',historical_results_preserved=True,
        files={p.relative_to(output).as_posix():stage.sha(p) for p in output.rglob('*') if p.is_file()})
    # A prospective admission manifest must have been prepared before any labels/predictions.
    admission=source.parent/'admission.json'
    if admission.exists():
        record=stage.read(admission)
        if record['dataset_sha256']!=stage.sha(source):raise ValueError('Prospective admission identity changed')
        for name,digest in record['files'].items():
            if stage.sha(source.parent/name)!=digest:raise ValueError('Prospective admission evidence changed')
        shutil.copytree(source.parent,output/'admission-evidence')
        result.update(kind='prospective_reviewed',admission=record)
        result['files'].update({p.relative_to(output).as_posix():stage.sha(p) for p in (output/'admission-evidence').rglob('*') if p.is_file()})
    stage.save(output/'dataset-version.json',result)
    print('New dataset version saved; historical labels and independent responses retained.')


SEMANTIC=('intake_id','decision','template_group','semantic_overlap','evidence_verified','reviewer_code','reviewed_at_utc','reason','language','source')


def admit(intake,screen,semantic,freeze,output):
    private_output(output);frozen=stage.verify_freeze(freeze)
    summary=stage.read(screen/'summary.json');ledger=stage.read(screen/'ledger.json')
    if summary['intake_sha256']!=stage.sha(intake) or summary['freeze_sha256']!=stage.sha(freeze):raise ValueError('Screened intake/freeze identity changed')
    if summary.get('ledger_sha256')!=stage.sha(screen/'ledger.json'):raise ValueError('Screen ledger changed or predates integrity support; rescreen into a new version')
    originals=table(intake,stage.INTAKE);reviews=table(semantic,SEMANTIC)
    indexed={r['intake_id']:r for r in originals};judgments={r['intake_id']:r for r in reviews};screened={r['intake_id']:r for r in ledger}
    if len(indexed)!=len(originals) or len(judgments)!=len(reviews) or set(indexed)!=set(judgments) or set(indexed)!=set(screened):raise ValueError('Semantic review must cover each screened ID exactly once')
    candidates=[];excluded=[];deadline=stage.utc(frozen['created_utc'])+timedelta(days=30)
    for key,r in indexed.items():
        review=judgments[key]
        if review['decision'] not in ('admit','hold') or not all(review[k].strip() for k in ('reason','reviewer_code','reviewed_at_utc')):raise ValueError('Incomplete semantic review')
        reviewed=stage.utc(review['reviewed_at_utc'])
        if not stage.utc(r['collected_at_utc'])<=reviewed<=stage.utc(stage.now()):raise ValueError('Invalid semantic review chronology')
        reasons=list(screened[key]['reasons'])
        if review['decision']=='hold':reasons.append('human_hold')
        if review['semantic_overlap']!='no' or review['evidence_verified']!='yes':reasons.append('semantic_or_evidence_unresolved')
        if not all(review[k].strip() for k in ('template_group','language','source')):reasons.append('missing_group_or_support')
        if stage.utc(r['collected_at_utc'])>deadline:reasons.append('outside_collection_window')
        if reasons:excluded.append(dict(id=key,reasons=reasons));continue
        candidates.append(dict(id=key,text=r['redacted_text'],group=review['template_group'],language=review['language'],source=review['source'],
                               received_at_utc=r['received_at_utc'],collected_at_utc=r['collected_at_utc']))
    candidates.sort(key=lambda r:(stage.utc(r['collected_at_utc']),stage.utc(r['received_at_utc']),r['id']))
    selected=[];groups=set()
    for row in candidates:
        if row['group'] in groups or len(groups)>=200:
            excluded.append(dict(id=row['id'],reasons=['later_group_member_or_collection_cap']));continue
        groups.add(row['group']);selected.append(row)
    if len(groups)<200 and stage.utc(stage.now())<deadline:raise ValueError('Collection window remains open: wait for 200 groups or 30 days')
    if not selected:raise ValueError('No eligible prospective candidates')
    output.mkdir(parents=True,exist_ok=False);stage.save(output/'dataset.json',selected);stage.save(output/'excluded.json',excluded)
    for name,path in {'intake.csv':intake,'semantic.csv':semantic,'screen-summary.json':screen/'summary.json','screen-ledger.json':screen/'ledger.json'}.items():shutil.copyfile(path,output/name)
    stage.save(output/'admission.json',dict(created_utc=stage.now(),scope='all SMS phishing',freeze_sha256=stage.sha(freeze),
        dataset_sha256=stage.sha(output/'dataset.json'),historical_index_sha256=summary['historical_index_sha256'],
        cutoff_utc=deadline.isoformat(),records=len(selected),excluded=len(excluded),
        files={p.name:stage.sha(p) for p in output.iterdir() if p.is_file()}))
    print('Prospective candidates frozen for blinded review; no predictions generated.')


RUNTIME_FILES=('research/smishguard/review_completion.py','research/smishguard/validation_stage.py',
    'research/smishguard/parity.py','research/smishguard/mbert_quantize.py',
    'research/smishguard/deployment_policy.py','research/smishguard/preliminary_compare.py',
    'research/smishguard/expanded_evaluate.py','research/smishguard/evaluate.py',
    'research/smishguard/mbert_evaluate.py','research/smishguard/uncertainty.py',
    'android/app/src/mbert/java/ph/smishguard/model/BertWordPiece.kt',
    'android/app/src/mbert/java/ph/smishguard/model/MbertDetector.kt')
RUNTIME_PACKAGES=('numpy','scipy','scikit-learn','transformers','tokenizers','onnxruntime')


def runtime_versions():
    return {name:importlib.metadata.version(name) for name in RUNTIME_PACKAGES}


def lock_runtime(freeze,output):
    private_output(output);stage.verify_freeze(freeze)
    stage.save(output,dict(created_utc=stage.now(),model_freeze_sha256=stage.sha(freeze),
        files={name:stage.sha(stage.ROOT/name) for name in RUNTIME_FILES},packages=runtime_versions(),
        note='Additional evaluation/runtime integrity; original model freeze time and hashes are preserved.'))


def verify_runtime(freeze):
    path=freeze.parent/'evaluation-runtime-lock.json';lock=stage.read(path)
    if lock['model_freeze_sha256']!=stage.sha(freeze) or lock['packages']!=runtime_versions():raise ValueError('Evaluation runtime/freeze changed')
    if set(lock['files'])!=set(RUNTIME_FILES) or any(stage.sha(stage.ROOT/name)!=h for name,h in lock['files'].items()):raise ValueError('Evaluation inference code changed')
    return path


def scores_for_models(rows, frozen):
    from .parity import predict
    from .mbert_quantize import session
    from .mbert_experiment import redacted_case_view
    from transformers import BertTokenizer
    from scipy.special import expit
    scores={};models={}
    for name in ('lr','nb','svm','mbert'):
        assets=stage.ROOT/f'android/app/src/{name}/assets';model=stage.read(assets/'model.json');models[name]=model
        if name!='mbert':scores[name]=np.array([predict(model,r['text'])[0] for r in rows]);continue
        tokenizer=BertTokenizer(vocab_file=str(assets/'vocab.txt'),do_lower_case=False,strip_accents=False)
        runtime=session(assets/'model.onnx');values=[]
        for row in rows:
            encoded=dict(tokenizer(redacted_case_view(row['text']),max_length=model['max_length'],padding='max_length',truncation=True,return_tensors='np'))
            logits=runtime.run(None,encoded)[0][0].astype(np.float64)
            values.append(float(expit(model['calibration']['a']*(logits[1]-logits[0])+model['calibration']['b'])))
        scores[name]=np.array(values)
    return scores,models


def evaluate(dataset,freeze,output,scorer=None):
    from .evaluate import metrics
    from .expanded_evaluate import complete_intervals
    from .mbert_evaluate import paired
    from .deployment_policy import assessable
    private_output(output);frozen=stage.verify_freeze(freeze);version=stage.read(dataset/'dataset-version.json')
    runtime=verify_runtime(freeze)
    for name,digest in version['files'].items():
        if stage.sha(dataset/name)!=digest:raise ValueError('Reviewed dataset evidence changed')
    if version['kind']!='prospective_reviewed' or version['admission']['freeze_sha256']!=stage.sha(freeze):raise ValueError('Requires reviewed prospective cohort for this exact four-model freeze')
    rows=stage.read(dataset/'dataset.json');y=np.array([r['label'] for r in rows]);groups=np.array([r['group'] for r in rows])
    if not rows or len(set(groups))!=len(rows):raise ValueError('Expected one member per prospective template group')
    # The lock lives with the cohort, so changing output directories cannot reopen it.
    output.mkdir(parents=True,exist_ok=False)
    stage.save(dataset/'evaluation-started.json',dict(created_utc=stage.now(),dataset_version_sha256=stage.sha(dataset/'dataset-version.json'),freeze_sha256=stage.sha(freeze),runtime_sha256=stage.sha(runtime)))
    scores,models=(scorer or scores_for_models)(rows,frozen)
    if set(scores)!={'lr','nb','svm','mbert'}:raise ValueError('Exactly four frozen models required')
    results={};predictions={}
    support={str(k):dict(records=int((y==k).sum()),groups=len(set(groups[y==k]))) for k in (0,1)}
    adequate=all(s['records']>=20 and s['groups']>=10 for s in support.values())
    for name,p in scores.items():
        t=frozen['models'][name]['threshold']
        if models[name]['threshold']!=t:raise ValueError('Threshold changed')
        result=metrics(y,p,t);predictions[name]=p>=t
        mask=np.array([len(r['text'])<=10000 and assessable(r['text'],models[name].get('assessability_vocabulary',models[name].get('vocabulary',[]))) for r in rows])
        result.update(macro_f1=float(f1_score(y,p>=t,labels=[0,1],average='macro',zero_division=0)),threshold=t,
                      coverage=float(mask.mean()),scored=int(mask.sum()),abstained=int((~mask).sum()),
                      scored_only=metrics(y[mask],p[mask],t) if mask.any() else None,
                      accuracy_abstentions_as_failures=float(((p>=t)==y)[mask].sum()/len(y)),
                      confidence_intervals=complete_intervals(y,p,groups,t) if adequate else None)
        for field in ('source','language'):
            result['by_'+field]={}
            for value in sorted({r[field] for r in rows}):
                indices=np.array([r[field]==value for r in rows]);labels=y[indices]
                result['by_'+field][value]=dict(records=len(labels),positives=int(labels.sum()),
                    metrics=metrics(labels,p[indices],t) if len(labels)>=20 and min((labels==0).sum(),(labels==1).sum())>=5 else None)
        results[name]=result
    stage.verify_freeze(freeze)
    verify_runtime(freeze)
    stage.save(output/'paired-predictions.json',dict(ids=[r['id'] for r in rows],labels=y.tolist(),groups=groups.tolist(),scores={k:v.tolist() for k,v in scores.items()}))
    stage.save(output/'comparison.json',dict(results=results,support=support,
        interpretation='descriptive convenience cohort' if adequate else 'descriptive only; insufficient confirmatory support',
        paired_f1=paired(y,predictions,groups) if adequate else None,freeze_sha256=stage.sha(freeze),dataset_version_sha256=stage.sha(dataset/'dataset-version.json')))
    fields=('model','threshold','accuracy','precision','recall','f1','macro_f1','false_positive_rate','brier','log_loss','coverage')
    stage.csv_write(output/'comparison.csv',fields,[dict(model=name,**{k:result[k] for k in fields[1:]}) for name,result in results.items()])
    lines=['| Model | Accuracy | Phishing F1 | Coverage |','|---|---:|---:|---:|']
    lines.extend(f"| {name} | {r['accuracy']:.4f} | {r['f1']:.4f} | {r['coverage']:.4f} |" for name,r in results.items())
    (output/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('Four frozen models evaluated once; comparison tables saved privately.')


def main():
    parser=argparse.ArgumentParser(description=__doc__);commands=parser.add_subparsers(dest='command',required=True)
    p=commands.add_parser('apply');p.add_argument('source',type=Path);p.add_argument('adjudication',type=Path);p.add_argument('output',type=Path)
    p=commands.add_parser('admit')
    for arg in ('intake','screen','semantic','freeze','output'):p.add_argument(arg,type=Path)
    p=commands.add_parser('evaluate')
    for arg in ('dataset','freeze','output'):p.add_argument(arg,type=Path)
    p=commands.add_parser('lock-runtime');p.add_argument('freeze',type=Path);p.add_argument('output',type=Path)
    args=parser.parse_args()
    if args.command=='apply':apply_labels(args.source,args.adjudication,args.output)
    elif args.command=='admit':admit(args.intake,args.screen,args.semantic,args.freeze,args.output)
    elif args.command=='evaluate':evaluate(args.dataset,args.freeze,args.output)
    else:lock_runtime(args.freeze,args.output)


if __name__=='__main__':main()
