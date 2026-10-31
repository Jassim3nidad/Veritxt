"""Standalone, retrospective NB comparison. Never writes Android production assets.

This module is embedded verbatim in the Colab notebook. Message-bearing data,
vocabulary, predictions and models stay in a new private run directory.
"""
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
import argparse
import csv
import hashlib
import importlib.metadata
import io
import json
import math
import pickle
import platform
import re
import stat
import sys
import time
import unicodedata
import zipfile

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from threadpoolctl import threadpool_limits

SEED = 42
MEMBER = 'smishguard_dataset_2026-10-12/smishguard_dataset.csv'
SOURCES = ('Kaggle: Tagalog-SMS (ZERO, 2025)',
           'Kaggle: PH Spam + Marketing SMS (Chua, 2022)',
           'Kaggle: Philippine Spam/Scam SMS (bwandowando)')
# Fixed before fitting: conservative English-only removal, shared by A and B.
# Avoid the full English list, which contains Filipino/Taglish words at/may/an,
# and preserve negations and security-warning words. No language detection.
STOP_WORDS = sorted('the these those which whom whose with from yours their theirs yourself yourselves'.split())
TOKEN_PATTERN = r'(?u)https?://[^\s<>]+|www\.[^\s<>]+|[₱$€£]\s?\d+(?:[,.]\d+)*|\b\d+(?:[,.]\d+)*\b|\b\w+\b'
URL = re.compile(r'https?://[^\s<>]+|www\.[^\s<>]+', re.I)
POLICY = dict(primary='validation scam F1', tie_breaks=['scam recall', 'scam precision', 'smaller model bytes', 'configuration ID'],
              threshold='NB posterior >=0.5; SVM margin >=0; no threshold tuning',
              refit='training only; validation never refitted', deployment_approved=False)


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalize(text):
    """Only collapse whitespace. No URL/amount masking, stemming or translation."""
    if not isinstance(text, str):
        raise ValueError('Text must be a string')
    return re.sub(r'\s+', ' ', text).strip()


def read_dataset(path, member=MEMBER):
    path = Path(path)
    if path.suffix.lower() != '.zip':
        raise ValueError('Use the original dataset ZIP to retain its identity/schema')
    with zipfile.ZipFile(path) as z:
        if sum(e.file_size for e in z.infolist()) > 100_000_000:
            raise ValueError('ZIP exceeds 100 MB uncompressed limit')
        for e in z.infolist():
            parts = e.filename.replace('\\', '/').split('/')
            if e.filename.startswith(('/', '\\')) or '..' in parts or ':' in e.filename or stat.S_ISLNK(e.external_attr >> 16):
                raise ValueError('Unsafe ZIP member')
        # Extract only the known CSV, into memory; never execute bundled scripts.
        raw = z.read(member)
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig'), newline=''), strict=True)
    required = {'id', 'text', 'label', 'category', 'language', 'source', 'source_category',
                'sender', 'date', 'template_group', 'label_method', 'confidence', 'needs_review'}
    if not reader.fieldnames or set(reader.fieldnames) != required or len(reader.fieldnames) != len(required):
        raise ValueError('Unexpected October 12 CSV schema')
    rows = list(reader)
    if not rows or any(None in r or any(v is None for v in r.values()) for r in rows):
        raise ValueError('Empty or malformed dataset CSV')
    return rows, dict(zip_sha256=digest(path), member=member,
        csv_sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw), schema=reader.fieldnames,
        extraction='Known CSV read into memory; other ZIP files never executed')


def counts(rows):
    c = Counter(r['label'] for r in rows)
    return dict(records=len(rows), ham=c[0], smishing=c[1], scam_fraction=c[1]/len(rows) if rows else None)


