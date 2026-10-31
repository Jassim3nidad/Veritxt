# All-algorithm 80/20 retraining — 19 October 2026

**Highest observed test F1:** latest-B-proposed-raw.

All 35 configurations were freshly retrained or constructed from freshly fitted components on the identical 2,734 training records. All use the identical 684 test records (611 ham, 73 smishing). No old fitted classifier or transformer checkpoint was substituted for retraining. The local pretrained mBERT base initializes every fresh full/fold fine-tune. The earlier NB-only 80/20 experiment is preserved.

This is a retrospective extension after earlier test results were already viewed. Fixed historical settings and default thresholds were recorded before fitting; there is no newly untouched test or overall deployment selection. Rankings below are descriptive. The same constraints that produced 79.9883%/20.0117% membership preserve whole groups and class counts, but yield only nine test components, source concentration, and uneven training CV folds. Do not interpret 684 rows as independent campaigns. Inherited source/rule labels remain unverified.

| Configuration | Training OOF F1 | Test accuracy | Scam precision | Scam recall | Scam F1 | TN/FP/FN/TP |
|---|---:|---:|---:|---:|---:|---|
| latest-B-proposed-raw | 86.87% | 99.71% | 100.00% | 97.26% | 98.61% | 611/0/2/71 |
| latest-NB-alpha-0.01-raw | 89.76% | 99.56% | 96.05% | 100.00% | 97.99% | 608/3/0/73 |
| vote-legacy-lr+legacy-nb+mbert | 91.14% | 99.56% | 100.00% | 95.89% | 97.90% | 611/0/3/70 |
| legacy-nb-sigmoid | 87.78% | 99.42% | 96.00% | 98.63% | 97.30% | 608/3/1/72 |
| vote-legacy-svm+legacy-nb+mbert | 92.17% | 99.42% | 100.00% | 94.52% | 97.18% | 611/0/4/69 |
| vote-legacy-nb+mbert | 81.82% | 99.27% | 93.59% | 100.00% | 96.69% | 606/5/0/73 |
| vote-legacy-svm+mbert | 82.06% | 99.27% | 93.59% | 100.00% | 96.69% | 606/5/0/73 |
| AE-E-raw | 87.20% | 99.27% | 94.74% | 98.63% | 96.64% | 607/4/1/72 |
| AE-E-sigmoid | 85.71% | 99.27% | 94.74% | 98.63% | 96.64% | 607/4/1/72 |
| stack-mbert+legacy-svm+legacy-nb | — | 99.27% | 100.00% | 93.15% | 96.45% | 611/0/5/68 |
| vote-legacy-lr+mbert | 80.49% | 98.98% | 91.25% | 100.00% | 95.42% | 604/7/0/73 |
| vote-legacy-lr+legacy-svm+mbert | 90.68% | 98.98% | 98.53% | 91.78% | 95.04% | 610/1/6/67 |
| vote-legacy-lr+legacy-svm+legacy-nb+mbert | 90.81% | 98.98% | 100.00% | 90.41% | 94.96% | 611/0/7/66 |
| mbert | 78.61% | 98.83% | 90.12% | 100.00% | 94.81% | 603/8/0/73 |
| stack-legacy-lr+legacy-svm+legacy-nb | — | 98.68% | 98.48% | 89.04% | 93.53% | 610/1/8/65 |
| knn-raw | 81.60% | 98.54% | 88.89% | 98.63% | 93.51% | 602/9/1/72 |
| AE-C-raw | 88.16% | 98.25% | 86.75% | 98.63% | 92.31% | 600/11/1/72 |
| AE-C-sigmoid | 87.71% | 98.10% | 87.50% | 95.89% | 91.50% | 601/10/3/70 |
| latest-SVM-reference-raw | 78.94% | 98.25% | 98.41% | 84.93% | 91.18% | 610/1/11/62 |
| AE-D-sigmoid | 81.02% | 97.66% | 91.30% | 86.30% | 88.73% | 605/6/10/63 |
| AE-A-sigmoid | 76.89% | 97.37% | 89.86% | 84.93% | 87.32% | 604/7/11/62 |
| AE-B-raw | 84.73% | 97.08% | 82.72% | 91.78% | 87.01% | 597/14/6/67 |
| AE-D-raw | 82.14% | 96.78% | 82.28% | 89.04% | 85.53% | 597/14/8/65 |
| AE-B-sigmoid | 81.82% | 96.64% | 82.89% | 86.30% | 84.56% | 598/13/10/63 |
| legacy-svm-sigmoid | 87.11% | 96.93% | 98.15% | 72.60% | 83.46% | 610/1/20/53 |
| vote-legacy-svm+legacy-nb | 90.35% | 96.93% | 98.15% | 72.60% | 83.46% | 610/1/20/53 |
| AE-A-raw | 80.07% | 96.35% | 81.58% | 84.93% | 83.22% | 597/14/11/62 |
| vote-legacy-lr+legacy-svm+legacy-nb | 88.31% | 96.64% | 98.08% | 69.86% | 81.60% | 610/1/22/51 |
| vote-legacy-lr+legacy-nb | 85.88% | 96.64% | 100.00% | 68.49% | 81.30% | 611/0/23/50 |
| vote-legacy-lr+legacy-svm | 85.02% | 96.49% | 96.23% | 69.86% | 80.95% | 609/2/22/51 |
| legacy-lr-sigmoid | 84.98% | 95.47% | 85.00% | 69.86% | 76.69% | 602/9/22/51 |
| latest-NB-alpha-0.5-raw | 52.79% | 95.61% | 100.00% | 58.90% | 74.14% | 611/0/30/43 |
| random-forest-raw | 74.03% | 94.44% | 84.31% | 58.90% | 69.35% | 603/8/30/43 |
| latest-A-baseline-raw | 28.91% | 92.98% | 100.00% | 34.25% | 51.02% | 611/0/48/25 |
| latest-NB-alpha-2.0-raw | 4.71% | 89.33% | 0.00% | 0.00% | 0.00% | 611/0/73/0 |

