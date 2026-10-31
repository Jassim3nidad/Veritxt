# VeriTxt controlled three-class comparison — 20 October 2026

This protocol is written before model fitting and final evaluation for this experiment. It does not erase the corpus's historical exposure. The comparison is retrospective and evaluates inherited labels.

## Input and eligibility

Read only `smishguard_dataset_2026-10-12/smishguard_dataset.csv` inside the existing October 12 ZIP. Never execute the bundled build or labeling scripts. The strict existing reader checks the CSV schema, archive safety and UTF-8 decoding. Original fields are id, text, label, category, language, source, source_category, sender, date, template_group, label_method, confidence, and needs_review.

Explicit mapping: Ham=0 (`ham`), Smishing=1 (`smishing`), Gambling=2 (`gambling_ad`). Gambling advertisements are a separate class; gambling-related fraudulent lures retain their inherited Smishing label. Neither class is silently merged or relabeled.

Preserve the recent research scope: the three named Kaggle sources in `nb_comparison.SOURCES`; exclude flagged `needs_review=True` records. Existing GitHub/team source holds remain. Also exclude malformed/empty/overlong text, every side of a normalized exact-label conflict, and redundant normalized copies. Report overlapping exclusion reasons separately from total excluded rows. No eligibility decision depends on model predictions. The experiment cannot certify acquisition rights, privacy review or independent label accuracy.

## Grouping and partitions

Reuse `nb_comparison.normalize`, `group_rows` and `vectorizer` without modifying them. Whitespace is collapsed; casefolded text is used for exact-copy checks. Label-blind connected components join supplied `template_group` identities, source-scoped sender/campaign/conversation identities when available, and near-copy templates. Near-copy detection uses the existing Unicode template key after URL/number removal and SequenceMatcher with autojunk disabled at similarity >=0.85, including transitive connections. Labels never determine a similarity edge. Mixed-label groups are retained intact. Grouping sees all text only to prevent overlap; it learns no classification features. The grouping heuristic is conservative and can both merge unrelated messages and miss paraphrases.

Allocate whole components jointly to 60% training, 20% validation and 20% test. With N retained records, validation and test each contain ceil(0.20N); the remainder is training. Class counts in each partition must lie between floor and ceil of their proportional target. Each class must appear in at least six training groups and two validation/test groups. Within these hard constraints, minimize summed absolute deviations from proportional class-bearing group counts, normalized by each class's total group count. Very small seeded assignment costs break ties; seed=42. The solver uses SciPy MILP, a 120-second limit and relative gap 0.001. Allocation fails on infeasibility or timeout; it never falls back to splitting groups or searches seeds based on model scores. Save solver status, objective and gap.

The 80% training set is exactly the union of 60% training and 20% validation. The same 20% test rows are used in all four configurations. Assert disjoint IDs, normalized text and connected groups across all base partitions, plus all three classes in each. Actual row, class, source and group composition must accompany results. Exact row fractions do not guarantee representative campaigns or traffic.

## Shared features and classifiers

Both algorithms use the identical existing TF-IDF settings: lowercase Unicode words; URL-, number- and currency-preserving token pattern; word unigrams and bigrams; min_df=1, max_df=1.0, unlimited features, raw term frequency, smoothed IDF, L2 normalization, no accent removal, and the same 13 conservative English stopwords. The full settings are serialized in configuration.json. Preserve negations and Filipino/Taglish terms affected by broad English stopword lists. No translation, stemming, feature selection, learned text cleaning, balancing, class weighting, calibration or threshold tuning. Source, label metadata, template groups and record IDs are never classifier features.

LinearSVC uses C in {0.001, 0.01, 0.1, 1, 10, 100, 1000}, dual='auto', max_iter=20000, random_state=42. MultinomialNB uses alpha in {0.001, 0.01, 0.1, 0.5, 1, 2, 10}, with default empirical class priors. Predictions use the native multiclass decision, including LinearSVC's default one-versus-rest formulation. Any fitting warning fails the run for investigation.

## Selection and evaluation boundary

For 60% configurations, fit each candidate full pipeline only on 60% training; transform the validation portion and maximize its macro F1. Refit the selected setting on the same 60% training records only. Never incorporate validation records into this final fit. CV mean/SD are not applicable to this single-validation design.