def clean(rows):
    if len({r['id'] for r in rows}) != len(rows) or any(not r['id'] for r in rows):
        raise ValueError('Missing/duplicate record IDs')
    buckets = defaultdict(list)
    for i, r in enumerate(rows):
        buckets[normalize(r['text']).casefold()].append(i)
    # Examine all labels, including unsupported/flagged/source-held records.
    conflicts = {k for k, ii in buckets.items() if len({rows[i]['label'] for i in ii}) > 1}
    retained, ledger, seen = [], [], set()
    mapping = {'ham': 0, 'smishing': 1}
    for r in rows:
        text = normalize(r['text']); key = text.casefold(); reasons = []
        if r['label'] not in mapping:
            reasons.append('unsupported_label_' + r['label'])
        if r['source'] not in SOURCES:
            reasons.append('existing_source_scope_hold')
        if r['needs_review'].lower() not in ('true', 'false'):
            raise ValueError('Unknown needs_review status')
        if r['needs_review'].lower() == 'true':
            reasons.append('flagged_for_label_review')
        if not text or '\x00' in text or '\ufffd' in text or len(text) > 10000:
            reasons.append('empty_malformed_or_overlong')
        if key in conflicts:
            reasons.append('conflicting_normalized_labels')
        if not reasons:
            if key in seen:
                reasons.append('duplicate_normalized_text')
            else:
                seen.add(key)
                retained.append(dict(r, text=text, label=mapping[r['label']], original_label=r['label']))
        ledger.append(dict(id=r['id'], reasons=reasons, text_changed=text != r['text'],
                           original_label=r['label'], key_sha256=hashlib.sha256(key.encode()).hexdigest()))
    audit = dict(input_records=len(rows), input_labels=dict(Counter(r['label'] for r in rows)),
        raw_exact_duplicate_extra_rows=len(rows)-len({r['text'] for r in rows}),
        normalized_duplicate_extra_rows=len(rows)-len(buckets),
        conflicting_normalized_groups=len(conflicts),
        conflicting_record_ids=[rows[i]['id'] for k in conflicts for i in buckets[k]],
        missing={k:sum(not r[k].strip() for r in rows) for k in rows[0]},
        exclusion_reason_counts=dict(Counter(reason for e in ledger for reason in e['reasons'])),
        excluded_records=sum(bool(e['reasons']) for e in ledger), after_cleaning=counts(retained),
        language_before=dict(Counter(r['language'] for r in rows)),
        language_after=dict(Counter(r['language'] for r in retained)),
        sources_after=dict(Counter(r['source'] for r in retained)),
        label_status='Inherited source/rule labels, not independently verified',
        source_policy='Existing three-source research scope; GitHub permission and team consent/use remain unresolved',
        text_policy='Dataset CSV text, whitespace collapsed only; URLs/numbers/currency preserved; no further redaction')
    return retained, ledger, audit


def template_key(text):
    value = URL.sub(' ', text.casefold())
    value = re.sub(r'\d+', ' ', value)
    # Unicode word characters, avoiding the previous ASCII-only grouping gap.
    return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]|_', ' ', value)).strip()


def group_rows(rows):
    texts = [template_key(r['text']) for r in rows]
    hist = [Counter(t) for t in texts]; parent = list(range(len(rows)))
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    def join(i, j):
        parent[root(i)] = root(j)
    for field in ('template_group', 'sender', 'campaign', 'conversation'):
        seen = {}
        for i, r in enumerate(rows):
            v = r.get(field, '')
            if v and v.lower() not in ('unknown', 'nan', 'none'):
                key = v if field == 'template_group' else (r['source'], v)
                if key in seen:
                    join(i, seen[key])
                seen[key] = i
    for i in range(len(rows)):
        for j in range(i):
            if root(i) == root(j):
                continue
            if texts[i] == texts[j]:
                join(i, j); continue
            total = max(1, len(texts[i])+len(texts[j]))
            if 2*min(len(texts[i]), len(texts[j]))/total < .85:
                continue
            if 2*sum(min(v, hist[j].get(k, 0)) for k, v in hist[i].items())/total < .85:
                continue
            if SequenceMatcher(None, texts[i], texts[j], autojunk=False).ratio() >= .85:
                join(i, j)
    return np.array([root(i) for i in range(len(rows))])


