"""Validate/convert supplied LR weights unchanged; no training/evaluation approval."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import unicodedata
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from .train import write_json

PROBES=["Hello po, kumusta ang inyong araw?", "Pakisuri ang account sa opisyal na app.",
        "A I x ñ Ñ Á É é café _ OTP account_1", "İ I ı i STRASSE Straße ΟΣ ΟΣΑ ΑΣ́Α",
        "a b a b single_character ² Ⅷ 𐐀 𐐨", "Verify at https://example.invalid/software-test only",
        "qzxvunknownword", " ", "", "hello "*1000, "bayad "*1666,
        "GCash account verify ngayon", "BDO statement available sa app", "ÁéÑ name_test 123",
        "👋 Kumusta po! Meeting natin bukas."]


def validate(m):
    if m.get("model_type")!="logistic_regression" or m.get("classes")!=["ham","smishing"] or m.get("ngram_range")!=[1,2] or m.get("lowercase") is not True:
        raise ValueError("Unsupported supplied model semantics")
    vocab=m["vocabulary"];n=len(vocab)
    if not 1<=n<=50000 or any(type(i) is not int for i in vocab.values()) or set(vocab.values())!=set(range(n)):
        raise ValueError("Vocabulary indices must be unique and contiguous")
    for term in vocab:
        if not isinstance(term,str) or term!=term.lower() or not re.fullmatch(r"\w+(?: \w+)?",term):raise ValueError("Unsupported feature token")
    for name in ("idf","coef"):
        if len(m[name])!=n or any(type(x) not in (int,float) or not math.isfinite(x) for x in m[name]):raise ValueError("Invalid numeric vector")
    if any(x<=0 for x in m["idf"]) or type(m["intercept"]) not in (int,float) or not math.isfinite(m["intercept"]):raise ValueError("Invalid IDF/intercept")
    return m


def portable(m,text):
    tokens=re.findall(r"\b\w+\b",text.lower())
    counts=Counter(tokens+[a+" "+b for a,b in zip(tokens,tokens[1:])])
    values={m["vocabulary"][word]:count*m["idf"][m["vocabulary"][word]] for word,count in counts.items() if word in m["vocabulary"]}
    norm=math.sqrt(sum(v*v for v in values.values()))
    margin=m["intercept"]+sum(m["coef"][i]*v/norm for i,v in values.items()) if norm else m["intercept"]
    score=1/(1+math.exp(-margin)) if margin>=0 else math.exp(margin)/(1+math.exp(margin))
    return score


def ranges(points):
    result=[]
    for i in points:
        if result and result[-1][1]+1==i:result[-1][1]=i
        else:result.append([i,i])
    return result


def unicode_contract():
    # Freeze Python's Unicode properties, including numeric/underscore word chars,
    # full lowercase expansion, and context-sensitive Greek final sigma.
    word=[];lower={};cased=[];ignorable=[]
    for i in range(sys.maxunicode+1):
        c=chr(i)
        if c.isalnum() or c=="_":word.append(i)
        if c.lower()!=c:lower[str(i)]=c.lower()
        if c.islower() or c.isupper() or c.istitle():cased.append(i)
        if ("AΣ"+c+"A").lower()[1]=="σ" and ("AΣ"+c+" ").lower()[1]=="ς":ignorable.append(i)
    return dict(unicode_version=unicodedata.unidata_version,word_ranges=ranges(word),lowercase_map=lower,
                cased_ranges=ranges(cased),case_ignorable_ranges=ranges(ignorable))


def convert(source, guide, output, parity, report):
    if unicodedata.unidata_version != "15.0.0": raise ValueError("Use Python 3.12 / Unicode 15.0.0 for this versioned Android contract")
    m=validate(json.loads(source.read_text(encoding="utf-8-sig")))
    vectorizer=TfidfVectorizer(vocabulary=m["vocabulary"],ngram_range=(1,2),lowercase=True,token_pattern=r"(?u)\b\w+\b")
    vectorizer.idf_=np.array(m["idf"])
    refs=re.findall(r'\| "(.+?)" \| (ham|smishing) \| ([0-9.]+) \|',guide.read_text(encoding="utf-8-sig"))
    if len(refs)!=5:raise ValueError("Expected five guide reference messages")
    reference=[]
    for i,(text,label,expected) in enumerate(refs):
        score=portable(m,text);error=abs(score-float(expected))
        if error>0.000050000001 or (score>.5)!=(label=="smishing"):raise ValueError("Guide reference mismatch; weights not changed")
        reference.append(dict(reference=i+1,rounded_expected=float(expected),python_score=score,absolute_error=error))
    cases=[];max_error=0.
    for text in PROBES:
        z=float((vectorizer.transform([text])@np.array(m["coef"]))[0]+m["intercept"])
        expected=1/(1+math.exp(-z));score=portable(m,text);max_error=max(max_error,abs(score-expected))
        if abs(score-expected)>1e-12:raise ValueError("Portable/scikit-learn mismatch")
        cases.append(dict(text=text,tokens=re.findall(r"\b\w+\b",text.lower()),score=score,suspicious=score>.5,valid_input=bool(text.strip()) and len(text)<=10000))
    words=sorted(m["vocabulary"],key=m["vocabulary"].get)
    converted=dict(schema_version=2,preprocessing_version="python-unicode-word-v2",feature_type="word-unigram-bigram-tfidf-l2",
        vocabulary=words,idf=m["idf"],weights=m["coef"],bias=m["intercept"],classes=["ham","smishing"],positive_class="smishing",
        ngram_range=[1,2],lowercase=True,token_pattern=r"\b\w+\b",term_frequency="raw",normalization="l2",score_transform="sigmoid",
        threshold=.5,threshold_comparison="strict_greater",synthetic=False,
        provenance=dict(kind="user_supplied_export",source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),trained_on_rows=m.get("trained_on_rows")),
        technical_compatibility="reference_verified",evaluation_status="unverified",calibration_status="uncalibrated",
        intended_use="manual_development",automatic_warnings_approved=False,unicode=unicode_contract())
    output.parent.mkdir(parents=True,exist_ok=True);write_json(output,converted)
    parity.parent.mkdir(parents=True,exist_ok=True);write_json(parity,cases)
    write_json(report,dict(source_sha256=converted["provenance"]["source_sha256"],converted_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
        feature_count=len(words),reference_rounding_tolerance=.00005,guide_references=reference,python_sklearn_max_absolute_error=max_error,
        android_tolerance=1e-10,unicode_version=unicodedata.unidata_version,python_version=sys.version.split()[0],
        note="Weights/IDF/intercept unchanged. Positive class from export+guide+reference agreement; original training code absent. Software parity is not research evaluation."))
    print("Converted supplied model unchanged; five rounded references and portable/scikit-learn checks passed.")


def main():
    p=argparse.ArgumentParser();p.add_argument("source",type=Path);p.add_argument("guide",type=Path)
    p.add_argument("--output",type=Path,default=Path("android/app/src/development/assets/model.json"))
    p.add_argument("--parity",type=Path,default=Path("android/app/src/androidTest/assets/supplied-parity.json"))
    p.add_argument("--report",type=Path,default=Path("docs/model-conversion.json"));a=p.parse_args();convert(a.source,a.guide,a.output,a.parity,a.report)


if __name__ == "__main__":main()
