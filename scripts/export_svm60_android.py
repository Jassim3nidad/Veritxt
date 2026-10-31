"""Export the frozen validation-selected SVM 60% without fitting or thesis-test reuse."""
from pathlib import Path
import argparse
import csv
import io
import json
import pickle
import numpy as np
from smishguard import multiclass_comparison as m

ROOT=Path(__file__).resolve().parents[1]
SOURCE60='73c996492889c846a396aba1b6f250eb3e488605104cb18c5318bb75c9dc605a'
SOURCE80='957fe1ef05885a81d909c495d23a06487908c07b891f204109fdd13b474f8104'
CASHBACK='[EWB]You have PHP 5,216 available for cashback. Claim it before it expires today'
PRACTICAL=[
 ('user_cashback','User-reported suspicious; authenticity not verified',CASHBACK),
 ('cashback_link','Synthetic cashback lure','[EWB]You have PHP 5,216 available for cashback. Claim it before it expires today at https://example.invalid/claim'),
 ('fake_bank','Synthetic bank lure','Your account is suspended. Verify your password at https://example.invalid/verify'),
 ('fake_delivery','Synthetic delivery lure','Your parcel is on hold. Pay a delivery fee at https://example.invalid/delivery to release your package.'),
 ('credential_request','Synthetic credential request','Your bank account is suspended. Send your OTP and PIN to https://example.invalid/account immediately.'),
 ('short_link','Synthetic shortened-link lure','Your account is locked. Act now: https://bit.ly/fictional-veritxt-test'),
 ('filipino_lure','Synthetic Filipino lure','Na-lock ang iyong account. Ibigay ang iyong OTP ngayon sa https://example.invalid/claim'),
 ('taglish_lure','Synthetic Taglish lure','Urgent po! Pakiverify ang account mo ngayon para hindi ma-suspend. https://example.invalid/verify'),
 ('unknown_sender','Synthetic unfamiliar sender','[ZXNOTICE] Your account needs verification immediately. Please visit https://example.invalid/update'),
 ('expiry','Synthetic expiry-based lure','Your reward expires today. Claim it now at https://example.invalid/reward'),
 ('ham_filipino','Synthetic ordinary conversation','Kita tayo bukas sa opisina. Ingat sa biyahe.'),
 ('ham_english','Synthetic ordinary conversation','The meeting starts tomorrow at nine. Bring your notes.'),
 ('ham_taglish','Synthetic ordinary conversation','Ma, late ako uuwi. May meeting pa sa office. Ingat po!'),
 ('otp_warning','Synthetic security notice','Your OTP is 123456. Never share this code with anyone.'),
 ('bank_notice','Synthetic informational notice','Your monthly statement is available in your banking app. Open the app directly to view it.'),
 ('gambling','Synthetic gambling advertisement','Play slots casino now! Register and claim your free bonus at https://example.invalid/casino'),
 ('gambling_taglish','Synthetic gambling advertisement','Laro na sa online casino! May libreng bonus at slots para sa iyo.'),
 ('ambiguous','Synthetic ambiguous offer','Claim your cashback in the official app before the offer expires.'),
 ('phone_in_message','Synthetic contact message','Please call +1 202 555 0100 when you arrive.'),
 ('short','Synthetic short message','Hi')]


def fixtures(pipe,probes):
    vec,model=pipe['tfidf'],pipe['classifier']
    texts=[m.legacy.normalize(text) for _,text in probes]
    x=vec.transform(texts);scores=model.decision_function(x);labels=model.predict(x);analyzer=vec.build_analyzer()
    return [dict(name=name,text=text,terms=analyzer(texts[i]),features={int(k):float(v) for k,v in zip(x[i].indices,x[i].data)},
        scores=scores[i].tolist(),prediction=int(labels[i]),
        wrapper='failure' if len(text)>10000 or '\x00' in text else 'unable' if not texts[i] else 'success')
        for i,(name,text) in enumerate(probes)]


