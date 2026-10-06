"""Private blinded reviews and a frozen, prospective intake boundary. No model fitting."""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
from difflib import SequenceMatcher
import hashlib
import io
import json
import os
from pathlib import Path
import random
import secrets
import uuid
import xml.etree.ElementTree as ET
import zipfile
from .expanded_prepare import clean
from .preprocessing import normalize
from .review_packets import private_output

ROOT=Path(__file__).resolve().parents[2]
STAGE=ROOT/'research/data/validation-20261006'
RUN=ROOT/'research/data/expanded-20261005/experiment-v1'
LABELS=('phishing','genuine','out_of_scope','uncertain')
FIELDS=('review_id','redacted_text','decision','rationale','privacy_issue','reviewer_code','completed_at_utc')
INTAKE=('intake_id','received_at_utc','collected_at_utc','redacted_text','collector_code',
        'source_use_evidence','receipt_evidence_ref','permission_status','privacy_review_status',
        'privacy_reviewer','prior_model_viewing','notes')
TEXT_KEYS={'text','text_redacted','redacted_text','text_for_review','message','message_text','sms','message_body','sms_text','body','v2'}

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,value):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as f:json.dump(value,f,indent=2,ensure_ascii=False,allow_nan=False)
def now():return datetime.now(timezone.utc).isoformat()
def display(s):
    s=str(s)
    return "'"+s if s.lstrip().startswith(('=','+','-','@')) else s
