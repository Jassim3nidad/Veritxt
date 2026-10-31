"""Verify frozen notebook evidence without fitting or selecting another model."""
import argparse
import ast
import importlib.util
import re
from pathlib import Path
import nbformat

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('run', type=Path)
    parser.add_argument('--previous', type=Path)
    parser.add_argument('--public', type=Path, default=ROOT/'docs/nb-comparison-20261016')
    args = parser.parse_args(); run = args.run.resolve()
    # Use the exact trusted source snapshot, including its native newline bytes.
    # The notebook may have been executed on a different OS than this checkout.
    spec = importlib.util.spec_from_file_location('frozen_nb_comparison', run/'implementation.py')
    experiment = importlib.util.module_from_spec(spec); spec.loader.exec_module(experiment)
    dataset = ROOT/'research/data/newdata-20261013/smishguard_dataset_2026-10-12.zip'
    experiment.verify_freeze(dataset, run)
    nb = nbformat.read(run/'executed-notebook.ipynb', as_version=4); nbformat.validate(nb)
    code = [c for c in nb.cells if c.cell_type=='code']
    assert [c.execution_count for c in code] == list(range(1,len(code)+1))
    assert not any(o.output_type=='error' for c in code for o in c.outputs)
    embedded = next(c.source for c in code if 'IMPLEMENTATION_SOURCE =' in c.source)
    assignment = next(node for node in ast.parse(embedded).body if isinstance(node, ast.Assign) and
        any(isinstance(t, ast.Name) and t.id=='IMPLEMENTATION_SOURCE' for t in node.targets))
    assert ast.literal_eval(assignment.value) == (ROOT/'research/smishguard/nb_comparison.py').read_text(encoding='utf-8')
    assert experiment.digest(run/'implementation.py') == experiment.load(run/'metadata.json')['implementation_sha256']
    assert experiment.digest(run/'executed-notebook.ipynb') == experiment.digest(ROOT/'research/NB_Baseline_Proposed_Comparison.ipynb')
    manifest = experiment.load(args.public/'evidence-manifest.json')
    for name, sha in manifest['public_files'].items():
        assert experiment.digest(args.public/name) == sha, name
    selection = experiment.load(run/'selection.json')
    for result in experiment.load(run/'test-results.json')['results']:
        prediction = experiment.load(run/result['spec']['id']/'test-predictions.json')
        assert experiment.metrics(prediction['labels'], prediction['predictions']) == result['test']
    if args.previous:
        for name in ['splits.json','selection.json',*[name+'/test-predictions.json' for name in selection['test_evaluation_ids']]]:
            assert experiment.load(args.previous/name) == experiment.load(run/name), name
    test_log = run.parent/'research-tests.log'; text = test_log.read_text(encoding='utf-8',errors='replace')
    total = re.search(r'Ran (\d+) tests in ',text)
    assert total and re.search(r'^OK\s*$',text,re.M), 'Research tests must have passed'
    experiment.save(run/'completion-verification.json', dict(freeze_verified=True, notebook_valid=True,
        embedded_source_matches_live=True, published_hashes_verified=True, metrics_recomputed_from_frozen_predictions=True,
        previous_run_predictions_identical=bool(args.previous), research_tests=int(total.group(1)),
        research_test_failures=0, research_test_log_sha256=experiment.digest(test_log),
        source_note='Exact saved source preserves native newline encoding; use this snapshot for byte-level freeze verification.'))
    print('PASS: frozen data/source/artifacts/selection, executed notebook, public hashes and all saved classification metrics.')
    if args.previous: print('PASS: two fresh fits have identical splits, selection and every evaluated test score/prediction.')
    print('Research regression tests:',total.group(1),'passed. No Android runtime compatibility is claimed.')


if __name__ == '__main__': main()