A–E reproduce the previous family-winning hyperparameters: A word LR, B word Linear SVM, C word+character Linear SVM, D word+character LR, E word NB. Each is compared with native/raw and training-OOF sigmoid scores at fixed default thresholds; these are not the older validation-tuned thresholds. Latest NB variants and SVM preserve the raw-URL/currency tokenizer and conservative stopwords. Legacy LR/SVM/NB use sg-ascii-v1 normalization, unigram TF-IDF and fixed C=10 / alpha=.1; their standalone sigmoids are training-only. RF uses 200 balanced trees; KNN uses k=5, both with the original 5,000-feature Unicode word-bigram settings. Different feature paths are explicit model configurations, not an isolated estimator-only experiment.

mBERT uses the pinned multilingual cased base, two fixed epochs, Adafactor 2e-5, accumulation 8, microbatch 1, deterministic CUDA float16 and fit-only p95 lengths capped at 256. It receives the same eligible CSV messages with case preserved and its native tokenizer, rather than TF-IDF. No held-out checkpoint selection is performed. This updated text view and allocation differ from the older redacted mBERT experiment.

All 11 equal-weight soft votes over legacy LR/SVM/NB/mBERT are included. LR/NB/mBERT supply native posteriors; SVM supplies a training-OOF sigmoid. For OOF SVM probability predictions, each outer fit uses a separate inner grouped sigmoid. The two historical LR meta stacks use the same full-training OOF base probability rows, with fold-local features and independent mBERT base fits. Meta training fit is not presented as held-out CV; the stack rows therefore show no training OOF F1. Ensemble ties map to ham; standalone ties map to smishing.

All saved test metrics were recomputed from frozen predictions. Test membership, source hashes, fitted artifacts and protocol were checked before/after the exclusive test evaluation. Full models, message text, vocabularies and predictions stay private under C:/Users/Jassim Trinidad/OneDrive/Desktop/smishguard/research/runs/all-algorithms-8020-20261019/run-v1. Source terms/attribution remain in ../source-evidence.md. No APK or app model was changed. XLM-R has not previously been trained; mBERT quantization is an inference derivative.

Reproduction (use a new run directory; mBERT requires the existing local CUDA environment/base):

```powershell
$env:PYTHONPATH='research'
$py='research/data/mbert-20261002/venv/Scripts/python.exe'
$run='research/runs/all-algorithms-8020-20261019/NEW-RUN'
& $py -m smishguard.all_algorithms_8020 prepare $run
& $py -m smishguard.all_algorithms_8020 classical $run
& $py -m smishguard.all_algorithms_8020 mbert $run
& $py -m smishguard.all_algorithms_8020 freeze $run
& $py -m smishguard.all_algorithms_8020 evaluate $run
& $py -m smishguard.all_algorithms_8020 report $run
```