def validate_split(rows, groups, split):
    flat = [i for ids in split.values() for i in ids]
    if len(flat) != len(rows) or set(flat) != set(range(len(rows))):
        raise ValueError('Splits must be a disjoint complete cover')
    for p, ids in split.items():
        if {rows[i]['label'] for i in ids} != {0, 1}:
            raise ValueError(p + ' lacks both classes; do not search favorable seeds')
        for q, jj in split.items():
            if p < q and (set(groups[ids]) & set(groups[jj]) or
                {rows[i]['text'].casefold() for i in ids} & {rows[j]['text'].casefold() for j in jj}):
                raise ValueError('Group or text leakage between splits')


def split_rows(rows, groups):
    y = np.array([r['label'] for r in rows])
    if any(len(set(groups[y == c])) < 20 for c in (0, 1)):
        raise ValueError('Need >=20 groups per class for this prespecified split')
    folds = [b for _, b in StratifiedGroupKFold(n_splits=20, shuffle=True, random_state=SEED).split(y, y, groups)]
    split = {p:np.concatenate(folds[a:b]).tolist() for p, a, b in
             [('train', 0, 14), ('validation', 14, 17), ('test', 17, 20)]}
    validate_split(rows, groups, split)
    return split


def vectorizer():
    return TfidfVectorizer(lowercase=True, strip_accents=None, token_pattern=TOKEN_PATTERN,
        stop_words=STOP_WORDS, ngram_range=(1, 2), max_features=None, min_df=1,
        max_df=1.0, norm='l2', use_idf=True, smooth_idf=True, sublinear_tf=False)


def metrics(y, pred):
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    report = classification_report(y, pred, labels=[0, 1], target_names=['ham', 'smishing'],
                                   output_dict=True, zero_division=0)
    return dict(accuracy=float(accuracy_score(y, pred)), precision=report['smishing']['precision'],
        recall=report['smishing']['recall'], f1=report['smishing']['f1-score'],
        macro_f1=float(f1_score(y, pred, average='macro', zero_division=0)),
        fpr=float(fp/(tn+fp)), fnr=float(fn/(fn+tp)),
        confusion_matrix=[[int(tn), int(fp)], [int(fn), int(tp)]], classification_report=report)


def matrix():
    return [dict(id='A-baseline', algorithm='nb', alpha=1.0),
            dict(id='B-proposed', algorithm='nb', alpha=.1),
            *[dict(id='NB-alpha-'+str(a), algorithm='nb', alpha=a) for a in (.01, .5, 2.0)],
            dict(id='SVM-reference', algorithm='svm', C=1.0)]


def predictions(model, x, spec):
    # Use explicit >= for ties consistently in export and inference.
    if spec['algorithm'] == 'nb':
        score = model.predict_proba(x)[:, 1]; threshold = .5
    else:
        score = model.decision_function(x); threshold = 0.
    return np.asarray(score), (score >= threshold).astype(int)


def choose(results):
    return sorted(results, key=lambda r:(-r['validation']['f1'], -r['validation']['recall'],
        -r['validation']['precision'], r['model_bytes'], r['spec']['id']))[0]['spec']['id']


