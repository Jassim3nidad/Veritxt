# Completed verification — 20 October 2026

- 28 targeted synthetic integrity checks passed: 10 for this comparison, 10 for the reused NB comparison and 8 for the existing holdout workflow. They cover explicit three-class mapping, conflicts/duplicates, group linkage, deterministic allocation, nested membership, five-fold coverage, infeasible grouping rejection, feature-fitting isolation, confusion orientation, bootstrap pairing, seal tampering and refusal of repeated final evaluation before loading messages.
- Both algorithms have exactly the same fitted vocabulary and IDF array at each fitting size: 30,227 features at 60%, 37,885 at 80%.
- All three base partitions form a complete, disjoint cover. All five CV folds exclude test records, retain all three classes and keep row/text/group memberships disjoint. Training-fold validation covers each 80% training record once.
- All four test metrics were recomputed from saved row predictions. Identical test indices and labels were verified for all models.
- Original dataset, source, membership, selections and fitted-artifact SHA-256 seals passed after evaluation. The exclusive evaluation marker remains in place.
- All 123 existing Android/source/prior-report files in the preservation snapshot retained their original SHA-256 hashes. Existing app integration and APKs were not edited or rebuilt.
- The four combined/summary chart types were opened and visually checked; individual confusion plots use the same checked confusion data.
- Aggregate artifact hashes are listed in `artifact-manifest.json`. Private verification records, populated memberships, fitted models and row predictions remain in `research/runs/multiclass-20261020/run-v1/`.

Verification establishes implementation consistency with the declared protocol. It does not independently validate inherited labels, source representativeness, campaign independence or future SMS performance.

Tests can be reproduced from the repository root:

```powershell
$env:PYTHONPATH='research'
research\.venv\Scripts\python.exe -m unittest research.tests.test_multiclass_comparison research.tests.test_nb_comparison research.tests.test_holdout_8020 -v
```
