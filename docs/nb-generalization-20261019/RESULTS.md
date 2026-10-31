# NB generalization audit and retraining — 19 October 2026

The earlier 99.71% result came from 684 test rows but only nine independent components; 606 rows (88.60%) belonged to one component. Exact-text overlap: 0; stored template-group overlap: 0. This is evidence of a concentrated evaluation, not proof that the model memorized exact test messages. The earlier best-algorithm claim was stronger than this evidence supports.

Five disjoint, whole-group tests each use integer-rounded 80% training / 20% testing. Every eligible message is predicted once without being used by that model. Group counts are balanced before fitting; no model score enters allocation. Three additional source-held-out fits remove all related groups from training. Source holdouts are stress tests with different fractions, not additional 80/20 experiments. All labels/corpus remain historically exposed; this does not create a fresh prospective test.

| Fixed condition | Mean training accuracy | Group CV accuracy | Scam precision | Scam recall | Scam F1 | Fold F1 range | Equal-group accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|
| original-alpha-0.1 | 99.94% | 98.07% | 100.00% | 81.82% | 90.00% | 82.26%–97.14% | 82.20% |
| reduced-alpha-0.1 | 99.71% | 97.72% | 94.95% | 82.92% | 88.53% | 79.37%–95.89% | 83.31% |
| reduced-alpha-1 | 97.81% | 95.79% | 100.00% | 60.33% | 75.26% | 60.95%–90.08% | 66.71% |
| source-only | — | 93.86% | 100.00% | 42.15% | 59.30% | 58.82%–59.62% | 70.93% |
| permuted-label | — | 89.23% | 22.22% | 0.55% | 1.08% | 0.00%–2.70% | 89.40% |

| Group fold | Training rows | Test rows | Test ham/scam | Test components |
|---|---:|---:|---:|---:|
| group-fold-0 | 2734 | 684 | 611/73 | 60 |
| group-fold-1 | 2734 | 684 | 611/73 | 60 |
| group-fold-2 | 2734 | 684 | 611/73 | 60 |
| group-fold-3 | 2735 | 683 | 611/72 | 60 |
| group-fold-4 | 2735 | 683 | 611/72 | 60 |

An all-ham classifier gets 89.38% accuracy and zero scam F1. Source-only NB receives source identity with no message text. The label-permutation model is a deliberately randomized negative control, evaluated against its separately permuted labels; it is not a phishing-quality estimate or a permutation significance test.

| Entire held-out source | Model | Training rows | Purged related rows | Ham/scam test support | Accuracy | Recall | Scam F1 | FPR |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Kaggle: PH Spam + Marketing SMS (Chua, 2022) | original-alpha-0.1 | 1731 | 625 | 906/156 | 94.26% | 60.90% | 75.70% | 0.00% |
| Kaggle: PH Spam + Marketing SMS (Chua, 2022) | reduced-alpha-0.1 | 1731 | 625 | 906/156 | 95.86% | 80.77% | 85.14% | 1.55% |
| Kaggle: PH Spam + Marketing SMS (Chua, 2022) | reduced-alpha-1 | 1731 | 625 | 906/156 | 89.17% | 26.28% | 41.62% | 0.00% |
| Kaggle: Philippine Spam/Scam SMS (bwandowando) | original-alpha-0.1 | 3155 | 110 | 0/153 | 49.02% | 49.02% | 65.79% | not estimable |
| Kaggle: Philippine Spam/Scam SMS (bwandowando) | reduced-alpha-0.1 | 3155 | 110 | 0/153 | 53.59% | 53.59% | 69.79% | not estimable |
| Kaggle: Philippine Spam/Scam SMS (bwandowando) | reduced-alpha-1 | 3155 | 110 | 0/153 | 2.61% | 2.61% | 5.10% | not estimable |
| Kaggle: Tagalog-SMS (ZERO, 2025) | original-alpha-0.1 | 560 | 655 | 2149/54 | 86.97% | 75.93% | 22.22% | 12.75% |
| Kaggle: Tagalog-SMS (ZERO, 2025) | reduced-alpha-0.1 | 560 | 655 | 2149/54 | 84.61% | 77.78% | 19.86% | 15.22% |
| Kaggle: Tagalog-SMS (ZERO, 2025) | reduced-alpha-1 | 560 | 655 | 2149/54 | 88.79% | 62.96% | 21.59% | 10.56% |

Original NB keeps the earlier full-URL/number/currency tokenizer, alpha=.1 and threshold >=.5. Reduced models remove complete URLs/emails/numeric identifiers and amounts using a fixed transform; keep conservative stopwords and word (1,2) TF-IDF; use min_df=2, max_df=.95, cap=20,000. Compare alpha=.1 and stronger smoothing alpha=1. These feature changes can also remove useful signals; lower accuracy is not automatically better generalization. No condition, threshold or split is selected by test ranking.

Equal-group accuracy gives each template/sender component equal weight, instead of allowing hundreds of related messages to dominate. Train/test gaps are descriptive; low gaps do not establish absence of memorization. Source and inherited labeling rules remain confounded. Positive-only source tests cannot measure false-positive rate. No independent campaign/sender identity, human labels or verified receipt chronology has been added. A chronological claim or real-world accuracy estimate cannot be established from these retrospective reshuffles.

All fitted models and private neighbor/prediction ledgers are retained under research/runs/nb-generalization-20261019/run-v1. The fixed first fold supplies each reference 80%-trained artifact; it was chosen before evaluation. No Android model is replaced. Source attribution and existing license restrictions remain in ../source-evidence.md.

Reproduce from the repository root with a new private output directory:

```powershell
$run='research/runs/nb-generalization-20261019/NEW-RUN'
research/.venv/Scripts/python.exe scripts/retrain_nb_generalization.py train $run
research/.venv/Scripts/python.exe scripts/retrain_nb_generalization.py evaluate $run
research/.venv/Scripts/python.exe scripts/retrain_nb_generalization.py report $run
```
