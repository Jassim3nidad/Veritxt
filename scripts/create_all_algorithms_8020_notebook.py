"""Create the local reproduction notebook; replay only after training completes."""
import argparse
import os
from pathlib import Path

import nbformat as nb

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--execute',action='store_true');args=parser.parse_args()
    cells=[nb.v4.new_markdown_cell('''# All algorithms — 80% training / 20% testing

This local notebook covers all 35 standalone score variants, voting ensembles and
stacking models listed in `docs/all-algorithms-8020-20261019/MODEL-GUIDE.md`.
It uses the same 2,734 training and 684 test messages for every model. Existing
completed stages are verified and replayed; set `RUN` to a **new directory** to
perform fresh training. The default training was launched through the CLI, and
this notebook replays its saved evidence. CUDA training uses the existing local
mBERT environment and pinned multilingual cased base. No download is performed.

The corpus and earlier test results were already exposed. This is a retrospective
comparison with inherited labels, source concentration and only nine independent
test components. Rankings are descriptive; no deployment model is selected.
''')]
    cells.append(nb.v4.new_code_cell('''import os, sys, subprocess
from pathlib import Path
import pandas as pd
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents]
            if (p/'research/smishguard/all_algorithms_8020.py').is_file())
sys.path.insert(0, str(ROOT/'research'))
from smishguard import all_algorithms_8020 as a, nb_comparison as n
RUN = ROOT/'research/runs/all-algorithms-8020-20261019/run-v1'
PYTHON = ROOT/'research/data/mbert-20261002/venv/Scripts/python.exe'
def phase(name):
    env = dict(os.environ, PYTHONPATH=str(ROOT/'research'))
    subprocess.run([str(PYTHON), '-u', '-m', 'smishguard.all_algorithms_8020',
                    name, str(RUN)], cwd=ROOT, env=env, check=True)
print('Run:', RUN)
'''))
    cells.append(nb.v4.new_code_cell('''if not RUN.exists():
    phase('prepare')
cfg, rows, splits = a.context(RUN)
audit = n.load(RUN/'data-audit.json')
display(pd.DataFrame(audit['partitions']).T)
print('Fixed classical settings:', len(cfg['matrix']))
'''))
    cells.append(nb.v4.new_code_cell('''if not (RUN/'classical-results.json').exists():
    phase('classical')
print('Completed classical score variants:', len(n.load(RUN/'classical-results.json')))
'''))
    cells.append(nb.v4.new_code_cell('''if not (RUN/'mbert-complete.json').exists():
    phase('mbert')
mbert = n.load(RUN/'mbert-complete.json')
display(pd.DataFrame([dict(fit=s['id'], training_records=s['train_records'],
                          epochs=s['fixed_epoch'], max_length=s['max_length'],
                          seconds=s['seconds']) for s in mbert['summaries']]))
'''))
    cells.append(nb.v4.new_code_cell('''if not (RUN/'freeze.json').exists():
    phase('freeze')
a.verify(RUN)
print('Frozen configurations:', len(n.load(RUN/'entries.json')))
'''))
    cells.append(nb.v4.new_code_cell('''if not (RUN/'test-results.json').exists():
    phase('evaluate')
a.verify(RUN)
results = n.load(RUN/'test-results.json')['results']
table = pd.DataFrame([dict(model=e['id'], **{k:e['test'][k] for k in
        ('accuracy','precision','recall','f1','macro_f1','fpr','fnr')}) for e in results])
display(table.sort_values(['f1','recall'], ascending=False).reset_index(drop=True))
print('Highest observed test F1:', table.loc[table.f1 == table.f1.max(), 'model'].tolist())
'''))
    cells.append(nb.v4.new_code_cell('''for entry in results:
    prediction = n.load(RUN/'test-predictions'/(entry['id']+'.json'))
    assert prediction['indices'] == splits['partitions']['test']
    assert prediction['labels'] == [rows[i]['label'] for i in prediction['indices']]
    assert n.metrics(prediction['labels'], prediction['predictions']) == entry['test']
phase('report')
print('Verified all', len(results), 'saved metric tables and identical test membership.')
print('Aggregate report:', ROOT/'docs/all-algorithms-8020-20261019/RESULTS.md')
'''))
    cells.append(nb.v4.new_markdown_cell('''Training OOF metrics are available in the saved run. The stacking meta model is
trained on base OOF rows; its training fit is not presented as held-out CV.
The raw/sigmoid variants share a classifier, and ensembles share fresh component
fits. Text, vocabulary, weights and row-level predictions remain in private run
folders. The full report explains features, thresholds and limitations. This
notebook does not install a model in the Android app.
'''))
    document=nb.v4.new_notebook(cells=cells,metadata=dict(kernelspec=dict(name='python3',display_name='Python 3',language='python')))
    for cell in document.cells:
        if cell.cell_type=='code':compile(cell.source,'<notebook>','exec')
    nb.validate(document)
    path=ROOT/'research/All_Algorithms_80_20_Comparison.ipynb'
    if args.execute:
        run=ROOT/'research/runs/all-algorithms-8020-20261019/run-v1'
        if not (run/'test-results.json').exists():raise RuntimeError('Complete real training/evaluation before evidence replay')
        from nbclient import NotebookClient
        from ipykernel.kernelspec import install
        install(prefix=str(ROOT/'research/.venv'),kernel_name='smishguard-all-8020',display_name='SmishGuard all algorithms 80/20')
        os.environ['JUPYTER_PATH']=str(ROOT/'research/.venv/share/jupyter')
        NotebookClient(document,timeout=1800,kernel_name='smishguard-all-8020',resources={'metadata':{'path':str(ROOT)}}).execute()
        document.metadata.kernelspec=dict(name='python3',display_name='Python 3',language='python')
        nb.write(document,run/'executed-notebook.ipynb')
    nb.write(document,path)
    print('Executed' if args.execute else 'Created',path)


if __name__=='__main__':main()
