"""Execute every notebook cell using this interpreter's kernel; preserve failed attempts privately."""
import argparse
import os
from pathlib import Path
import sys
import nbformat
from nbclient import NotebookClient
from ipykernel.kernelspec import install

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',default='runs/bantaytext-20261013/notebook-run')
    args=parser.parse_args()
    path=ROOT/'research/SmishGuard_Model_Training_and_Evaluation.ipynb'
    kernel_root=ROOT/'research/.venv'
    install(prefix=str(kernel_root),kernel_name='smishguard-bantaytext',display_name='SmishGuard research')
    os.environ['JUPYTER_PATH']=str(kernel_root/'share/jupyter')
    os.environ['SMISHGUARD_RUN']=args.run
    # Windows Java/kernel tools need sockets; use TCP for the kernel as usual.
    nb=nbformat.read(path,as_version=4)
    try:
        NotebookClient(nb,timeout=1800,kernel_name='smishguard-bantaytext',resources={'metadata':{'path':str(ROOT/'research')}}).execute()
    except Exception:
        failed=ROOT/'research'/args.run/'failed-notebook.ipynb'
        failed.parent.mkdir(parents=True,exist_ok=True)
        nbformat.write(nb,failed)
        raise
    nb.metadata['kernelspec']=dict(name='python3',display_name='Python 3',language='python')
    nbformat.validate(nb);nbformat.write(nb,path)
    print('Executed all',len(nb.cells),'cells; saved aggregate outputs in',path.name)


if __name__=='__main__':main()
