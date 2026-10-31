# Source-based model improvement experiment — 13 October 2026

**New development choice: Linear SVM with combined word/character TF-IDF, C=1, min_df=2.** It leads source-based validation under the prespecified false-alert/recall goals. The current APK remains byte-identical and still uses the earlier word-only SVM.

This is retrospective research using the existing inherited labels. Source-validation metrics were used to choose among 51 configurations and their operating thresholds; they are optimized development results, not unbiased future-source performance. The reserved 498-record test was excluded from new fits and selection, but was historically examined. No independently verified fresh SMS cohort was added.

## What changed

- Source-based validation holds out each development source and purges cross-source related templates. All vocabulary/IDF, classifier fits and SVM calibration folds exclude the held source and reserved test.
- Compare SVM/LR C=0.01/0.1/1/10 and NB alpha=0.03/0.1/1/10; word features with/without English stopwords, character-within-word 3–5 grams, and combined word/character features. New candidates exclude terms appearing in fewer than two training documents. Three historical configurations are explicit min_df=1 controls.
- Choose warning thresholds using source-validation predictions. A candidate must keep FPR ≤2% in every source/language subgroup with ≥100 ham records and recall ≥50% in every source with ≥20 smishing records. Positive-only sources cannot establish a false-positive rate. Failure to meet the goal is reported, and an all-negative predictor is rejected by the recall floor.
- Freeze family winners, thresholds and final development-only fits before reserved-test prediction.

51/51 candidates completed; 0 failures and 0 candidates with fitting warnings. 14 configurations met the development operating goals. The run took 84.2 seconds on this host; this is not an Android benchmark.

## Source-based development results

All families use the same 2,056 development records. Each model scores a development source using a fit that excludes that source and its related template groups. Equal-source mean F1 weights the three sources equally rather than allowing the largest source to dominate.

| Family winner | Threshold | Mean source F1 | Worst supported FPR | Lowest supported source recall | Goals met |
|---|---:|---:|---:|---:|---|
| svm-combined-1-df2 | 0.72096472 | 80.77% | 1.98% | 74.23% | Yes |
| lr-combined-10-df2 | 0.43880478 | 71.64% | 2.07% | 52.58% | No — fallback |
| nb-combined-0.03-df2 | 0.99996363 | 70.99% | 1.98% | 56.70% | Yes |

Selected SVM mean source F1 is **80.77%**, compared with **70.63%** for the matched source-fold historical word-only configuration, when both receive the new source-validation operating-point selection. This changes features, C, minimum document frequency and threshold together, so it does not identify the causal effect of one change.

| Held development source | Scam support | Detected | Missed | Ham support | False alerts | F1 |
|---|---:|---:|---:|---:|---:|---:|
| bwandowando | 97 | 72 | 25 | 0 | 0 | 85.21% |
| marketing | 111 | 90 | 21 | 695 | 1 | 89.11% |
| tagalog | 44 | 34 | 10 | 1109 | 22 | 68.00% |

The Tagalog-source development fold has 22 false alerts among 1,109 ham messages and catches 34/44 scams. Its 68.00% F1 remains imperfect. These development-fold counts are not directly comparable to the older 133/1,371 false-alert stress test: membership, training fits, thresholds and the role in selection differ. The name “Tagalog” denotes a source, not a pure Tagalog-language evaluation.

## Reserved historical test

After selection, family winners were refitted on the 2,056 development records. The original APK comparator had 1,540 fitting records and its original ≥0.37 threshold. All results below use the same 498 test IDs and labels, but training sizes and configurations differ. Do not reselect from this table.

| Model | Detected scams /73 | Missed scams | False alerts /425 ham | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Original APK SVM | 70 | 3 | 4 | 94.59% | 95.89% | 95.24% |
| SVM new family winner | 69 | 4 | 2 | 97.18% | 94.52% | 95.83% |
| LR new family winner | 63 | 10 | 1 | 98.44% | 86.30% | 91.97% |
| NB new family winner | 55 | 18 | 0 | 100.00% | 75.34% | 85.94% |

The new SVM produces two fewer false alerts and one additional missed scam versus the original APK comparator. Its small retrospective F1 increase does not establish a statistically or prospectively superior production model.

