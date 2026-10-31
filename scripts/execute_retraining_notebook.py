"""Execute notebook end-to-end using the research kernel; failed attempts stay private."""
import argparse
import os
from pathlib import Path
import nbformat
from nbclient import NotebookClient
from ipykernel.kernelspec import install

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--dataset',default='runs/bantaytext-20261013/notebook-run-v3/dataset.json');p.add_argument('--replay',action='store_true');args=p.parse_args()
    install(prefix=str(ROOT/'research/.venv'),kernel_name='smishguard-retraining',display_name='SmishGuard retraining')
    os.environ['JUPYTER_PATH']=str(ROOT/'research/.venv/share/jupyter')
    os.environ['SMISHGUARD_RETRAIN_RUN']=args.run;os.environ['SMISHGUARD_DATASET']=args.dataset
    os.environ['SMISHGUARD_REPLAY']='1' if args.replay else '0'
    path=ROOT/'research/Model_Training_and_Evaluation.ipynb';nb=nbformat.read(path,as_version=4)
    try:NotebookClient(nb,timeout=1800,kernel_name='smishguard-retraining',resources={'metadata':{'path':str(ROOT/'research')}}).execute()
    except Exception:
        failed=ROOT/'research'/args.run/'failed-notebook.ipynb';failed.parent.mkdir(parents=True,exist_ok=True);nbformat.write(nb,failed);raise
    nb.metadata['kernelspec']=dict(name='python3',display_name='Python 3',language='python')
    nbformat.validate(nb);nbformat.write(nb,path);print('Executed',len(nb.cells),'notebook cells')


if __name__=='__main__':main()
