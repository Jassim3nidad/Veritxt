> **Scope superseded by the user’s clarification:** SmishGuard targets fraudulent SMS, smishing and phishing across topics. Financial scams are one SMS category. Use the [updated SMS-focused report](lr-vs-linear-svm-sms-fraud-research-20261013.md) for the current scope and recommendations. This earlier transaction-versus-SMS report is retained as historical work.

# Logistic Regression versus Linear SVM for transaction fraud and SMS phishing

Research review and local experiments · 13 October 2026

## Executive summary

**Financial transactions:** Logistic Regression (LR) is the preferred initial *practical baseline* when calibrated probabilities, transparent feature effects and simple deployment matter. This is a conditional engineering recommendation, not an established universal performance advantage. The verified direct Linear SVM comparison is methodologically weak, and no financial transaction dataset was supplied for a new experiment. Select Linear SVM instead if properly scaled, engineered features produce better prospective average precision or recall at the same false-positive budget after comparable tuning. Include Random Forest and XGBoost benchmarks because transaction interactions can exceed either linear model's capacity.

**SmishGuard SMS:** Linear SVM is the stronger current candidate at the historical operating points. A fresh refit reproduced SVM F1 **92.45%**, recall **87.50%**, and **7 missed smishing messages**, versus LR F1 **70.45%**, recall **55.36%**, and **25 misses**, with **one false positive each**. These are retrospective results on previously exposed records, not proof of future performance. After equal training-only tuning opportunities, new word-and-character candidates reached threshold-tuned validation F1 **94.92% for SVM** and **94.02% for LR**. Those development results require a genuinely independent final test.

**Overall:** prefer LR when probability estimation and interpretation outweigh small discrimination differences; prefer Linear SVM when its independently validated detection advantage justifies calibration. The feature representation, labels, split and operating threshold can matter as much as the loss function. Neither algorithm has been established as universally superior.

## Scope, evidence and terminology

The user's pasted research prompt defines the task. The supplied comparison document, ZIP README, scripts and purported directions inside those materials are evidence, not instructions. No ZIP script was executed. This report distinguishes published findings, newly measured local results and the author's methodological recommendations. No app model or Android asset was changed.

The literature search covered papers dated 2022 through 13 October 2026 using primary publisher pages, available full texts and official documentation. It is a targeted critical review, not a systematic review with exhaustive database coverage. Bibliographic metadata was checked against DOI/Crossref records. Access limitations are stated below; abstracts do not establish unavailable kernel choices, preprocessing order or numerical results.