## Language results

The existing metadata combines Filipino and Taglish. Separate Tagalog/Taglish rankings cannot be created without new language annotations. Counts below are on the reserved test; the combined subgroup contains only ten scams and is descriptive.

| Language | Model | Detected scams | Missed scams | False alerts | Ham support |
|---|---|---:|---:|---:|---:|
| English | SVM | 60/63 | 3 | 2 | 284 |
| Filipino/Taglish | SVM | 9/10 | 1 | 0 | 141 |
| English | LR | 56/63 | 7 | 1 | 284 |
| Filipino/Taglish | LR | 7/10 | 3 | 0 | 141 |
| English | NB | 47/63 | 16 | 0 | 284 |
| Filipino/Taglish | NB | 8/10 | 2 | 0 | 141 |

Source-validation language performance also remains uneven: the selected SVM catches 115/155 English scams with 22/1,207 ham false alerts, and 81/97 Filipino/Taglish scams with 1/597 ham false alerts. These are optimized development outcomes, not independent language guarantees.

## Original false-alert investigation

Prepared a private review packet for all 133 inherited-label false positives. 123 are labeled English and ten Filipino/Taglish; all have the broad supplied “Legit message” category. Their median fitted score is 0.6792. Human verification and adjudication remain pending; no inherited label was changed. A private feature-contribution ledger accompanies the packet so reviewers can investigate why the separate stress-test model flagged each message.

| Descriptive pattern | False-alert messages /133 | Correctly unflagged ham /1,238 |
|---|---:|---:|
| url_marker | 17 | 161 |
| number_marker | 91 | 984 |
| account_verify_words | 45 | 163 |
| code_password_words | 61 | 156 |
| payment_words | 73 | 388 |
| negation_words | 60 | 362 |
| do_not_share_phrase | 3 | 24 |

Financial/account/code wording occurs in many supplied legitimate messages, providing a plausible shortcut to investigate. Pattern counts are correlations, not causal proof or independent label verification. Seventeen false alerts scored at least 0.90, so a high numerical score alone does not establish correctness. Learned terms, contributions and masked messages remain in private storage.

## Verification and delivery

- 153 source-fit pipelines and 3 final pipelines were replayed; maximum source score error 0.0. All source-validation threshold choices reproduce.
- 81 original artifacts retain identical hashes, including all older candidate models, the original app assets and the delivery APK.
- Source/group/reserved-test isolation, training-only calibration memberships and the pre-test selection freeze were verified. Nine new guard tests passed; the complete research suite passed 130 tests.
- No app model, dataset label, human review decision, fresh SMS record or physical-phone result was fabricated.
- Private trained candidates: `research/runs/source-robustness-20261013/run-v1/final/`. The selected fitted pipeline is `svm-combined-1-df2/pipeline.pkl`.
- Private reviewer materials: `private-false-alert-review.csv`, `private-feature-contributions.json`; empty future-data template: `prospective-intake.csv` in the same private run.
- The new word/character FeatureUnion is not supported by the current APK’s word-only native contract. It requires a new portable scorer and Python/JVM/Android parity before an app variant can use it. The current APK was intentionally preserved during this research task.

## Reproduction

```powershell
$env:PYTHONPATH='research'
research/.venv/Scripts/python.exe -m unittest discover -s research/tests -p test_source_robustness.py -v
research/.venv/Scripts/python.exe -m smishguard.source_robustness --original research/runs/bantaytext-20261013/notebook-run-v3 --output research/runs/source-robustness-20261013/NEW-RUN
```

The output must be a new private directory. See [prespecified protocol](source-robustness-protocol-20261013.md), [aggregate JSON](source-robustness-results-20261013.json), and [candidate CSV](source-robustness-results-20261013.csv). The generic prospective intake is intentionally empty; completing its labels provides evidence, not an automatic blanket software-development permission gate.

Methods: [grouped validation](https://scikit-learn.org/1.6/modules/cross_validation.html), [character/word feature extraction](https://scikit-learn.org/stable/modules/feature_extraction.html), [validation-only threshold tuning](https://scikit-learn.org/stable/modules/classification_threshold.html). Executed sklearn version is 1.6.1; stable documentation may describe a later version.