def train(dataset, output, member=MEMBER):
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    rows, identity = read_dataset(dataset, member)
    clean_rows, ledger, audit = clean(rows)
    save(output/'cleaning-ledger.json', ledger); save(output/'dataset.json', clean_rows)
    start = time.perf_counter(); groups = group_rows(clean_rows)
    split = split_rows(clean_rows, groups)
    audit['grouping_seconds'] = time.perf_counter()-start
    audit['groups'] = len(set(groups))
    members = defaultdict(list)
    for i, g in enumerate(groups): members[int(g)].append(i)
    mixed = [ii for ii in members.values() if len({clean_rows[i]['label'] for i in ii}) > 1]
    save(output/'mixed-label-template-review.json', [[clean_rows[i]['id'] for i in ii] for ii in mixed])
    audit['mixed_label_template_groups'] = len(mixed)
    audit['mixed_label_template_records'] = sum(map(len, mixed))
    audit['partitions'] = {p:dict(counts([clean_rows[i] for i in ids]), groups=len(set(groups[ids]))) for p, ids in split.items()}
    audit['group_overlap'] = {p+'-'+q:len(set(groups[split[p]]) & set(groups[split[q]])) for p in split for q in split if p < q}
    audit['normalized_text_overlap'] = {p+'-'+q:len({clean_rows[i]['text'].casefold() for i in split[p]} &
        {clean_rows[j]['text'].casefold() for j in split[q]}) for p in split for q in split if p < q}
    save(output/'data-audit.json', audit)
    save(output/'splits.json', dict(partitions=split, groups=groups.tolist(), seed=SEED,
        policy='20 stratified group folds allocated 14/3/3; approximate 70/15/15, no seed retries',
        grouping='Label-blind URL/number normalized Unicode SequenceMatcher >=.85 connected components plus supplied template/sender metadata'))
    config = dict(seed=SEED, positive_class='smishing', label_mapping={'ham':0, 'smishing':1}, matrix=matrix(),
        policy=POLICY, input_identity=identity, preprocessing=dict(normalization='whitespace collapse then Python Unicode lowercase',
        token_pattern=TOKEN_PATTERN, stop_words=STOP_WORDS, ngram_range=[1, 2], min_df=1, max_features=None,
        tf='raw', idf='smooth', norm='l2', no_language_detection=True),
        history='previously_used; retrospective, no new independent test cohort',
        source_scope=list(SOURCES), selection_uses_test=False)
    save(output/'configuration.json', config)
    save(output/'metadata.json', dict(python=sys.version, unicode=unicodedata.unidata_version, platform=platform.platform(),
        processor=platform.processor(), packages={p:importlib.metadata.version(p) for p in
        ('numpy', 'scipy', 'scikit-learn', 'pandas', 'matplotlib', 'joblib', 'threadpoolctl')},
        implementation_sha256=digest(Path(__file__)), timestamp_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())))
    training = [normalize(clean_rows[i]['text']) for i in split['train']]
    validation = [normalize(clean_rows[i]['text']) for i in split['validation']]
    yt = [clean_rows[i]['label'] for i in split['train']]; yv = [clean_rows[i]['label'] for i in split['validation']]
    results = []
    with threadpool_limits(limits=1):
        for spec in matrix():
            folder = output/spec['id']; folder.mkdir()
            start = time.perf_counter(); vec = vectorizer(); xt = vec.fit_transform(training)
            vec_seconds = time.perf_counter()-start
            model = MultinomialNB(alpha=spec['alpha']) if spec['algorithm'] == 'nb' else LinearSVC(C=spec['C'], random_state=SEED, dual='auto', max_iter=10000)
            start = time.perf_counter(); model.fit(xt, yt); fit_seconds = time.perf_counter()-start
            if list(model.classes_) != [0, 1]: raise ValueError('Positive-class orientation changed')
            (folder/'vectorizer.pkl').write_bytes(pickle.dumps(vec, protocol=5))
            (folder/'model.pkl').write_bytes(pickle.dumps(model, protocol=5))
            score, pred = predictions(model, vec.transform(validation), spec)
            save(folder/'validation-predictions.json', dict(indices=split['validation'], labels=yv, scores=score.tolist(), predictions=pred.tolist()))
            results.append(dict(spec=spec, validation=metrics(yv, pred), vectorizer_seconds=vec_seconds,
                classifier_seconds=fit_seconds, training_seconds=vec_seconds+fit_seconds,
                model_bytes=(folder/'model.pkl').stat().st_size, vectorizer_bytes=(folder/'vectorizer.pkl').stat().st_size,
                features=len(vec.vocabulary_)))
    selected = choose(results); best_nb = choose([r for r in results if r['spec']['algorithm'] == 'nb'])
    save(output/'validation-results.json', results)
    save(output/'selection.json', dict(selected=selected, best_nb=best_nb, policy=POLICY,
        test_evaluation_ids=list(dict.fromkeys(['A-baseline', 'B-proposed', 'SVM-reference', best_nb, selected]))))
    write_csv(output/'hyperparameters.csv', [dict(id=r['spec']['id'], alpha=r['spec'].get('alpha'),
        **{k:r['validation'][k] for k in ('precision', 'recall', 'f1', 'macro_f1', 'fpr', 'fnr')}) for r in results])
    # Freeze every training/selection input and artifact before evaluating test.
    files = {p.relative_to(output).as_posix():digest(p) for p in output.rglob('*') if p.is_file()}
    save(output/'freeze.json', dict(dataset_sha256=digest(dataset), implementation_sha256=digest(Path(__file__)), files=files))
    print('Fitting and validation selection complete:', selected, '; final test not transformed')
    return audit


