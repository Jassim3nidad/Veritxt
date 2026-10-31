"""Export the sealed svm-80 pipeline unchanged; independent synthetic parity only.

No fitting, held-out text access, calibration, masking or threshold selection.
"""
from pathlib import Path
import argparse
import json
import pickle
import random
import sys
import unicodedata
import numpy as np
from smishguard import multiclass_comparison as m
from smishguard.convert_supplied import unicode_contract, ranges

ROOT=Path(__file__).resolve().parents[1]
SOURCE_SHA='957fe1ef05885a81d909c495d23a06487908c07b891f204109fdd13b474f8104'
MODEL_VERSION='veritxt-multiclass-20261020-svm-80-C10'


def prepare(run,output):
    run,output=Path(run).resolve(),Path(output).resolve()
    m.verify(run,'training-seal.json')
    source=run/'svm-80.pkl'
    if m.legacy.digest(source)!=SOURCE_SHA:raise ValueError('Not the selected frozen multiclass SVM')
    if unicodedata.unidata_version!='15.0.0':raise ValueError('Use the original Python 3.12 Unicode 15 runtime')
    selected=next(r for r in m.load(run/'selection.json') if r['id']=='svm-80')
    assert selected['value']==10. and selected['training_records']==3042 and selected['features']==37885
    pipe=pickle.loads(source.read_bytes());vec,model=pipe['tfidf'],pipe['classifier']
    assert model.C==10. and model.classes_.tolist()==[0,1,2] and model.coef_.shape==(3,37885)
    assert model.multi_class=='ovr' and model.fit_intercept and vec.preprocessor is None
    assert vec.token_pattern==m.legacy.TOKEN_PATTERN and vec.stop_words==m.legacy.STOP_WORDS
    assert vec.ngram_range==(1,2) and vec.norm=='l2' and not vec.sublinear_tf and vec.smooth_idf
    assert vec.lowercase and not vec.binary and vec.strip_accents is None
    vocabulary=vec.get_feature_names_out().tolist()
    assert all(vec.vocabulary_[term]==i for i,term in enumerate(vocabulary))
    export=dict(schema_version=10,research_contract='veritxt-raw-unicode-multiclass-svm-v1',
        model_version=MODEL_VERSION,algorithm='linear_svm',C=10.,input_view='raw_sms',
        classes=[0,1,2],class_names=['Ham','Smishing','Gambling'],
        decision='argmax_first_class_on_tie',score='raw_one_vs_rest_margins',calibration='none',
        probability=False,ngram_range=[1,2],token_pattern=vec.token_pattern,stop_words=vec.stop_words,
        normalization='whitespace-collapse-then-python-lowercase',tf='raw',norm='l2',smooth_idf=True,
        vocabulary=vocabulary,idf=vec.idf_.tolist(),coefficients=model.coef_.tolist(),intercepts=model.intercept_.tolist(),
        unicode=unicode_contract(),digit_ranges=ranges(i for i in range(sys.maxunicode+1) if chr(i).isdecimal()),
        whitespace_ranges=ranges(i for i in range(sys.maxunicode+1) if chr(i).isspace()),
        provenance=dict(experiment='multiclass-20261020/run-v1',source_artifact='svm-80.pkl',
            pipeline_sha256=SOURCE_SHA,training_seal_sha256=m.legacy.digest(run/'training-seal.json'),
            selection_sha256=m.legacy.digest(run/'selection.json'),
            dataset_sha256=m.load(run/'configuration.json')['input_identity']['zip_sha256'],
            training_records=3042,test_records=761,refitted=False),
        evaluation_status='python_retrospective_inherited_labels',automatic_warning_policy='existing_consent_and_risk_policy')
    output.mkdir(parents=True,exist_ok=False)
    m.save(output/'model.json',export)
    reread=m.load(output/'model.json')
    np.testing.assert_array_equal(reread['idf'],vec.idf_)
    np.testing.assert_array_equal(reread['coefficients'],model.coef_)
    np.testing.assert_array_equal(reread['intercepts'],model.intercept_)
    probes=[
        ('ham_filipino','Kita tayo bukas sa opisina. Ingat sa biyahe.'),
        ('smishing_english','Your account is suspended. Verify your password at https://example.invalid/verify'),
        ('gambling_english','Play slots casino now! Register and claim your free bonus at https://example.invalid/casino'),
        ('ham_english','The meeting starts tomorrow at nine. Bring your notes.'),
        ('ham_taglish','Ma, late ako uuwi. May meeting pa sa office. Ingat po!'),
        ('smishing_filipino','Na-lock ang iyong account. Ibigay ang iyong OTP ngayon sa https://example.invalid/claim'),
        ('gambling_taglish','Laro na sa online casino! May libreng bonus at slots para sa iyo.'),
        ('otp_warning','Your OTP is 123456. Never share this code with anyone.'),
        ('phone_inside','Please call +1 202 555 0100 when you arrive.'),
        ('short','Hi'),('short_tagalog','Oo'),('ambiguous','Claim your reward after your appointment.'),
        ('empty',''),('spaces',' \t\n\u00a0\u2007'),('unknown','qzxvqunknownfixture'),('punctuation','???!!!'),
        ('url_only','https://example.invalid/account'),('phone_only','+1 202 555 0100'),
        ('email_only','fictional@example.invalid'),
        ('unicode','👋 Kumustá po! ΣΟΣ ΟΣΑ ΑΣ́Α İ café a\u0301 𐐀 𐐨 𞓐 𠀀'),
        ('all_whitespace','\x1c\x1d\x1e\x1f\x85\u00a0\u2007\u2028\t\nΣΟΣ İ 𐐀 café ₱ ٢,٥٠٠.٥٠'),
        ('url_punctuation','HTTPS://EXAMPLE.INVALID/Verify?a=99). www.EXAMPLE.invalid, foohttps://x <>'),
        ('number_boundaries','123abc 12.34abc a123 123.45.67x 1,2x _34 ₱ ٥,٢x $12abc €𑁦.𝟙'),
        ('stopword_bridging','verify the account with yours at no not an a'),
        ('currency','₱ 5,000.50 $12.34 €0.01 £ ٢.٥ ₱\t123 PHP200'),
        ('long','Please attend the meeting tomorrow. '*220),
        ('max_length','a '*4999+'ab'),('over_limit','a'*10001),
        ('nul','hello\x00world'),('embedded_newline','Payment received.\n\nNever share OTP.\tSalamat!')]
    # Model-derived vocabulary coverage is a numerical test, not a new SMS dataset.
    probes += [('vocabulary_'+str(i),' | '.join(vocabulary[i:i+60])) for i in range(0,len(vocabulary),60)]
    rng=random.Random(20261020)
    alphabet='aA_01. ,<>:/?\t\n₱$€£ΣΟΣİé²Ⅷ٢𝟙𐐀\u2007\u0301\x1c'
    probes += [('token_edge_'+str(i),''.join(rng.choices(alphabet,k=120))) for i in range(400)]
    normalized=[m.legacy.normalize(t) for _,t in probes]
    x=vec.transform(normalized);scores=model.decision_function(x);pred=model.predict(x)
    records=[];maximum_export_error=0.
    portable_weights=np.asarray(reread['coefficients'])
    analyzer=vec.build_analyzer()
    for i,(name,text) in enumerate(probes):
        features={int(k):float(v) for k,v in zip(x[i].indices,x[i].data)}
        portable=np.array(reread['intercepts'],dtype=float)
        for k,v in features.items():portable+=portable_weights[:,k]*v
        error=float(np.max(np.abs(portable-scores[i])));maximum_export_error=max(maximum_export_error,error)
        assert error<=1e-10 and int(np.argmax(portable))==int(pred[i])
        records.append(dict(name=name,text=text,terms=analyzer(normalized[i]),features=features,
            scores=scores[i].tolist(),prediction=int(pred[i]),
            wrapper='failure' if len(text)>10000 or '\x00' in text else 'unable' if not normalized[i] else 'success'))
    assert {r['prediction'] for r in records}=={0,1,2}
    fixture=dict(model_sha256=m.legacy.digest(output/'model.json'),source_pipeline_sha256=SOURCE_SHA,
        independent_of_thesis_test=True,thesis_messages_used=0,tolerance=1e-10,cases=records)
    m.save(output/'multiclass-svm-cases.json',fixture)
    (output/'android-test-assets').mkdir()
    m.save(output/'android-test-assets/multiclass-svm-cases.json',fixture)
    asset=ROOT/'android/app/src/multiclassSvm/assets/model.json'
    if asset.exists():raise FileExistsError('Refuse to replace an existing model export')
    asset.parent.mkdir(parents=True,exist_ok=True);asset.write_bytes((output/'model.json').read_bytes())
    m.save(output/'export-manifest.json',dict(model_sha256=m.legacy.digest(asset),source_pipeline_sha256=SOURCE_SHA,
        training_seal_sha256=m.legacy.digest(run/'training-seal.json'),export_script_sha256=m.legacy.digest(__file__),
        cases=len(records),thesis_test_messages_used=0,features=len(vocabulary),classes=[0,1,2],C=10.,
        weights_unchanged=True,maximum_export_error=maximum_export_error,refitted=False,
        model_bytes=asset.stat().st_size,fixture_sha256=m.legacy.digest(output/'multiclass-svm-cases.json')))
    m.verify(run,'training-seal.json')
    print(json.dumps(m.load(output/'export-manifest.json'),indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,default=ROOT/'research/runs/multiclass-20261020/run-v1')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();prepare(args.run,args.output)