def csv_write(p,fields,rows):
    with p.open('x',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        w.writerows({k:display(r.get(k,'')) for k in fields} for r in rows)

def prepare(source=None, review=None):
    source=source or RUN/'case-view.json';review=review or STAGE/'review'
    private_output(review)
    rows=read(source)
    if not rows or any(not r.get('id') or not r.get('text','').strip() for r in rows) or len({r['id'] for r in rows})!=len(rows):
        raise ValueError('Expected nonempty unique source IDs and text')
    review.mkdir(parents=True,exist_ok=False)
    mapping=[];packets={}
    for r in rows:
        mapping.append(dict(source_id=r['id'],text=r['text'],a=uuid.uuid4().hex,b=uuid.uuid4().hex))
    for who in ('a','b'):
        order=[dict(review_id=r[who],redacted_text=r['text']) for r in mapping]
        seed=secrets.randbits(64);random.Random(seed).shuffle(order)
        packets[who]=order
        csv_write(review/f'annotator-{who}.csv',FIELDS,order)
    save(review/'coordinator/mapping.json',mapping)
    save(review/'coordinator/packet-inputs.json',dict(fields=FIELDS,packets=packets))
    save(review/'coordinator/packet-manifest.json',dict(records=len(rows),created_utc=now(),
        files={f'annotator-{w}.csv':sha(review/f'annotator-{w}.csv') for w in ('a','b')},
        status='prepared; independent decisions and human privacy checks pending',decisions_assigned=0,
        source_sha256=sha(source)))
    # Blank reviewer attestations are explicit inputs, never inferred from filled cells.
    csv_write(review/'coordinator/attestations.csv',('packet','reviewer_code','independent_without_labels_or_predictions','signed_at_utc'),[{'packet':'a'},{'packet':'b'}])
    csv_write(review/'coordinator/privacy-release.csv',('review_id','redacted_text','release_status','privacy_reviewer','note'),
              [dict(review_id=r['a'],redacted_text=r['text']) for r in mapping])
    print('Prepared two independent orders with',len(rows),'blinded records each; zero human decisions.')

def freeze():
    p=STAGE/'prospective-freeze.json'
    models={};files={}
    for name in ('lr','nb','svm','mbert'):
        assets=ROOT/f'android/app/src/{name}/assets';meta=read(assets/'model.json')
        selected={f.relative_to(ROOT).as_posix():sha(f) for f in assets.iterdir() if f.is_file()}
        files.update(selected)
        models[name]=dict(model_version=meta['model_version'],threshold=meta['threshold'],
            threshold_comparison=meta.get('threshold_comparison','greater_or_equal'),assets=selected)
        f=RUN/name/'freeze.json';files[f.relative_to(ROOT).as_posix()]=sha(f)
    for rel in ('research/smishguard/preprocessing.py','research/smishguard/mbert_experiment.py',
                'docs/expanded-comparison-protocol-20261005.md','research/mbert-dependency-lock.txt'):
        files[rel]=sha(ROOT/rel)
    for f in (ROOT/'android/app/src/main/java/ph/smishguard/model').glob('*.kt'):
        files[f.relative_to(ROOT).as_posix()]=sha(f)
    save(p,dict(created_utc=now(),models=models,files=files,policy='No fitting, recalibration, checkpoint/threshold selection or test-driven changes. Packaging-only changes require byte-identical assets and parity.',
        prospective_records_received=0,physical_phone_evidence_received=0))
    print('Four models, thresholds, assets and inference code frozen for future intake.')

def verify_freeze(p):
    f=read(p)
    if any(not (ROOT/name).is_file() or sha(ROOT/name)!=digest for name,digest in f['files'].items()):
        raise ValueError('Frozen pipeline changed; do not evaluate this prospective cohort')
    return f

def read_responses(path,expected):
    with path.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=list(FIELDS):raise ValueError('Unexpected response columns')
        rows=list(reader)
    if any(None in r or any(v is None for v in r.values()) for r in rows):raise ValueError('Malformed response row')
    if len(rows)!=len(expected) or len({r['review_id'] for r in rows})!=len(rows):raise ValueError('Missing or duplicated response IDs')
    values={r['review_id']:r for r in rows}
    if set(values)!=set(expected):raise ValueError('Responses do not match assigned packet')
    for k,r in values.items():
        if None in r or any(v is None for v in r.values()):raise ValueError('Malformed response row')
        if r['redacted_text']!=display(expected[k]):raise ValueError('Review text was changed; retain original and request coordinator correction')
        if r['decision'] and r['decision'] not in LABELS:raise ValueError('Invalid human decision')
        if r['decision'] and (not all(r[x].strip() for x in ('rationale','reviewer_code','completed_at_utc')) or r['privacy_issue'] not in ('no','yes','uncertain')):
            raise ValueError('Completed decision lacks rationale, reviewer, timestamp or privacy response')
        if r['completed_at_utc'] and utc(r['completed_at_utc'])>utc(now()):raise ValueError('Future response timestamp')
    return values

def agreement(pairs):
    n=len(pairs)
    if not n:return dict(paired=0,observed=None,expected=None,kappa=None,confusion={})
    a=Counter(x for x,y in pairs);b=Counter(y for x,y in pairs)
    observed=sum(x==y for x,y in pairs)/n
    expected=sum(a[k]*b[k] for k in set(a)|set(b))/n**2
    return dict(paired=n,observed=observed,expected=expected,
                kappa=(observed-expected)/(1-expected) if expected<1 else None,
                confusion={x:{y:sum(u==x and v==y for u,v in pairs) for y in LABELS} for x in LABELS})

def analyze(a,b,output,review=None):
    review=review or STAGE/'review'
    private_output(output);mapping=read(review/'coordinator/mapping.json')
    if a.resolve()==b.resolve():raise ValueError('Two distinct independent return files required')
    packet_manifest=read(review/'coordinator/packet-manifest.json')
    packet_inputs=read(review/'coordinator/packet-inputs.json')['packets']
    for who in ('a','b'):
        packet=review/f'annotator-{who}.csv'
        if sha(packet)!=packet_manifest['files'][packet.name]:raise ValueError('Original packet changed')
        expected={r[who]:r['text'] for r in mapping}
        if {r['review_id']:r['redacted_text'] for r in packet_inputs[who]}!=expected:raise ValueError('Coordinator mapping differs from packet inputs')
        read_responses(packet,expected)
    responses={who:read_responses(path,{r[who]:r['text'] for r in mapping}) for who,path in (('a',a),('b',b))}
    reviewers={who:{r['reviewer_code'] for r in values.values() if r['decision']} for who,values in responses.items()}
    if any(len(v)>1 for v in reviewers.values()) or reviewers['a']&reviewers['b']:
        raise ValueError('Each packet requires one distinct independent reviewer; check reviewer codes')
    pairs=[];binary=[];queue=[];completed=Counter()
    for r in mapping:
        x,y=(responses[w][r[w]] for w in ('a','b'))
        for who,row in (('a',x),('b',y)):completed[who]+=bool(row['decision'])
        if x['decision'] and y['decision']:
            pairs.append((x['decision'],y['decision']))
            if x['decision'] in LABELS[:2] and y['decision'] in LABELS[:2]:binary.append(pairs[-1])
        # Every record needs explicit final confirmation; agreement is never fabricated adjudication.
        queue.append(dict(adjudication_id=r['a'],redacted_text=r['text'],decision_a=x['decision'],decision_b=y['decision'],
            rationale_a=x['rationale'],rationale_b=y['rationale'],privacy_a=x['privacy_issue'],privacy_b=y['privacy_issue'],
            reason_required='missing' if not (x['decision'] and y['decision']) else 'disagreement_or_uncertain' if x['decision']!=y['decision'] or 'uncertain' in (x['decision'],y['decision']) else 'agreement_confirmation',
            final_decision='',adjudicator_code='',final_rationale='',resolved_privacy='',completed_at_utc=''))
    output.mkdir(parents=True,exist_ok=False)
    result=dict(records=len(mapping),completed=dict(completed),all_categories=agreement(pairs),binary_complete_pairs=agreement(binary),
        binary_pairs_excluded=len(pairs)-len(binary),human_independence='pending separate signed attestations',
        final_decisions=0,note='Agreement is pre-adjudication. Partial-pair estimates are descriptive, not final. Undefined kappa is null, never zero.')
    save(output/'agreement.json',result)
    save(output/'adjudication-basis.json',queue)
    csv_write(output/'adjudication.csv',tuple(queue[0]),queue)
    # Preserve the actual input bytes, including partial returns. Later edits cannot
    # silently replace the pre-adjudication evidence or its source dataset identity.
    evidence=output/'evidence';evidence.mkdir()
    for name,path in {'a.csv':a,'b.csv':b,'mapping.json':review/'coordinator/mapping.json',
                      'packet-manifest.json':review/'coordinator/packet-manifest.json',
                      'attestations.csv':review/'coordinator/attestations.csv',
                      'privacy-release.csv':review/'coordinator/privacy-release.csv'}.items():
        (evidence/name).write_bytes(path.read_bytes())
    save(output/'return-manifest.json',dict(created_utc=now(),
        files={p.relative_to(output).as_posix():sha(p) for p in [*evidence.iterdir(),output/'agreement.json',output/'adjudication-basis.json']},
        source_sha256=packet_manifest['source_sha256']))
    print('Agreement output created; paired decisions:',len(pairs),'; no final labels assigned.')

def validated_adjudication(path):
    manifest=read(path.parent/'return-manifest.json')
    for name,digest in manifest['files'].items():
        if sha(path.parent/name)!=digest:raise ValueError('Frozen return evidence changed; create a new agreement version')
    mapping=read(path.parent/'evidence/mapping.json')
    response_sets={who:read_responses(path.parent/f'evidence/{who}.csv',{m[who]:m['text'] for m in mapping}) for who in ('a','b')}
    mapped={m['a']:m for m in mapping}
    basis={r['adjudication_id']:r for r in read(path.parent/'adjudication-basis.json')}
    with path.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=list(next(iter(basis.values()))):raise ValueError('Unexpected adjudication columns')
        rows=list(reader)
    if any(None in r or any(v is None for v in r.values()) for r in rows):raise ValueError('Malformed adjudication row')
    expected={r['a'] for r in mapping}
    if len(rows)!=len(expected) or {r.get('adjudication_id') for r in rows}!=expected:raise ValueError('Adjudication must cover the assigned cohort once')
    for r in rows:
        for k in ('redacted_text','decision_a','decision_b','rationale_a','rationale_b','privacy_a','privacy_b','reason_required'):
            if r.get(k)!=display(basis[r['adjudication_id']][k]):raise ValueError('Adjudication evidence changed; preserve independent responses')
        decision=r.get('final_decision','')
        if not decision:continue
        if decision not in LABELS or not all(r.get(k,'').strip() for k in ('adjudicator_code','final_rationale','completed_at_utc')) or r.get('resolved_privacy') not in ('yes','no'):
            raise ValueError('Invalid or incomplete adjudication')
        if not r.get('decision_a') or not r.get('decision_b'):raise ValueError('Both independent reviews must precede final adjudication')
        finished=utc(r['completed_at_utc'])
        if finished>utc(now()):raise ValueError('Future adjudication timestamp')
        pair=mapped[r['adjudication_id']]
        for who in ('a','b'):
            response=response_sets[who][pair[who]]
            if finished<utc(response['completed_at_utc']):raise ValueError('Adjudication predates independent responses')
    return rows,mapping,manifest


def adjudicate(path,output):
    private_output(output)
    rows,_,_=validated_adjudication(path)
    final=[r['final_decision'] for r in rows if r['final_decision']]
    save(output,dict(records=len(rows),final_decisions=len(final),pending=len(rows)-len(final),counts=dict(Counter(final)),
        physical_phone_evidence='pending',note='Final decisions do not overwrite historical labels or frozen metrics.'))
    print('Adjudication validation complete; finalized:',len(final))

def json_texts(value):
    if isinstance(value,dict):
        for k,v in value.items():
            if str(k).strip().lower() in TEXT_KEYS and isinstance(v,str) and v.strip():yield v
            elif isinstance(v,(dict,list)):yield from json_texts(v)
    elif isinstance(value,list):
        for v in value:yield from json_texts(v)

def xlsx_rows(data):
    ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        shared=[''.join(e.itertext()) for e in ET.fromstring(z.read('xl/sharedStrings.xml'))] if 'xl/sharedStrings.xml' in z.namelist() else []
        for member in z.namelist():
            if not member.startswith('xl/worksheets/sheet') or not member.endswith('.xml'):continue
            header=None
            for row in ET.fromstring(z.read(member)).findall('.//s:row',ns):
                cells={}
                for cell in row.findall('s:c',ns):
                    col=''.join(c for c in cell.get('r','') if c.isalpha());v=cell.find('s:v',ns)
                    text=v.text or '' if v is not None else ''.join(t.text or '' for t in cell.findall('.//s:t',ns))
                    cells[col]=shared[int(text)] if cell.get('t')=='s' else text
                if header is None:header=cells
                else:yield {header[k]:v for k,v in cells.items() if k in header}

def texts_from_bytes(data,name,inventory,depth=0):
    suffix=Path(name).suffix.lower();count=0
    if name.split('!')[-1].split('/')[-1].lower()=='smsspamcollection':suffix='.tsv'
    if suffix=='.zip':
        if depth>4:raise ValueError('Nested archive depth exceeded')
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for item in z.infolist():
                if item.is_dir() or (Path(item.filename).suffix.lower() not in ('.csv','.tsv','.json','.xlsx','.zip') and Path(item.filename).name.lower()!='smsspamcollection'):continue
                if item.file_size>128*1024*1024:raise ValueError('Oversized historical table; inspect separately')
                yield from texts_from_bytes(z.read(item),name+'!'+item.filename,inventory,depth+1)
        inventory.append(dict(file=name,sha256=hashlib.sha256(data).hexdigest(),kind='archive'))
        return
    if suffix=='.xlsx':values=xlsx_rows(data)
    elif suffix in ('.csv','.tsv'):
        decoded=data.decode('utf-8-sig')
        # UCI SMSSpamCollection is headerless tab-separated label/message data.
        if suffix=='.tsv' and decoded.split('\t',1)[0].lower() in ('ham','spam'):
            values=({'text':r[1]} for r in csv.reader(io.StringIO(decoded),delimiter='\t') if len(r)==2)
        else:values=csv.DictReader(io.StringIO(decoded),delimiter='\t' if suffix=='.tsv' else ',')
    elif suffix=='.json':values=[json.loads(data.decode('utf-8-sig'))]
    else:return
    for row in values:
        for text in json_texts(row):count+=1;yield text
    inventory.append(dict(file=name,sha256=hashlib.sha256(data).hexdigest(),text_values=count,kind='text_table' if count else 'no_text_fields'))

def history(root,output):
    private_output(output);output.mkdir(parents=True,exist_ok=False)
    inventory=[];exact=set();normalized=set();files=[]
    for directory,dirs,names in os.walk(root):
        dirs[:]=sorted(d for d in dirs if d not in {'venv','.venv','base','site-packages','__pycache__','node_modules'}
                       and not (Path(directory)/d).resolve().is_relative_to(output.resolve()))
        for name in sorted(names):
            p=Path(directory)/name
            if p.suffix.lower() not in ('.csv','.tsv','.json','.xlsx','.zip') and p.name.lower()!='smsspamcollection':continue
            files.append(p)
    # All available historical CSV/TSV/JSON/XLSX tables, including source ZIPs and prior review views.
    for p in files:
        if p.stat().st_size>128*1024*1024:raise ValueError('Oversized historical input requires explicit inspection')
        for text in texts_from_bytes(p.read_bytes(),p.relative_to(root).as_posix(),inventory):
            exact.add(hashlib.sha256(text.encode()).hexdigest());key=normalize(clean(text))
            if key:normalized.add(key)
    save(output/'index.json',dict(exact_sha256=sorted(exact),normalized_texts=sorted(normalized)))
    save(output/'inventory.json',dict(root='research/data',files=inventory,index_sha256=sha(output/'index.json'),created_utc=now(),
         limitation='Covers every recognized table in available local archives and research storage, not unavailable or deleted corpora. No-match is not proof of independence.'))
    print('History indexed:',len(files),'local files;',len(normalized),'unique normalized views. No messages logged.')

def utc(value):
    d=datetime.fromisoformat(value.replace('Z','+00:00'))
    if d.tzinfo is None or d.utcoffset().total_seconds()!=0:raise ValueError('UTC timestamp required')
    return d

def matches(text,texts,minimum=.85):
    key=normalize(clean(text));hits=[]
    if not key:return hits
    for i,other in enumerate(texts):
        if 2*min(len(key),len(other))/(len(key)+len(other))<minimum:continue
        sm=SequenceMatcher(None,key,other,autojunk=False)
        reverse=SequenceMatcher(None,other,key,autojunk=False)
        if sm.quick_ratio()>=minimum and max(sm.ratio(),reverse.ratio())>=minimum:hits.append(i)
    return hits

def intake(path,index_dir,freeze_path,output):
    private_output(output);frozen=verify_freeze(freeze_path);index=read(index_dir/'index.json');manifest=read(index_dir/'inventory.json')
    if sha(index_dir/'index.json')!=manifest['index_sha256']:raise ValueError('Historical index changed')
    with path.open(encoding='utf-8-sig',newline='') as stream:
        reader=csv.DictReader(stream)
        if reader.fieldnames!=list(INTAKE):raise ValueError('Unexpected intake columns')
        rows=[r for r in reader if any(r.values())]
    if any(None in r or any(v is None for v in r.values()) for r in rows):raise ValueError('Malformed intake row')
    if len({r['intake_id'] for r in rows})!=len(rows) or any(not r['intake_id'] for r in rows):raise ValueError('Missing or duplicate intake ID')
    output.mkdir(parents=True,exist_ok=False);ledger=[];start=utc(frozen['created_utc']);observed=utc(now())
    norm=index['normalized_texts'];norm_set=set(norm);exact=set(index['exact_sha256'])
    for i,r in enumerate(rows):
        reasons=[];text=r.get('redacted_text','')
        if not text.strip():reasons.append('missing_text')
        elif not normalize(clean(text)):reasons.append('empty_normalized_text')
        try:
            received=utc(r['received_at_utc']);collected=utc(r['collected_at_utc'])
            if not start<received<=collected<=observed:reasons.append('not_documented_post_freeze_receipt')
        except (ValueError,KeyError):reasons.append('invalid_dates')
        for k in ('collector_code','source_use_evidence','receipt_evidence_ref','privacy_reviewer'):
            if not r.get(k,'').strip():reasons.append('missing_'+k)
        for k,required in (('permission_status','approved'),('privacy_review_status','verified'),('prior_model_viewing','no')):
            if r.get(k)!=required:reasons.append(k+'_unresolved')
        key=normalize(clean(text));literal=hashlib.sha256(text.encode()).hexdigest() in exact
        exact_normalized=bool(key) and key in norm_set
        near=[] if literal or exact_normalized else matches(text,norm)
        if literal or exact_normalized or near:reasons.append('historical_overlap')
        within=matches(text,[normalize(clean(other['redacted_text'])) for other in rows])
        if any(j!=i for j in within):reasons.append('within_intake_template_overlap')
        ledger.append(dict(intake_id=r['intake_id'],reasons=reasons,literal_exact=literal,normalized_exact=exact_normalized,
            near_history_indices=near,within_intake_indices=[j for j in within if j!=i],
            status='hold' if reasons else 'candidate_pending_semantic_group_and_evidence_review'))
    save(output/'ledger.json',ledger)
    save(output/'summary.json',dict(records=len(rows),holds=sum(bool(r['reasons']) for r in ledger),
        candidates=sum(not r['reasons'] for r in ledger),human_labels='pending',evaluation='not performed',
        freeze_sha256=sha(freeze_path),historical_index_sha256=sha(index_dir/'index.json'),intake_sha256=sha(path),
        ledger_sha256=sha(output/'ledger.json'),
        note='No predictions run. No-match does not establish fresh or independent data. All candidates require coordinator evidence and semantic-template review.'))
    print('Intake screened:',len(rows),'records; no predictions or labels generated.')

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('prepare');a.add_argument('--source',type=Path);a.add_argument('--review',type=Path)
    sub.add_parser('freeze')
    a=sub.add_parser('agreement');a.add_argument('a',type=Path);a.add_argument('b',type=Path);a.add_argument('output',type=Path);a.add_argument('--review',type=Path)
    a=sub.add_parser('adjudicate');a.add_argument('input',type=Path);a.add_argument('output',type=Path)
    a=sub.add_parser('history');a.add_argument('root',type=Path);a.add_argument('output',type=Path)
    a=sub.add_parser('intake');a.add_argument('input',type=Path);a.add_argument('index',type=Path);a.add_argument('freeze',type=Path);a.add_argument('output',type=Path)
    a=sub.add_parser('verify-freeze');a.add_argument('input',type=Path)
    a=p.parse_args()
    if a.command=='prepare':prepare(a.source,a.review)
    elif a.command=='freeze':freeze()
    elif a.command=='agreement':analyze(a.a,a.b,a.output,a.review)
    elif a.command=='adjudicate':adjudicate(a.input,a.output)
    elif a.command=='history':history(a.root,a.output)
    elif a.command=='intake':intake(a.input,a.index,a.freeze,a.output)
    else:verify_freeze(a.input);print('Frozen models and inference code unchanged.')

if __name__=='__main__':main()
