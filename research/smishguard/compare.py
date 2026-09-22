"""Compare frozen baseline candidates on validation only, then seal one selection."""
import argparse
import hashlib
import json
from pathlib import Path
from .train import main as train_main, write_json

SEALED_FILES = ("research-model.pkl", "splits.json", "run.json", "model.json")


def seals(run):
    return {name:hashlib.sha256((run/name).read_bytes()).hexdigest() for name in SEALED_FILES if (run/name).is_file()}


def verify_selection(run, selection):
    record=json.loads(selection.read_text(encoding="utf-8"))
    if (selection.parent/record["selected_run"]).resolve() != run.resolve() or record["sha256"] != seals(run):
        raise ValueError("Selected run or frozen files changed after validation selection")
    return record


def compare(dataset, output, split="group", seed=20260917, data_history="previously_used", condition="deployment", analyzer="word"):
    output.mkdir(parents=True,exist_ok=False)
    candidates=[]
    split_bytes=None
    for name in ("lr","nb","svm"):
        run=output/name
        train_main([str(dataset),str(run),"--model",name,"--split",split,"--seed",str(seed),"--data-history",data_history,"--condition",condition,"--analyzer",analyzer])
        current=(run/"splits.json").read_bytes()
        if split_bytes is not None and current != split_bytes:
            raise ValueError("Candidates do not share the same split manifest")
        split_bytes=current
        metadata=json.loads((run/"run.json").read_text(encoding="utf-8"))
        candidates.append(dict(model=name, validation_f1=metadata["validation_f1"], validation_pr_auc=metadata["validation_pr_auc"]))
    # Stable tie-break is specified before any results: LR, then NB, then SVM.
    selected=max(candidates,key=lambda row:row["validation_pr_auc"])["model"]
    write_json(output/"selection.json",dict(selected_run=selected, candidates=candidates,
        policy="Highest validation trapezoidal PR-AUC after per-candidate calibration/threshold fitting; ties LR, NB, SVM",
        split=split, sha256=seals(output/selected), test_used=False,
        scope="Baseline candidate selection only; not a thesis winner or deployment approval"))
    return selected


def main():
    p=argparse.ArgumentParser()
    p.add_argument("dataset",type=Path); p.add_argument("output",type=Path)
    p.add_argument("--split",choices=["group","time-group","random","time"],default="group")
    p.add_argument("--seed",type=int,default=20260917)
    p.add_argument("--data-history",choices=["previously_used","prospectively_reserved"],required=True)
    p.add_argument("--condition",choices=["deployment","text-only","text-url","placeholders","shape","punctuation"],default="deployment")
    p.add_argument("--analyzer",choices=["word","char"],default="word")
    args=p.parse_args()
    name=compare(args.dataset,args.output,args.split,args.seed,args.data_history,args.condition,args.analyzer)
    print(f"Validation-selected candidate: {name}. Selection frozen; final test not opened.")


if __name__ == "__main__": main()