For 80% configurations, form five deterministic StratifiedGroupKFold folds within the 80% portion (shuffle=False, avoiding shuffled group-allocation behavior in the installed scikit-learn version). The outer allocation uses seed 42. Both algorithms share saved fold memberships. Assert class support and group/text disjointness for every fold; each training record must appear exactly once as fold validation. Fit a fresh TF-IDF-plus-classifier Pipeline per fold and candidate. Select the largest unweighted mean of the five macro F1 scores; exact ties choose smaller C/alpha. Report fold values and population SD (ddof=0). These are tuning scores, not an unbiased nested-CV estimate of the selected model. Refit the selected pipeline on every 80% training row.

Freeze input/source hashes, full membership, parameter grid, tuning results, selections and fitted models before transforming test messages. A separate evaluation stage verifies hashes and creates an exclusive evaluation marker; it refuses repeat evaluation. Evaluate all four prespecified configurations once. No parameter, group, split, seed or exclusion changes may depend on test metrics. Metric reports are independently recomputed from saved predictions. Existing app assets and APKs are outside this experiment's write paths.

## Outcomes and interpretation

Primary outcome: three-class macro F1 on the controlled 80/20 comparison. Report accuracy, macro precision/recall/F1, weighted F1, every class's precision/recall/F1/support, correct and incorrect counts, full actual-row/predicted-column confusion matrices, Smishing/Gambling predicted Ham, and Ham predicted Smishing/Gambling. Give Smishing recall particular attention. Report all grid/CV/validation values and all four configurations, without using test scores to revise tuning.

Report differences in percentage points. A prespecified paired cluster bootstrap resamples whole test components with replacement 2,000 times (seed 42), retaining paired predictions; omit replicates missing any true class and report their count. Save conditional percentile 95% intervals for algorithm differences and within-algorithm training-regime changes. These fixed-fit intervals do not capture uncertainty from training, annotation, group construction, hyperparameter selection or new sources and do not establish prospective statistical superiority. Folds share training data; CV SD is descriptive variability, not a standard error or confidence interval.

The 60% versus 80% comparison changes both fitting sample size and tuning procedure (validation versus five-fold CV). It answers the requested practical regime comparison; it is not a pure causal learning-curve experiment. Previously exposed records, inherited rule-derived labels, source imbalance, conservative sender components, imbalanced classes and one outer split limit generalization. Recommend an algorithm provisionally from the controlled 80% evidence and consider recall/error tradeoffs. Do not install a model in Android.

## Reproduction

From the repository root in PowerShell:

```powershell
research\.venv\Scripts\python.exe -m pip install -r research\multiclass-comparison-requirements.txt
$env:PYTHONPATH='research'
research\.venv\Scripts\python.exe -m unittest research.tests.test_multiclass_comparison -v
research\.venv\Scripts\python.exe -m smishguard.multiclass_comparison run research/runs/multiclass-20261020/NEW-RUN --dataset research/data/newdata-20261013/smishguard_dataset_2026-10-12.zip --report-dir docs/multiclass-comparison-20261020/NEW-REPORT
research\.venv\Scripts\python.exe scripts/report_multiclass_comparison.py research/runs/multiclass-20261020/NEW-RUN docs/multiclass-comparison-20261020/NEW-REPORT
```

Use fresh run and report directory names. To inspect the boundary, replace `run` with sequential `prepare` (with --dataset), `train`, `evaluate`, and `report` (with --report-dir), using the same run path. Grouping can take several minutes. Populated data, cleaning ledgers, exact memberships, predictions, fitted pipelines, source snapshots and sealed manifests remain in the Git-ignored research/runs directory. Public reports contain aggregate tables and figures. JSON records exact library versions, SHA-256 identities, feature settings and selection policy. Repeating under another numerical library/solver version can produce different tied allocations; preserve the saved membership for an exact audit of the completed run.

The supplemental reporting script contains study-specific interpretive prose and verifies the reported confusion matrices and selected CV statistics before reusing it. If a changed input or runtime produces different outcomes, numerical tables/figures from the generic experiment module remain available; the supplemental script refuses to reuse the old numerical narrative. Interpret new outcomes before writing a new thesis discussion.

Method references: [scikit-learn data leakage guidance](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage) and [grouped cross-validation guidance](https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-iterators-for-grouped-data). The completed experiment records its actual installed versions; current documentation does not replace that version record.
