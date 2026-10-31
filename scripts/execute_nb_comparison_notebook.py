"""Execute the complete comparison and retain the exact executed notebook privately."""
import argparse
import os
from pathlib import Path
import nbformat
from nbclient import NotebookClient
from ipykernel.kernelspec import install

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--dataset', type=Path, default=ROOT/'research/data/newdata-20261013/smishguard_dataset_2026-10-12.zip')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); output = a.output.resolve()
    if output.exists(): raise FileExistsError('Use a new run directory')
    install(prefix=str(ROOT/'research/.venv'), kernel_name='smishguard-nb-comparison', display_name='SmishGuard NB comparison')
    os.environ['JUPYTER_PATH'] = str(ROOT/'research/.venv/share/jupyter')
    os.environ['SMISHGUARD_NB_DATASET'] = str(a.dataset.resolve())
    os.environ['SMISHGUARD_NB_OUTPUT'] = str(output)
    path = ROOT/'research/NB_Baseline_Proposed_Comparison.ipynb'
    nb = nbformat.read(path, as_version=4)
    try:
        NotebookClient(nb, timeout=1800, kernel_name='smishguard-nb-comparison',
            resources={'metadata':{'path':str(ROOT)}}).execute()
    except Exception:
        output.mkdir(parents=True, exist_ok=True)
        nbformat.write(nb, output/'failed-notebook.ipynb'); raise
    nb.metadata.kernelspec = dict(name='python3', display_name='Python 3', language='python')
    nbformat.validate(nb)
    nbformat.write(nb, path); nbformat.write(nb, output/'executed-notebook.ipynb')
    # Preserve the embedded source and its actual byte identity.
    source_cell = next(c.source for c in nb.cells if c.cell_type == 'code' and 'IMPLEMENTATION_SOURCE =' in c.source)
    import ast
    assignment = next(n for n in ast.parse(source_cell).body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id=='IMPLEMENTATION_SOURCE' for t in n.targets))
    (output/'implementation.py').write_text(ast.literal_eval(assignment.value), encoding='utf-8')
    print('Executed', len(nb.cells), 'cells:', output)


if __name__ == '__main__': main()