def write_csv(path, rows):
    with Path(path).open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def verify_freeze(dataset, output):
    output = Path(output); freeze = load(output/'freeze.json')
    if digest(dataset) != freeze['dataset_sha256'] or digest(Path(__file__)) != freeze['implementation_sha256']:
        raise ValueError('Frozen dataset or implementation changed')
    for name, sha in freeze['files'].items():
        if digest(output/name) != sha: raise ValueError('Frozen artifact changed: '+name)


def export_reference(vec, model, spec, output):
    """Portable research specification, deliberately incompatible with ModelLoader."""
    if spec['algorithm'] == 'nb':
        weights = model.feature_log_prob_[1]-model.feature_log_prob_[0]
        bias = model.class_log_prior_[1]-model.class_log_prior_[0]
    else:
        weights = model.coef_[0]; bias = model.intercept_[0]
    save(output, dict(schema_version=8, research_contract='raw-unicode-url-amount-nb-comparison-v1',
        algorithm=spec['algorithm'], classes=['ham', 'smishing'], positive_class='smishing',
        vocabulary=vec.get_feature_names_out().tolist(), idf=vec.idf_.tolist(), weights=weights.tolist(), bias=float(bias),
        token_pattern=TOKEN_PATTERN, stop_words=STOP_WORDS, ngram_range=[1, 2],
        unicode_version=unicodedata.unidata_version, normalize='collapse Unicode whitespace, Python Unicode lowercase',
        tf='raw', norm='l2', score='sigmoid log odds' if spec['algorithm']=='nb' else 'margin',
        threshold=.5 if spec['algorithm']=='nb' else 0., threshold_comparison='greater_or_equal',
        probability_approved=False, automatic_warnings_approved=False, android_compatible=False))


def reference_features(export, text):
    """Independent JSON inference: no fitted sklearn vectorizer or model required."""
    tokens = [t for t in re.findall(export['token_pattern'], normalize(text).lower()) if t not in export['stop_words']]
    terms = tokens + [' '.join(tokens[i:i+2]) for i in range(len(tokens)-1)]
    vocabulary = {t:i for i, t in enumerate(export['vocabulary'])}
    values = {vocabulary[t]:count*export['idf'][vocabulary[t]] for t, count in Counter(terms).items() if t in vocabulary}
    norm = math.sqrt(sum(v*v for v in values.values()))
    return {i:v/norm for i, v in values.items()} if norm else {}


def reference_score(export, features):
    margin = export['bias']+sum(export['weights'][i]*v for i, v in features.items())
    if export['algorithm'] == 'nb':
        return 1/(1+math.exp(-margin)) if margin >= 0 else math.exp(margin)/(1+math.exp(margin))
    return margin


def reference_infer(export, text):
    """Offline engineering wrapper; abstention is separate from research metrics."""
    if not isinstance(text, str) or len(text) > 10000 or '\x00' in text or any(0xd800 <= ord(c) <= 0xdfff for c in text):
        return dict(status='invalid_input', raw_score=None, suspicious=None, probability_approved=False)
    features = reference_features(export, text)
    score = reference_score(export, features)
    return dict(status='assessed' if features else 'unable_to_assess', raw_score=score,
        suspicious=score >= export['threshold'] if features else None, probability_approved=False)


PROBES = [('empty', ''), ('punctuation', '???'), ('random', 'qzxv qvzzx jklpq'),
    ('short', 'ok'), ('numeric', '1234567890'), ('url_only', 'https://example.invalid/verify?a=99'),
    ('ordinary_english', 'Please bring bread when you come home.'),
    ('ordinary_tagalog', 'Kumain ka na ba? Nasa bahay na ako.'),
    ('ordinary_taglish', 'Ma late ako sa meeting, traffic pa dito.'),
    ('bank_notice', 'Your OTP is 123456. Do not share it with anyone.'),
    ('fictional_scam_english', 'Your bank account is suspended. Verify your PIN at https://example.invalid/account'),
    ('fictional_scam_tagalog', 'May natanggap kang ₱5,000! Ibigay ang OTP at PIN sa https://example.invalid/claim'),
    ('fictional_scam_taglish', 'GCash mo blocked na. Verify your account now sa https://example.invalid/login'),
    ('recognizable_fragments', 'win claim verify account'), ('unicode', 'ΣΟΣ İ café ₱2,500.50 a at may an no not')]