def prepare(output):
    run=ROOT/'research/runs/multiclass-20261020/run-v1';old=ROOT/'research/runs/multiclass-android-20261020/export-v2'
    m.verify(run,'training-seal.json')
    assert m.legacy.digest(run/'svm-60.pkl')==SOURCE60 and m.legacy.digest(run/'svm-80.pkl')==SOURCE80
    selection=next(s for s in m.load(run/'selection.json') if s['id']=='svm-60')
    assert selection['value']==10. and selection['training_records']==2281 and selection['features']==30227
    pipes={size:pickle.loads((run/f'svm-{size}.pkl').read_bytes()) for size in (60,80)}
    vec,model=pipes[60]['tfidf'],pipes[60]['classifier']
    assert model.C==10. and model.classes_.tolist()==[0,1,2] and model.coef_.shape==(3,30227)
    assert vec.get_params()==pipes[80]['tfidf'].get_params()
    base=m.load(old/'model.json');assert m.legacy.digest(old/'model.json')=='ba6fc0bf7f32cd4405402534fdda408eed418072279928958ae4ba88c83894d6'
    words=vec.get_feature_names_out().tolist();assert all(vec.vocabulary_[w]==i for i,w in enumerate(words))
    base.update(model_version='veritxt-multiclass-20261020-svm-60-C10',vocabulary=words,idf=vec.idf_.tolist(),
        coefficients=model.coef_.tolist(),intercepts=model.intercept_.tolist())
    base['provenance']=dict(experiment='multiclass-20261020/run-v1',source_artifact='svm-60.pkl',pipeline_sha256=SOURCE60,
        training_seal_sha256=m.legacy.digest(run/'training-seal.json'),selection_sha256=m.legacy.digest(run/'selection.json'),
        dataset_sha256=m.load(run/'configuration.json')['input_identity']['zip_sha256'],
        training_records=2281,validation_records=761,test_records=761,selection='20% validation macro F1; fitted only on 60%',refitted=False)
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    m.save(output/'model.json',base);reread=m.load(output/'model.json')
    for key,a in [('idf',vec.idf_),('coefficients',model.coef_),('intercepts',model.intercept_)]:np.testing.assert_array_equal(reread[key],a)
    # Reuse independent stress-test text, never corpus records or held-out labels.
    previous=m.load(old/'multiclass-svm-cases.json')['cases']
    probes=[(c['name'],c['text']) for c in previous if not c['name'].startswith('vocabulary_')]
    probes += [(name,text) for name,_,text in PRACTICAL]
    probes += [('vocabulary_'+str(i),' | '.join(words[i:i+60])) for i in range(0,len(words),60)]
    cases=fixtures(pipes[60],probes)
    fixture=dict(model_sha256=m.legacy.digest(output/'model.json'),source_pipeline_sha256=SOURCE60,training_percent=60,
        independent_of_thesis_test=True,thesis_messages_used=0,tolerance=1e-10,cases=cases)
    m.save(output/'multiclass-svm60-cases.json',fixture)
    practical={size:fixtures(pipes[size],[(n,t) for n,_,t in PRACTICAL]) for size in (60,80)}
    comparison=[]
    for i,(name,scenario,text) in enumerate(PRACTICAL):
        comparison.append(dict(name=name,scenario=scenario,text=text,human_verified_expected_label=None,
            label_evidence='No independent human verification supplied; not an accuracy sample',
            svm60=practical[60][i],svm80=practical[80][i]))
    m.save(output/'practical-comparison.json',dict(thesis_test_messages_used=0,cases=comparison))
    buf=io.StringIO(newline='');writer=csv.DictWriter(buf,fieldnames=['name','scenario','text','human_verified_expected_label','svm60_prediction','svm60_scores','svm80_prediction','svm80_scores'])
    writer.writeheader()
    for row in comparison:
        writer.writerow({k:row[k] for k in ['name','scenario','text','human_verified_expected_label']}|
            {f'svm{s}_prediction':m.NAMES[row[f'svm{s}']['prediction']] for s in (60,80)}|
            {f'svm{s}_scores':json.dumps(row[f'svm{s}']['scores']) for s in (60,80)})
    (output/'practical-comparison.csv').write_text(buf.getvalue(),encoding='utf-8')
    private=output/'android-test-assets';private.mkdir()
    for name in ['multiclass-svm60-cases.json','practical-comparison.json']:(private/name).write_bytes((output/name).read_bytes())
    # The old model is test-only. It is never added to the 60% application's assets.
    (private/'comparison-svm80-model.json').write_bytes((old/'model.json').read_bytes())
    (output/'comparison-svm80-model.json').write_bytes((old/'model.json').read_bytes())
    asset=ROOT/'android/app/src/multiclassSvm60/assets/model.json'
    if asset.exists():raise FileExistsError('Refuse to overwrite an existing 60% export')
    asset.parent.mkdir(parents=True,exist_ok=True);asset.write_bytes((output/'model.json').read_bytes())
    m.save(output/'export-manifest.json',dict(source_pipeline_sha256=SOURCE60,model_sha256=m.legacy.digest(asset),
        features=30227,training_records=2281,validation_records=761,test_records=761,C=10.,cases=len(cases),
        practical_examples=len(comparison),thesis_test_messages_used=0,refitted=False,arrays_unchanged=True,
        script_sha256=m.legacy.digest(__file__),training_seal_sha256=m.legacy.digest(run/'training-seal.json')))
    m.verify(run,'training-seal.json')
    print(json.dumps(m.load(output/'export-manifest.json'),indent=2))
    for row in comparison:print(row['name'],m.NAMES[row['svm60']['prediction']],m.NAMES[row['svm80']['prediction']])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();prepare(args.output)
