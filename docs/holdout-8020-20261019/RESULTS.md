# 80/20 retraining — 19 October 2026

**Training-CV-selected model: NB-alpha-0.01.** All six latest NB/SVM settings were retrained.

The original October 12 ZIP and latest NB comparison cleaning/features are reused. Labels are inherited; this historically exposed corpus supports retrospective evaluation only. Models, vocabulary, text and row predictions remain private. Current Android assets and prior notebooks are preserved.

| Partition | Records | Ham | Smishing | Fraction | Groups |
|---|---:|---:|---:|---:|---:|
| train | 2734 | 2444 | 290 | 79.9883% | 291 |
| test | 684 | 611 | 73 | 20.0117% | 9 |

20% is rounded upward to a whole record. Test positive support is rounded from the corpus class ratio. Whole template/sender connected components are allocated using binary integer constraints and fixed seed-42 group priorities. This changes the old fold allocator, which substantially missed its requested sizes. Group overlap: 0; normalized-text overlap: 0. The split is frozen before fitting. No score-based split/seed search or random leakage fallback is used. This constrained allocation is not a conventional row-random split, and group/source composition can differ from traffic.

Three grouped cross-validation folds are formed entirely within the 80% training partition. Each fold learns its own vocabulary/IDF and classifier; pooled training OOF F1 selects the configuration, then recall, precision, smaller classifier and ID break ties. Fixed NB threshold >=0.5 and SVM margin >=0; no calibration or threshold tuning. All six classifiers are refitted on every training row before selection/artifact hashes are sealed and the 20% test partition is transformed once. All configurations are reported; the test ranking cannot change selection.

The exact row/class constraints do not balance the number of groups or sources. The allocator minimizes the sum of positive seeded group priorities, which can favor fewer, larger components. This run's test set contains only **nine groups**, including 621/684 messages from the Tagalog-SMS source. These 684 rows must not be interpreted as 684 independent campaigns. Inner validation folds also differ substantially: 634, 1,491 and 609 records, with scam fractions 21.29%, 4.56% and 14.29%. Exact 80/20 row counts therefore do not establish representative sampling or stable generalization.

| Configuration | Training CV F1 | Test accuracy | Scam precision | Scam recall | Scam F1 | TN/FP/FN/TP |
|---|---:|---:|---:|---:|---:|---|
| A-baseline | 28.91% | 92.98% | 100.00% | 34.25% | 51.02% | 611/0/48/25 |
| B-proposed | 86.87% | 99.71% | 100.00% | 97.26% | 98.61% | 611/0/2/71 |
| NB-alpha-0.01 | 89.76% | 99.56% | 96.05% | 100.00% | 97.99% | 608/3/0/73 |
| NB-alpha-0.5 | 52.79% | 95.61% | 100.00% | 58.90% | 74.14% | 611/0/30/43 |
| NB-alpha-2.0 | 4.71% | 89.33% | 0.00% | 0.00% | 0.00% | 611/0/73/0 |
| SVM-reference | 78.94% | 98.25% | 98.41% | 84.93% | 91.18% | 610/1/11/62 |

Metrics were recomputed from the saved test predictions. Every candidate passed the existing independent JSON feature/score/decision checks on the test cohort and 115 synthetic probes at 1e-10 tolerance. These are Python inference checks, not Android integration. The schema-8 tokenizer still requires a matching Android scorer.

The training-CV-selected alpha=0.01 remains selected even though alpha=0.1 has higher test F1. Selection is not revised using the test results. The selected model's qualitative probes still flag the ordinary Taglish meeting/traffic example and miss the fictional Tagalog scam example; the recognizable-word nonsense probe also scores positive. These synthetic counterexamples are not an estimated error rate, but the high test metrics do not resolve them. No new app model was installed.

Validation completed: all 18 targeted split, selection, freeze, intake and inference regression checks passed. All six saved test metric tables were recomputed from their frozen row predictions, and frozen input/source/model hashes were verified after evaluation. The private completion-verification.json records the report hashes and checks.

The two-class source/rule labels, source imbalance, heuristic template grouping, approximate language metadata and historical exposure remain limitations. Different test membership prevents treating differences from older reports as a controlled accuracy improvement. CV fold supports, per-fold metrics, source/language test supports, FPR/FNR and classification reports are in results.json. Source terms/attribution remain in docs/source-evidence.md.

Reproduce from the repository root using a new private output directory:

```powershell
$env:PYTHONPATH='research'
research/.venv/Scripts/python.exe -m smishguard.holdout_8020 train research/data/newdata-20261013/smishguard_dataset_2026-10-12.zip research/runs/holdout-8020-20261019/NEW-RUN
research/.venv/Scripts/python.exe -m smishguard.holdout_8020 evaluate research/data/newdata-20261013/smishguard_dataset_2026-10-12.zip research/runs/holdout-8020-20261019/NEW-RUN
research/.venv/Scripts/python.exe -m smishguard.holdout_8020 report research/data/newdata-20261013/smishguard_dataset_2026-10-12.zip research/runs/holdout-8020-20261019/NEW-RUN --report-dir docs/holdout-8020-20261019
```

Completed private run: `research/runs/holdout-8020-20261019/run-v1`.