def inference_checks(vec, model, spec, export, texts):
    # Frozen test texts are used only for engineering parity, never model changes.
    synthetic = PROBES + [('seeded_noise_'+str(i), ''.join(np.random.default_rng(SEED+i).choice(list('qzxvjkw'), size=32))) for i in range(100)]
    probes = [t for _, t in synthetic]+texts
    x = vec.transform([normalize(t) for t in probes]); score, pred = predictions(model, x, spec)
    max_feature, max_score = 0., 0.; review = []
    for j, text in enumerate(probes):
        feat = reference_features(export, text); expected = dict(zip(x[j].indices.tolist(), x[j].data.tolist()))
        max_feature = max(max_feature, max((abs(feat.get(k,0)-expected.get(k,0)) for k in feat.keys() | expected.keys()), default=0))
        s = reference_score(export, feat); max_score = max(max_score, abs(s-float(score[j])))
        if (s >= export['threshold']) != bool(pred[j]): raise ValueError('JSON decision parity failed')
        if j < len(synthetic):
            wrapped = reference_infer(export, text)
            if bool(feat) != (wrapped['status'] == 'assessed'):
                raise ValueError('Reference abstention status mismatch')
            review.append(dict(name=synthetic[j][0], text=text, raw_score=float(score[j]), recognized_features=int(x[j].nnz),
                diagnostic_status='abstain_zero_features' if x[j].nnz == 0 else 'score_is_uncalibrated',
                suspicious=bool(pred[j])))
    if max_feature > 1e-10 or max_score > 1e-10: raise ValueError('JSON parity tolerance exceeded')
    invalid = {name:reference_infer(export, text)['status'] for name, text in
               [('none', None), ('nul', '\x00'), ('unpaired_surrogate', '\ud800'), ('overlong', 'x'*10001)]}
    if set(invalid.values()) != {'invalid_input'}: raise ValueError('Invalid input guard failed')
    return dict(cases=len(probes), synthetic_cases=len(synthetic), frozen_test_cases=len(texts), invalid_input_checks=invalid,
        max_feature_error=max_feature, max_score_error=max_score, probes=review,
        note='Python JSON reference parity only; Android scorer cannot load schema 8. Zero features returns class prior/margin, not evidence of safety or fraud.')


