"""Export the frozen fold-0 NB unchanged and prepare private native parity fixtures.

No fitting, threshold selection, masking, or evaluation-based model selection.
Run with research/.venv/Scripts/python.exe from the repository root.
"""
from pathlib import Path
import argparse
import json
import pickle
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import retrain_nb_generalization as g
from smishguard import nb_comparison as n
from smishguard.convert_supplied import unicode_contract, ranges


def prepare(run, output):
    run, output = Path(run).resolve(), Path(output).resolve()
    g.verify(run)
    output.mkdir(parents=True, exist_ok=False)
    source = run/'group-fold-0/original-alpha-0.1/pipeline.pkl'
    pipeline = pickle.loads(source.read_bytes())
    vec, model = pipeline.named_steps['tfidf'], pipeline.named_steps['classifier']
    assert model.alpha == .1 and model.classes_.tolist() == [0, 1]
    assert vec.token_pattern == n.TOKEN_PATTERN and vec.preprocessor is None
    assert vec.get_params()['stop_words'] == n.STOP_WORDS
    n.export_reference(vec, model, dict(algorithm='nb'), output/'model.json')
    export = n.load(output/'model.json')
    export.update(schema_version=9, research_contract='raw-unicode-url-amount-nb-android-v1',
        android_compatible=True, model_version='nb-generalization-20261019-fold0-alpha0.1',
        input_view='raw_sms', unicode=unicode_contract(),
        digit_ranges=ranges(i for i in range(sys.maxunicode+1) if chr(i).isdecimal()),
        whitespace_ranges=ranges(i for i in range(sys.maxunicode+1) if chr(i).isspace()),
        provenance=dict(pipeline_sha256=n.digest(source), freeze_sha256=n.digest(run/'freeze.json'),
            dataset_sha256=n.digest(run/'dataset.json'), training_records=2734, held_out_records=684,
            fold='group-fold-0', selection='predeclared first fold, no score-based selection'),
        evaluation_status='retrospective_unverified_labels', calibration_status='uncalibrated')
    n.save(output/'model.json', export)
    assert len((output/'model.json').read_bytes()) < 8_000_000
    rows = n.load(run/'dataset.json')
    fold = next(f for f in n.load(run/'folds.json')['folds'] if f['id'] == 'group-fold-0')
    assert len(fold['train']) == 2734 and len(fold['test']) == 684
    ledger = n.load(run/'group-fold-0/original-alpha-0.1/predictions.json')
    assert ledger['indices'] == fold['test']
    probes = list(n.PROBES) + [
        ('space', '\x1c\x85\u00a0\u2007\u2028 \t\nΣΟΣ İ 𐐀 café ₱ ٢,٥٠٠.٥٠'),
        ('url_punctuation', 'HTTPS://EXAMPLE.INVALID/Verify?a=99). www.EXAMPLE.invalid, foohttps://x <>'),
        ('number_boundaries', '123abc 12.34abc a123 123.45.67x 1,2x _34 ₱ ٥,٢x $12abc €𑁦.𝟙'),
        ('unicode_words', 'a I _ __ ² Ⅷ 𐐀 𐐨 ΣΟΣ ΟΣΑ ΑΣ́Α İ café a\u0301 𞓐 𠀀'),
        ('stopword_bridging', 'verify the account with yours at no not an a'),
        ('max_length', 'hello ' * 1666 + 'home'),
    ]
    # Exercise every vocabulary term, including exact URL/amount spellings.
    vocabulary = vec.get_feature_names_out().tolist()
    probes += [('vocabulary_'+str(i), ' | '.join(vocabulary[i:i+40])) for i in range(0, len(vocabulary), 40)]
    rng = random.Random(20261019)
    alphabet = 'aA_01. ,<>:/?\t\n₱$€£ΣΟΣİé²Ⅷ٢𝟙𐐀\u2007\u0301'
    probes += [('token_edge_'+str(i), ''.join(rng.choices(alphabet, k=120))) for i in range(200)]
    probes += [('held_out_'+str(i), rows[i]['text']) for i in fold['test']]
    texts = [n.normalize(t) for _, t in probes]
    matrix = vec.transform(texts)
    scores = model.predict_proba(matrix)[:, 1]
    analyzer = vec.build_analyzer()
    records = []
    for j, ((name, text), score) in enumerate(zip(probes, scores)):
        features = dict(zip(matrix[j].indices.tolist(), matrix[j].data.tolist()))
        reference = n.reference_features(export, text)
        assert set(features) == set(reference)
        assert max((abs(v-reference[k]) for k, v in features.items()), default=0) <= 1e-10
        assert abs(float(score)-n.reference_score(export, reference)) <= 1e-10
        records.append(dict(name=name, text=text, terms=analyzer(n.normalize(text)), features=features,
            score=float(score), suspicious=bool(score >= .5)))
    assert max(abs(float(scores[-684+j])-ledger['scores'][j]) for j in range(684)) <= 1e-10
    private = output/'android-test-assets'
    private.mkdir()
    n.save(private/'nb-generalization-cases.json', dict(cases=records, held_out_cases=684))
    # JVM reads the same fixtures; APK test assets contain examples, app assets never do.
    n.save(output/'nb-generalization-cases.json', dict(cases=records, held_out_cases=684))
    destination = ROOT/'android/app/src/nbGeneralization/assets'
    destination.mkdir(parents=True, exist_ok=True)
    (destination/'model.json').write_bytes((output/'model.json').read_bytes())
    n.save(output/'export-manifest.json', dict(model_sha256=n.digest(output/'model.json'),
        source_pipeline_sha256=n.digest(source), fixture_sha256=n.digest(private/'nb-generalization-cases.json'),
        cases=len(records), held_out_cases=684, vocabulary_features=len(vocabulary),
        training_records=2734, threshold=.5, alpha=.1, refitted=False, raw_sms_masking=False))
    g.verify(run)
    print(json.dumps(n.load(output/'export-manifest.json'), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', default=str(ROOT/'research/runs/nb-generalization-20261019/run-v1'))
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    prepare(args.run, args.output)