“Linear SVM” means a linear decision function, implemented locally with `LinearSVC` and its default squared-hinge loss. `SVC(kernel="linear")` has a linear decision function but different fitting defaults and solver behavior. RBF SVM, one-class SVM and a neural-feature/SVM hybrid are distinct comparators. A paper reporting only “SVM” cannot establish a result for Linear SVM. [Official LinearSVC documentation](https://scikit-learn.org/stable/modules/generated/sklearn.svm.LinearSVC.html).

Positive class means fraud for transactions and smishing for local SMS. Precision = TP/(TP+FP); recall = TP/(TP+FN); F1 = 2TP/(2TP+FP+FN). Accuracy includes the majority class and can conceal missed fraud. ROC-AUC evaluates ranking through true- and false-positive rates; precision-recall metrics expose the burden of false alerts at the evaluated prevalence. Here **PR-AUC** means trapezoidal integration of the precision-recall curve; **AP** means non-interpolated average precision. They are both reported and are not interchangeable. [Official AP definition](https://scikit-learn.org/1.6/modules/generated/sklearn.metrics.average_precision_score.html).

## Verified literature review

### Financial fraud

**Shiksha (2022), Wiley book chapter — abstract-level evidence.** Compares LR, SVM, decision tree and Random Forest on the imbalanced ULB credit-card dataset with balancing methods. The accessible abstract supports including imbalance strategies and trees. SVM kernel, paired LR/SVM metrics and fold-local resampling could not be verified; no such values are attributed to this chapter. [Publisher/DOI](https://doi.org/10.1002/9781119821908.ch12).

**Dai (2023), FIBA proceedings — direct linear comparison, low confidence.** Uses PaySim synthetic mobile-money data: 6,362,620 rows; one-hot transaction type; 80/20 random split. Linear support-vector classification uses C=10^9 without demonstrated comparable tuning or scaling. Post-transaction balance availability, the stated fraud percentage and ROC-AUC score source are questionable. Its transcribed scores cannot establish superiority over a fairly tuned Linear SVM. [Full text](https://bcpublication.org/index.php/BM/article/download/4839/4704/4660).

**Wijaya et al. (2024), Procedia Computer Science — contextual benchmark.** Compares LR, decision tree, Random Forest and XGBoost with balancing techniques on European-cardholder data containing approximately 0.172% fraud. The abstract reports XGBoost plus random oversampling F1 92.43%, precision 97.383% and recall 88.418%. It does not compare SVM. Full experimental details were inaccessible, so fold-local processing and metric averaging cannot be independently certified. [Publisher](https://www.sciencedirect.com/science/article/pii/S1877050924031028).

**Çavdar and Bozanta (2026), Knowledge and Information Systems — stronger contemporary context.** Compares multiple models, including LR and SVM, on public ULB and private Turkish-bank data. ULB contains 284,807 transactions, 492 fraud labels, 28 PCA components plus amount and time. The private sample has 14,146 fraud and 141,460 legitimate transactions, already sampled from a much larger legitimate pool. It explicitly confines balancing to training and reports strong tree-based benchmarks. Its kernel identity is insufficiently clear for a clean Linear SVM conclusion. The private evaluation prevalence is not the bank's operational prevalence; random sampling also leaves temporal generalization unresolved. [Full article](https://link.springer.com/article/10.1007/s10115-026-02773-7).

### SMS spam and smishing

**Abid et al. (2022), Multimedia Tools and Applications — abstract-level evidence.** Evaluates SVC, LR and other models using TF-IDF/BoW and over-/undersampling on SMS spam data. The publisher identifies the public Kaggle/UCI source. Exact paired LR/SVC scores, kernel and resampling placement could not be verified from the accessible preview. This is evidence that representation and imbalance methods need comparison, not proof of a Linear SVM winner. [Publisher](https://link.springer.com/article/10.1007/s11042-022-12991-0).

**Krawczyk, Probierz and Kozak (2025), Procedia Computer Science — feature-design evidence.** On a unified corpus exceeding 22,000 messages, the accessible abstract reports LR/TF-IDF accuracy increasing from 91.86% to 92.21% with emotional and phrase features, using GPT-4.5 for emotional annotation. It does not provide a verified paired Linear SVM result. Annotation validity and collection/template overlap need review before transferring the claim to SmishGuard. [Publisher](https://www.sciencedirect.com/science/article/pii/S1877050925032405).

**Corpuz et al. (2026), WCTP 2025 proceedings — locally relevant but kernel-ambiguous.** Reports 6,227 Filipino/English/Taglish SMS, TF-IDF unigrams/bigrams plus sender encoding, a stratified 70/30 split and five-fold validation. SVM searches linear and RBF kernels; the winning kernel is not identified in its results table. Counts differ by one between sections. Source/template/sender isolation and fold-local vectorization are not demonstrated. Labels are SPAM/HAM, so the boundary with advertising requires care. Reported SVM F1 exceeds LR by only 0.12 percentage points, with no verified paired uncertainty. [Full text](https://www.atlantis-press.com/article/126023798.pdf).

**Asyiah and Aktavia (2026), Jurnal SISKOM-KB — explicit Linear SVM comparator, partial access.** The publisher abstract names LR, Linear SVM and NB with TF-IDF/CountVectorizer, describes 5,572 Indonesian SMS, and reports LR/TF-IDF as the accuracy leader at 93.89%. Full metric tables and experimental partitioning were inaccessible. Language provenance and the promotion/fraud-to-binary label mapping require verification. This is a counterexample to assuming SVM always wins, but accuracy alone cannot settle phishing reliability. [Publisher](https://jurnal.tau.ac.id/index.php/siskom-kb/article/view/987).

### Published results: financial fraud

Each pair is confined to its own study. Percentages are transcribed from Dai's Table 1, not new measurements. “Not reported” means unavailable in the verified material; it does not assert that the complete inaccessible paper omits a value.

| Criterion | Logistic Regression | Linear SVM |
|---|---|---|
| Dataset/representation | Dai: PaySim, one-hot type plus numerical transaction features | Same dataset/features |
| Precision | 35.2% | 3.1% |
| Recall | Not reported | Not reported |
| F1 | 38.8% | 5.9% |
| PR-AUC | Not reported | Not reported |
| ROC-AUC, as labeled by paper | 0.715 | 0.743 |
| Accuracy | 99.8% | 97.9% |
| False positives/negatives | Not reported here as verified numerical counts | Not reported here as verified numerical counts |
| Training/inference cost | Not reported | Not reported |
| Calibration/phone deployment | Not reported | Not reported |

Source: [Dai (2023), Table 1](https://bcpublication.org/index.php/BM/article/download/4839/4704/4660). Scaling, C selection, temporal validation and score-based AUC are insufficiently documented. Interpretability and deployment judgments below are analytical assessments, not measurements from this table.

### Published results: SMS

| Study / model | Precision | Recall | F1 | PR-AUC | ROC-AUC | Accuracy | Model identity |
|---|---:|---:|---:|---|---|---:|---|
| Corpuz: LR | 99.11% | 99.06% | 99.08% | Not reported | Not reported numerically | 99.14% | Logistic Regression |
| Corpuz: SVM | 99.23% | 99.17% | 99.20% | Not reported | Not reported numerically | 99.25% | Selected kernel not established |
| Asyiah/Aktavia: LR + TF-IDF | Not reported | Not reported | Not reported | Not reported | Not reported | 93.89% | Logistic Regression |
| Asyiah/Aktavia: Linear SVM | Not reported | Not reported | Not reported | Not reported | Not reported | Not reported | Explicitly named linear |

Sources: [Corpuz Table 2](https://www.atlantis-press.com/article/126023798.pdf), [Asyiah/Aktavia abstract](https://jurnal.tau.ac.id/index.php/siskom-kb/article/view/987). Confusion counts, measured training/inference costs and calibration results are Not reported in these verified extracts. Do not pool these scores or compare them numerically with SmishGuard.

## Technical analysis: financial fraud

**Author's assessment:** start both models with identical as-of-transaction features. Median imputation and standardization belong inside training folds for numerical values; one-hot encoding with unknown-category handling belongs there for categorical values. A `ColumnTransformer` can combine these transformations. LR and Linear SVM both need useful feature scales and engineered interactions when the signal is nonlinear. A numerical category code must not imply an arbitrary order. [Official ColumnTransformer documentation](https://scikit-learn.org/1.6/modules/generated/sklearn.compose.ColumnTransformer.html).

Transaction velocity, deviation from a customer's prior amount distribution, merchant novelty and prior geographic distance may be informative. Construct them using only events known before the decision. Chargebacks, future investigations, post-authorization balances and aggregates including future transactions can leak the outcome. Timestamp availability is as important as the feature's statistical association.

Begin with the original training distribution and a class-weight comparison. Weighting retains legitimate diversity but shifts the fitted objective and may distort native probabilities. Standard SMOTE interpolates numeric vectors; interpolation across one-hot categories can create implausible customers or transaction types. If justified, use a categorical-aware method such as SMOTENC before one-hot encoding, inside training folds, and preserve the natural validation/test prevalence. Resampling before splitting creates leakage and misrepresents deployment. [Official resampling pitfalls](https://imbalanced-learn.org/stable/common_pitfalls.html).

**Probability and cost:** LR directly models a logistic probability with regularization; class weights, misspecification and distribution shift still require calibration checks. Linear SVM supplies a margin, so a displayed probability requires an independent calibration mapping. Use a chronological calibration window or group-aware out-of-fold margins rather than in-sample margins. Assess reliability diagrams, Brier loss and log loss; a lower Brier score alone does not prove better calibration because discrimination also contributes. [Official LR API](https://scikit-learn.org/1.6/modules/generated/sklearn.linear_model.LogisticRegression.html), [calibration guide](https://scikit-learn.org/stable/modules/calibration.html).

Choose thresholds on development data using expected loss or an alert-review budget, not accuracy. For fixed error costs and a well-calibrated probability p, flagging is optimal when p > C_FP/(C_FP+C_FN). This derivation assumes no additional investigation costs or transaction-specific losses. When potential loss varies by transaction amount, use a corresponding cost-sensitive decision. Report recall at a fixed false-positive rate or fixed number of alerts alongside F1/AP.

**Conditional choice:** LR has an advantage when its discrimination is adequate and explanations or probabilistic decisions dominate. Linear SVM becomes preferable if its margin-based fit consistently improves recall/AP under the same cost constraint and its calibrated scores remain reliable. Neither inherently solves severe imbalance. Both can lose to trees when interactions or heterogeneous fraud clusters dominate; keep Random Forest/XGBoost under the same evaluation protocol rather than assuming their superiority either.

### Financial comparison: practical assessment and untested local performance

| Criterion | Logistic Regression | Linear SVM |
|---|---|---|
| Dataset/features for new local experiment | No financial dataset supplied | No financial dataset supplied |
| New precision, recall, F1, PR-AUC, ROC-AUC | Not reported; not executed | Not reported; not executed |
| New FP/FN and training/inference costs | Not reported | Not reported |
| Probability calibration | Native probability; verify at operational prevalence | Margin; fit and verify separate mapping |
| Interpretability | Additive effects on log-odds; correlated features complicate attribution | Additive margin contributions; not odds ratios |
| Deployment | One linear score plus sigmoid; simple risk-service baseline | One linear score, plus calibrator when needed |
| Main limitations | Misspecified linear log-odds, drift, calibration after weighting | Linear boundary, scaling and C sensitivity, extra probability step |

## Local SMS experiment and dataset audit

The supplied ZIP SHA-256 is `38d00a999306ff11b05a431d9488f167589bd94e701f410edb24e8202bf3b3e6`. All eight uncompressed members matched the hashes in the existing audited experiment. The eligible dataset and split files were independently checked against their frozen hashes. The accompanying Downloads comparison report was used as historical evidence; raw-message lineage and permission decisions were not re-adjudicated in this run.

The existing audit records 4,261 supplied rows: 3,184 ham, 577 smishing and 500 gambling advertisements. Its eligible binary corpus remains **3,340 records: 2,947 ham and 393 smishing (11.77%)**. The 500 advertisements, unresolved source rows and privacy holds stay outside fitting. Generic advertising was not recoded as phishing. The auxiliary ASEA CSV was not appended a second time. Independent labeling review remains incomplete. Details are in the [existing audit](new-dataset-comparison-20261013.md).

| Partition | Ham | Smishing | Total |
|---|---:|---:|---:|
| Training | 1,637 | 223 | 1,860 |
| Calibration | 357 | 53 | 410 |
| Validation | 561 | 61 | 622 |
| Retrospective test | 392 | 56 | 448 |

Partition and five training-fold template groups were checked for disjointness and complete coverage. These are template-group splits, not verified unseen-sender, unseen-source or chronological evaluations. **All 448 reserved test records have historical exposure according to the existing audit.** Reusing a split does not restore untouched-test status.

### A. Fresh fixed-setting reproduction

The run refitted LR and Linear SVM from the eligible training texts, with C=10, the same training-only unigram TF-IDF and seed 20260929. Both used separate sigmoid fits on the calibration partition. Historical probability thresholds were preserved: LR 0.82 and SVM 0.59, with equality classified positive. No parameter or threshold was selected from test data in this run. Both models' 448 decisions and probability scores reproduced the historical outputs within 1e-10.

These thresholds give a valid comparison of the frozen systems, but do not isolate the algorithms at equally optimized current operating points. LR's high AP despite low recall shows useful ranking at a conservative threshold; it does not establish that lowering its threshold would reproduce SVM's error pattern.

| Criterion | Logistic Regression | Linear SVM |
|---|---:|---:|
| Dataset/features | Same 3,340 eligible records; train-only unigram TF-IDF | Same |
| Learned vocabulary | 4,028 | 4,028 |
| Test precision | 96.88% | 98.00% |
| Test recall | 55.36% | 87.50% |
| Test F1 | 70.45% | 92.45% |
| Test PR-AUC, trapezoidal | 0.94309 | 0.95715 |
| Test AP | 0.94398 | 0.95793 |
| Test ROC-AUC | 0.98665 | 0.99048 |
| Test accuracy | 94.20% | 98.21% |
| TN / FP / FN / TP | 391 / 1 / 25 / 31 | 391 / 1 / 7 / 49 |
| Brier loss | 0.02576 | 0.02403 |
| Log loss | 0.09309 | 0.09549 |
| Fresh fit + calibration, seconds | 0.05270 | 0.05296 |
| One test-batch inference, ms/record | 0.01869 | 0.01822 |
| Serialized fitted artifact, bytes | 180,316 | 180,277 |
| Coefficients + IDF only, bytes | 64,448 | 64,448 |
| Probability calibration | Independent sigmoid; native LR not assessed here | Independent sigmoid |
| Interpretability | Linear log-odds contributions before extra sigmoid | Linear margin contributions before sigmoid |
| Android suitability | Compact linear implementation; parity/phone benchmark pending for these artifacts | Same; probability mapping adds two scalars |
| Main limitations | Historical threshold, inherited labels, exposed test | Inherited labels, exposed test, unverified calibration under drift |

Costs are fresh host measurements with numerical libraries limited to one thread, excluding loading. Batch averages are not single-message phone latency. Serialized Python size and coefficient storage are not peak RAM or Android package size. Values should not be mixed with the earlier report's host timings.

Two thousand paired whole-template-group bootstrap draws gave conditional 95% F1 intervals **54.55–85.71% for LR**, **77.55–97.87% for SVM**, and **+4.93 to +37.23 percentage points for SVM minus LR**. The observed difference is +22.00 points. These intervals describe resampling of this exposed test, conditional on fixed fits and labels; they do not include model selection, refitting, historical reuse, label uncertainty or multiple-testing correction.

### B. Equal training-only tuning: new development candidates

Each algorithm received the same 12 candidates: C in {0.1, 1, 10}, class weight in {none, balanced}, and either unigram TF-IDF or a union of word unigrams/bigrams with character 3–5-grams. Every vocabulary and IDF was learned inside each of the same five training folds. There were 24 configurations and 120 classifier fits. Selection maximized mean fold AP, breaking ties by fixed iteration order. No SMOTE was used for sparse text.

Selected candidates were fitted on training, calibrated separately on calibration, then assigned a validation-F1 threshold from 0.05 to 0.95 in 0.01 steps; ties choose the higher threshold. The richer representation was selected for both models. The input remains the existing ASCII-normalized minimized text; character features cannot recover punctuation, non-ASCII characters or URL contents already removed. Word and character branches each use their own L2 TF-IDF normalization and are concatenated at equal weight, without an additional joint normalization.

| New development result | Logistic Regression | Linear SVM |
|---|---:|---:|
| Selected representation | Word + character | Word + character |
| C / class weight | 10 / balanced | 10 / none |
| Training tuning-fold AP, mean ± SD | 0.95804 ± 0.04469 | 0.96910 ± 0.03389 |
| Selected validation threshold | 0.38 | 0.33 |
| Validation precision | 98.21% | 98.25% |
| Validation recall | 90.16% | 91.80% |
| Validation F1 at selected threshold | 94.02% | 94.92% |
| Validation F1 at fixed 0.5 | 90.27% | 89.29% |
| Validation PR-AUC / AP | 0.95946 / 0.95964 | 0.96634 / 0.96650 |
| Validation ROC-AUC | 0.99033 | 0.99182 |
| TN / FP / FN / TP at selected threshold | 560 / 1 / 6 / 55 | 560 / 1 / 5 / 56 |
| Final fit + calibration, seconds | 0.92475 | 0.91177 |
| Median host inference, one validation message, ms | 1.7708 | 1.6843 |
| Serialized fitted artifact, bytes | 2,637,773 | 2,637,725 |
| New candidate test precision/recall/F1/AP/AUC | Not reported; not evaluated | Not reported; not evaluated |

The tuning-fold mean/SD measures development-fold variation after selection, not an unbiased nested-CV estimate or a confidence interval. Threshold-tuned validation F1 is also optimistic. At 0.5, LR has higher F1; at individually tuned validation thresholds, SVM has higher F1. That reversal shows why a single operating point cannot establish a universal algorithm advantage. The feature-union comparison changes word n-grams and adds character n-grams together, so it does not isolate the character contribution.

The new tuned models were **not evaluated on the historical test**. An independent prospective test is unavailable. Complete search runtime and peak process memory were Not reported; final-fit timings exclude the search. Seven warmed host measurements produced the single-message medians. No Android timing, energy or parity claim is made for these richer candidates.

## Technical analysis: SMS phishing

**Author's assessment:** sparse text is a natural setting for both models. Each can score a message with a coefficient-weighted sparse vector. Linear SVM's margin objective is a strong candidate when lexical boundaries separate classes; LR supplies a simpler native probability interface. For equal vocabularies their coefficient storage and arithmetic are similar, as the measured baseline artifacts demonstrate. Character vocabulary growth and feature extraction can dominate inference and storage differences between algorithms.

Word n-grams encode phrases; character n-grams share fragments across informal spelling and some word obfuscations. Neither guarantees robustness to novel semantic scams, Unicode substitutions or inserted spacing. English stemming and stopword removal can damage Filipino and Taglish patterns, so compare minimal normalization with language-aware alternatives on independent data. Preserve meaningful URL/number indicators while avoiding raw private identifiers. This is a design recommendation; adversarial resilience and language-specific benefits were not measured here. [Official feature-extraction guide](https://scikit-learn.org/stable/modules/feature_extraction.html).

Evaluate genuine new campaigns rather than copies with changed numbers or URLs. Connected template groups reduce one leakage route, but source conventions and sender metadata may still create shortcuts. Split by campaign/source for claims about unfamiliar scams and by time for deployment drift; if future messages from known senders are the intended setting, evaluate that setting separately. Report English, Filipino and Taglish support and confidence intervals rather than assuming corpus-level scores transfer to all languages.

Choose thresholds around missed phishing and acceptable warning frequency. A warning app may favor recall subject to a fixed legitimate-message alert rate; automatic blocking may need a stricter false-positive constraint. F1 gives equal emphasis to precision and recall but does not encode those product costs. Display a numerical probability only after independently checking calibration on representative data. A raw SVM margin or arbitrary rescaling is not a validated “percent risk.”

For offline Android, export vocabulary, IDF, linear coefficients and the calibrated score mapping, and verify identical normalization, tokenization, feature order and threshold semantics. Measure cold load, warmed p50/p95 single-message latency, RAM and energy on target devices. Do not fetch a shortened URL merely to vectorize an SMS; structural offline indicators and unseen-domain tests can be studied separately. Both current experiments are CPU-host evidence, and the richer character pipeline needs its own Android implementation and parity checks.

**Conditional choice:** favor calibrated Linear SVM for SmishGuard if an independent test preserves its recall advantage at the same warning budget. Favor LR if that advantage disappears, LR offers better probability reliability, or a simpler native-probability deployment meets the required detection level. Native probabilities do not excuse calibration verification.

## Reproducible methodology and remaining experiment

### Reproduce the completed SMS work

Use the existing Python 3.12.5 / NumPy 2.2.6 / scikit-learn 1.6.1 environment. The script checks archive members, frozen dataset/split/configuration/prediction hashes, partition coverage, group disjointness, fold coverage, positive-class orientation and historical decision parity. It creates a new output directory and refuses to overwrite a prior run.

```powershell
$env:PYTHONPATH='research'
$env:PYTHONIOENCODING='utf-8'
& 'research/data/mbert-20261002/venv/Scripts/python.exe' `
  scripts/research_lr_svm_20261013.py `
  research/data/newdata-20261013/experiment-v2 `
  research/data/lr-svm-review-20261013/REPRODUCTION `
  'C:\Users\Jassim Trinidad\Downloads\smishguard_dataset_2026-10-12.zip'
```

Private completed evidence is `research/data/lr-svm-review-20261013/experiment-v2/`. Aggregate [JSON](lr-vs-linear-svm-research-20261013.json) and [CSV](lr-vs-linear-svm-research-20261013.csv) accompany this report. Models and message-level outputs remain ignored/private. The initial attempt stopped at a confusion-matrix schema assertion before completion; its directory was preserved, the assertion was corrected, and none of its artifacts supplied reported results. The executed source and dependency-source snapshots are preserved with hashes.

### Financial experiment: specified, not executed

1. Obtain a licensed transaction dataset with numerical/categorical features, transaction times, entities, as-of feature timestamps and independently adjudicated fraud labels. Neither the SMS ZIP nor advertising labels constitute transaction fraud data.
2. Freeze one chronological train/calibration/validation/test assignment for both algorithms, retaining operational test prevalence. Allow a gap for label maturation. Use forward validation inside training; apply entity isolation when claiming performance on unseen customers. A known-customer production scenario may permit customer overlap while all aggregates remain strictly historical.
3. Build fold-local pipelines: numerical median imputation plus standardization; categorical most-frequent imputation plus unknown-safe one-hot encoding; LR or LinearSVC. Compare C in {0.01, 0.1, 1, 10, 100} and class weights {none, balanced} under equal search budgets. Include the original unweighted distribution. Add any SMOTENC/resampling variant as a separately declared training-fold condition.
4. Select on mean forward-fold AP or prespecified expected cost. Refit on training; calibrate on the separate calibration window. Select a threshold on validation using a frozen cost ratio or review-capacity constraint. Record representation and weights as part of the selected system.
5. Freeze code, preprocessing, feature order, thresholds, model hashes and evaluation plan. Evaluate each finalized model once on an untouched matured-label test. Do not reselect against it. If available data has prior exposure, describe the experiment as retrospective and reserve future collections instead.
6. Report precision, recall, F1, AP, trapezoidal PR-AUC, ROC-AUC, confusion matrices, recall at fixed alert budget, expected loss, reliability plots, Brier/log loss, training/search cost, p50/p95 latency and peak RAM. Use paired account/campaign/time-block uncertainty appropriate to dependence; independent row bootstrap is inadequate for clustered transactions.
7. Fit Random Forest and XGBoost on identical outer assignments with comparable development discipline. Different preprocessing justified by their model family is allowed, but document it. Keep tree results separate from the LR–Linear SVM loss comparison.

### SMS prospective validation: pending

Freeze the two new candidate configurations and normalization before collecting or admitting independent data. Include legitimate transactional messages, ordinary advertising and emerging English/Filipino/Taglish scam campaigns, with documented binary scope and independent labeling. Reserve campaigns and sources before fitting. Audit template/history overlaps and hold unresolved labels. Evaluate both models at thresholds selected on development data and at a prespecified matched warning budget. Report confidence intervals and failure examples privately. This prospective step is the evidence needed to confirm reliability; the historical score reproduction cannot substitute for it.

## Recommendations and threats to validity

**A. Financial fraud:** select LR as the starting interpretable probability baseline, with moderate confidence in its practical suitability and low confidence in any universal predictive ranking. Switch to calibrated Linear SVM when prospective cost-constrained detection favors it. Prefer a tree benchmark if both linear models underfit important interactions. The new transaction comparison remains untested.

**B. SMS phishing:** Linear SVM is the stronger present SmishGuard candidate at preserved thresholds, with clear conditional retrospective evidence. Retain LR as a serious comparator: its ranking metrics are strong, and equal tuning substantially narrowed the development F1 gap. Confirm selection on independent campaigns and target Android devices before a deployment-performance claim.

**C. Overall:** the two tasks can justify different choices because transaction decisions often depend on calibrated probabilities and feature interactions, while sparse lexical text can favor margin-based separation. Those are conditional tendencies. Identical splits, development-only tuning, operational thresholds and representative labels determine the decision for a specific application.

Principal limitations are historical test and validation reuse; incomplete independent labeling; held sources and scope ambiguity; only 56 test positives; no fresh transaction experiment; no verified temporal/sender/source isolation; inaccessible literature details; ambiguous published SVM kernels; varying spam-versus-phishing definitions; selection-biased fold/validation summaries; and host timings without phone measurements. The bootstrap does not remove these limitations. Changing dataset sizes, class prevalences, thresholds or metric averaging makes unrelated numerical scores unsuitable for ranking algorithms.

## References

1. Shiksha. (2022). Application of Machine Learning Algorithms With Balancing Techniques for Credit Card Fraud Detection: A Comparative Analysis. In P. Singh (Ed.), *Fundamentals and Methods of Machine and Deep Learning*, pp. 277–309. Wiley. [DOI: 10.1002/9781119821908.ch12](https://doi.org/10.1002/9781119821908.ch12).
2. Dai, M. (2023). Multiple Machine Learning Models on Credit Card Fraud Detection. *BCP Business & Management*, 44, 334–338. FIBA 2023 proceedings. [DOI: 10.54691/bcpbm.v44i.4839](https://doi.org/10.54691/bcpbm.v44i.4839).
3. Wijaya, M. G., Pinaringgi, M. F., Zakiyyah, A. Y., & Meiliana. (2024). Comparative Analysis of Machine Learning Algorithms and Data Balancing Techniques for Credit Card Fraud Detection. *Procedia Computer Science*, 245, 677–688. [DOI: 10.1016/j.procs.2024.10.294](https://doi.org/10.1016/j.procs.2024.10.294).
4. Çavdar, E. Z., & Bozanta, A. (2026). AI-based credit card fraud detection: a machine learning approach with model explainability on real-world data. *Knowledge and Information Systems*, 68, Article 161. [DOI: 10.1007/s10115-026-02773-7](https://doi.org/10.1007/s10115-026-02773-7).
5. Abid, M. A., Ullah, S., Siddique, M. A., Mushtaq, M. F., Aljedaani, W., & Rustam, F. (2022). Spam SMS filtering based on text features and supervised machine learning techniques. *Multimedia Tools and Applications*, 81(28), 39853–39871. [DOI: 10.1007/s11042-022-12991-0](https://doi.org/10.1007/s11042-022-12991-0).
6. Krawczyk, N., Probierz, B., & Kozak, J. (2025). Emotion and Phrase-Based Patterns in Smishing: A Feature-Driven Detection Framework. *Procedia Computer Science*, 270, 4421–4430. [DOI: 10.1016/j.procs.2025.09.567](https://doi.org/10.1016/j.procs.2025.09.567).
7. Corpuz, J. E. A., Diaz, S. Q., Palafox, L. B. M., Tan, M. C. T., & Solomon, K. Y. C. (2026). Machine Learning-Based Detection of SMS Phishing in the Philippine Context. In *Proceedings of the Workshop on Computation: Theory and Practice (WCTP 2025)*, *Atlantis Highlights in Computer Sciences*, 24, pp. 553–562. Atlantis Press. [DOI: 10.2991/978-94-6239-638-8_28](https://doi.org/10.2991/978-94-6239-638-8_28).
8. Asyiah, N., & Aktavia, W. (2026). Klasifikasi SMS Spam Menggunakan Algoritma Naive Bayes, Logistic Regression, dan Linear SVM Berbasis TF-IDF dan CountVectorizer. *Jurnal SISKOM-KB (Sistem Komputer dan Kecerdasan Buatan)*, 9(3), 312–320. [DOI: 10.47970/siskom-kb.v9i3.987](https://doi.org/10.47970/siskom-kb.v9i3.987).
9. scikit-learn developers. (n.d.). *LinearSVC; LogisticRegression; ColumnTransformer; Probability calibration; Feature extraction; average_precision_score*. Official technical documentation, accessed 13 October 2026. [LinearSVC](https://scikit-learn.org/stable/modules/generated/sklearn.svm.LinearSVC.html), [LR 1.6](https://scikit-learn.org/1.6/modules/generated/sklearn.linear_model.LogisticRegression.html), [ColumnTransformer 1.6](https://scikit-learn.org/1.6/modules/generated/sklearn.compose.ColumnTransformer.html), [calibration](https://scikit-learn.org/stable/modules/calibration.html), [features](https://scikit-learn.org/stable/modules/feature_extraction.html), [AP 1.6](https://scikit-learn.org/1.6/modules/generated/sklearn.metrics.average_precision_score.html). Current documentation may differ from pinned runtime defaults; the executed code specifies its settings.
10. imbalanced-learn developers. (n.d.). *Common pitfalls and recommended practices*. Official technical documentation, accessed 13 October 2026. [Documentation](https://imbalanced-learn.org/stable/common_pitfalls.html).
11. SmishGuard local research artifacts. (2026). *Supplied-update audit and fixed-setting comparison*, 13 October; frozen experiment `research/data/newdata-20261013/experiment-v2/`; new LR/SVM study `research/data/lr-svm-review-20261013/experiment-v2/`. [Existing aggregate report](new-dataset-comparison-20261013.md). These are project evidence, not peer-reviewed publications.