def evaluate(dataset, output):
    output = Path(output); verify_freeze(dataset, output)
    # Exclusive marker prevents rerunning even if evaluation is interrupted.
    with (output/'test-evaluation-started.json').open('x', encoding='utf-8') as f:
        json.dump(dict(selection_sha256=digest(output/'selection.json')), f)
    rows = load(output/'dataset.json'); split = load(output/'splits.json')['partitions']
    selection = load(output/'selection.json'); validation = load(output/'validation-results.json')
    ids = split['test']; texts = [normalize(rows[i]['text']) for i in ids]; y = [rows[i]['label'] for i in ids]
    results = []
    with threadpool_limits(limits=1):
        for name in selection['test_evaluation_ids']:
            item = next(r for r in validation if r['spec']['id'] == name); spec = item['spec']; folder = output/name
            vec = pickle.loads((folder/'vectorizer.pkl').read_bytes()); model = pickle.loads((folder/'model.pkl').read_bytes())
            x = vec.transform(texts); score, pred = predictions(model, x, spec)
            item = dict(item, test=metrics(y, pred))
            save(folder/'test-predictions.json', dict(indices=ids, labels=y, scores=score.tolist(), predictions=pred.tolist()))
            save(folder/'classification-report.json', item['test']['classification_report'])
            save(folder/'confusion-matrix.json', item['test']['confusion_matrix'])
            # Warm-up followed by one-message transform + score; host benchmark.
            predictions(model, vec.transform(texts[:1]), spec)
            durations = []
            for t in (texts[:100]*3):
                start = time.perf_counter(); predictions(model, vec.transform([t]), spec)
                durations.append((time.perf_counter()-start)*1000)
            item['host_inference_ms'] = dict(p50=float(np.median(durations)), p95=float(np.quantile(durations,.95)),
                repetitions=len(durations), scope='single-message normalization already applied; TF-IDF and classifier, warm host; not Android latency')
            subgroup = {}
            for language in sorted({rows[i]['language'] for i in ids}):
                ii = [j for j, i in enumerate(ids) if rows[i]['language'] == language]
                yy = [y[j] for j in ii]; support = dict(Counter(yy))
                subgroup[language] = dict(records=len(ii), ham=support.get(0,0), smishing=support.get(1,0),
                    metrics=metrics(yy, pred[ii]) if min(support.get(c,0) for c in (0,1)) >= 5 and len(ii)>=20 else None)
            item['language'] = subgroup
            export_reference(vec, model, spec, folder/'candidate-model.json')
            checks = inference_checks(vec, model, spec, load(folder/'candidate-model.json'), texts)
            save(folder/'inference-checks.json', checks)
            item['candidate_json_bytes'] = (folder/'candidate-model.json').stat().st_size
            results.append(item)
    save(output/'test-results.json', dict(selected=selection['selected'], results=results,
        interpretation='Retrospective inherited-label comparison. Selection sealed before this run used test data; historical exposure remains.'))
    write_csv(output/'comparison.csv', [dict(id=r['spec']['id'], **{k:r['test'][k] for k in
        ('accuracy','precision','recall','f1','macro_f1','fpr','fnr')}, training_seconds=r['training_seconds'],
        model_bytes=r['model_bytes'], vectorizer_bytes=r['vectorizer_bytes'],
        inference_p50_ms=r['host_inference_ms']['p50'], inference_p95_ms=r['host_inference_ms']['p95']) for r in results])
    print('Locked test comparison complete. Research selection remains', selection['selected'], '; production unchanged.')


def plots(output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    output = Path(output); results = load(output/'test-results.json')['results']; audit = load(output/'data-audit.json')
    fig, axes = plt.subplots(1, len(results), figsize=(4*len(results), 3.7), squeeze=False)
    for ax, r in zip(axes[0], results):
        cm = r['test']['confusion_matrix']; ax.imshow(cm, cmap='Blues')
        for i in range(2):
            for j in range(2): ax.text(j,i,str(cm[i][j]),ha='center',va='center')
        ax.set(xticks=[0,1], yticks=[0,1], xticklabels=['ham','scam'], yticklabels=['ham','scam'],
               title=r['spec']['id'], xlabel='Predicted', ylabel='Actual')
    fig.tight_layout(); fig.savefig(output/'confusion-matrices.png', dpi=160); plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(12,4))
    x = np.arange(len(results))
    for offset, key in enumerate(('precision','recall','f1')):
        axes[0].bar(x+(offset-1)*.25,[r['test'][key] for r in results],.25,label=key)
    axes[0].set(xticks=x,xticklabels=[r['spec']['id'] for r in results],ylim=(0,1.05),title='Retrospective scam-class metrics'); axes[0].legend()
    names = list(audit['partitions']); x = np.arange(len(names))
    for offset, key in enumerate(('ham','smishing')):
        axes[1].bar(x+(offset-.5)*.35,[audit['partitions'][n][key] for n in names],.35,label=key)
    axes[1].set(xticks=x,xticklabels=names,title='Grouped split support'); axes[1].legend()
    fig.tight_layout(); fig.savefig(output/'comparison.png', dpi=160); plt.close(fig)


def main():
    p = argparse.ArgumentParser(); p.add_argument('phase', choices=['train','evaluate','plots'])
    p.add_argument('dataset', type=Path); p.add_argument('output', type=Path); p.add_argument('--member', default=MEMBER)
    a = p.parse_args()
    if a.phase == 'train': train(a.dataset, a.output, a.member)
    elif a.phase == 'evaluate': evaluate(a.dataset, a.output)
    else: plots(a.output)


if __name__ == '__main__': main()
