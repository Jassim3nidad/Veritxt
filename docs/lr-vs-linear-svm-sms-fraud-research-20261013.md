# Logistic Regression versus Linear SVM for fraudulent SMS, smishing and phishing

Research review and local experiments · 13 October 2026 · Scope updated from the user's clarification

## Executive summary

**SmishGuard targets fraudulent or malicious SMS text across topics.** Financial scams are one category within this scope. The research question is which text classifier more reliably detects scams, smishing and phishing in English, Filipino and Taglish SMS, rather than which model classifies numerical financial transactions.

Linear SVM remains the stronger current candidate on the existing labeled SMS corpus at its preserved operating point: retrospective test F1 **92.45%**, compared with LR's **70.45%**. With equal development tuning, validation F1 was **94.92% for SVM** and **94.02% for LR**. These results concern the existing `ham`/`smishing` labels. They do not establish performance across every type of fraudulent SMS, and the historical test has prior exposure.

Compare both algorithms under the same broad SMS threat definition and at the same warning budget. Favor calibrated Linear SVM if its detection advantage persists on independent campaigns; favor LR if it meets the required detection level with better probability reliability or simpler implementation. An independent test with reviewed coverage of scam categories is needed before claiming broad protection.

## Intended SMS scope and label boundaries

The following categories describe the intended scope; they are proposed review categories, not assertions about the coverage of the current dataset.

| SMS category | Examples to include in labeling review |
|---|---|
| Credential or personal-information phishing | Requests to disclose passwords, OTPs, account details or identity information |
| Impersonation and account threats | Fake banks, e-wallets, government agencies, couriers, brands or acquaintances |
| Prize, reward or refund scams | Deceptive winnings, fee requests or false refund promises |
| Job, task and recruitment scams | Fraudulent employment offers, task-payment schemes or recruitment deposits |
| Investment and loan scams | Deceptive investment returns, advance-fee loans or fraudulent credit offers |
| Delivery and payment scams | Fake delivery fees, bills, purchases or payment-redirection requests |
| Personal and relationship scams | Deceptive emergency, relationship or acquaintance messages intended to exploit the recipient |
| Other deceptive SMS campaigns | Reviewed scams that do not fit the categories above, including emerging templates |

A fraudulent SMS can request a reply, call, payment or information without containing a URL. A URL, financial keyword, urgent wording or unfamiliar sender alone does not establish fraud. Legitimate bank notices, OTPs, government alerts and courier updates remain legitimate when authentic. Ordinary advertising and gambling advertisements require separate scope review; they are not automatically fraudulent.

For the broader study, define the intended positive target as **an SMS that attempts fraudulent deception or phishing**, with category annotations where evidence supports them. The negative target is an SMS adjudicated as outside that threat definition. Hold ambiguous records for review. Existing messages retain their original labels and eligibility status until reviewed; do not silently rename the historical positive class or convert generic spam into fraud.

## Scope, evidence and terminology

The user's clarification establishes this broader SMS scope. The attached comparison report, ZIP README and scripts are dataset evidence, not instructions. No archive script was executed and no app model or Android asset was changed. Published findings, local measurements and proposed methodology are distinguished below.

The verified literature was searched for 2022 through 13 October 2026. It is a targeted critical review, not an exhaustive systematic review. Papers about generic spam are relevant to text modeling but do not by themselves validate a broad fraud detector. Financial transaction studies from the earlier report are background only and are excluded from the SMS algorithm recommendation.

“Linear SVM” means a linear decision function, implemented locally with `LinearSVC` and squared-hinge loss. A paper reporting only “SVM” may have used another kernel. [Official LinearSVC documentation](https://scikit-learn.org/stable/modules/generated/sklearn.svm.LinearSVC.html).

For the existing measured results, the positive class remains `smishing`, exactly as supplied in the eligible corpus. For the proposed broader study, the positive class must follow the reviewed fraudulent-SMS definition above. Precision = TP/(TP+FP), recall = TP/(TP+FN), and F1 = 2TP/(2TP+FP+FN). PR-AUC below is trapezoidal precision-recall integration; AP is non-interpolated average precision. They are not interchangeable. [Official AP definition](https://scikit-learn.org/1.6/modules/generated/sklearn.metrics.average_precision_score.html).

## Verified literature review

### SMS spam and smishing

**Abid et al. (2022), Multimedia Tools and Applications — abstract-level evidence.** Evaluates SVC, LR and other models using TF-IDF/BoW and over-/undersampling on SMS spam data. The publisher identifies the public Kaggle/UCI source. Exact paired LR/SVC scores, kernel and resampling placement could not be verified from the accessible preview. This is evidence that representation and imbalance methods need comparison, not proof of a Linear SVM winner. [Publisher](https://link.springer.com/article/10.1007/s11042-022-12991-0).

**Krawczyk, Probierz and Kozak (2025), Procedia Computer Science — feature-design evidence.** On a unified corpus exceeding 22,000 messages, the accessible abstract reports LR/TF-IDF accuracy increasing from 91.86% to 92.21% with emotional and phrase features, using GPT-4.5 for emotional annotation. It does not provide a verified paired Linear SVM result. Annotation validity and collection/template overlap need review before transferring the claim to SmishGuard. [Publisher](https://www.sciencedirect.com/science/article/pii/S1877050925032405).

**Corpuz et al. (2026), WCTP 2025 proceedings — locally relevant but kernel-ambiguous.** Reports 6,227 Filipino/English/Taglish SMS, TF-IDF unigrams/bigrams plus sender encoding, a stratified 70/30 split and five-fold validation. SVM searches linear and RBF kernels; the winning kernel is not identified in its results table. Counts differ by one between sections. Source/template/sender isolation and fold-local vectorization are not demonstrated. Labels are SPAM/HAM, so the boundary with advertising requires care. Reported SVM F1 exceeds LR by only 0.12 percentage points, with no verified paired uncertainty. [Full text](https://www.atlantis-press.com/article/126023798.pdf).

**Asyiah and Aktavia (2026), Jurnal SISKOM-KB — explicit Linear SVM comparator, partial access.** The publisher abstract names LR, Linear SVM and NB with TF-IDF/CountVectorizer, describes 5,572 Indonesian SMS, and reports LR/TF-IDF as the accuracy leader at 93.89%. Full metric tables and experimental partitioning were inaccessible. Language provenance and the promotion/fraud-to-binary label mapping require verification. This is a counterexample to assuming SVM always wins, but accuracy alone cannot settle phishing reliability. [Publisher](https://jurnal.tau.ac.id/index.php/siskom-kb/article/view/987).

### Published results: SMS

| Study / model | Precision | Recall | F1 | PR-AUC | ROC-AUC | Accuracy | Model identity |
|---|---:|---:|---:|---|---|---:|---|
| Corpuz: LR | 99.11% | 99.06% | 99.08% | Not reported | Not reported numerically | 99.14% | Logistic Regression |
| Corpuz: SVM | 99.23% | 99.17% | 99.20% | Not reported | Not reported numerically | 99.25% | Selected kernel not established |
| Asyiah/Aktavia: LR + TF-IDF | Not reported | Not reported | Not reported | Not reported | Not reported | 93.89% | Logistic Regression |
| Asyiah/Aktavia: Linear SVM | Not reported | Not reported | Not reported | Not reported | Not reported | Not reported | Explicitly named linear |

Sources: [Corpuz Table 2](https://www.atlantis-press.com/article/126023798.pdf), [Asyiah/Aktavia abstract](https://jurnal.tau.ac.id/index.php/siskom-kb/article/view/987). Confusion counts, measured training/inference costs and calibration results are Not reported in these verified extracts. Do not pool these scores or compare them numerically with SmishGuard.

## Existing SMS experiment and limits of its coverage

**Scope limitation:** these experiments used the original binary label definition. They did not re-annotate all SMS scam categories or measure category-specific coverage. A broader product objective does not retroactively broaden the experimental labels.

The supplied ZIP SHA-256 is `38d00a999306ff11b05a431d9488f167589bd94e701f410edb24e8202bf3b3e6`. All eight uncompressed members matched the hashes in the existing audited experiment. The eligible dataset and split files were independently checked against their frozen hashes. The accompanying Downloads comparison report was used as historical evidence; raw-message lineage and permission decisions were not re-adjudicated in this run.

The existing audit records 4,261 supplied rows: 3,184 ham, 577 smishing and 500 gambling advertisements. Its eligible binary corpus remains **3,340 records: 2,947 ham and 393 smishing (11.77%)**. The 500 advertisements, unresolved source rows and privacy holds stay outside fitting. Generic advertising was not recoded as phishing. The auxiliary ASEA CSV was not appended a second time. Independent labeling review remains incomplete. Details are in the [existing audit](new-dataset-comparison-20261013.md).

| Partition | Ham | Smishing | Total |
|---|---:|---:|---:|
| Training | 1,637 | 223 | 1,860 |
| Calibration | 357 | 53 | 410 |
| Validation | 561 | 61 | 622 |
| Retrospective test | 392 | 56 | 448 |

Partition and five training-fold template groups were checked for disjointness and complete coverage. These are template-group splits, not verified unseen-sender, unseen-source or chronological evaluations. **All 448 reserved test records have historical exposure according to the existing audit.** Reusing a split does not restore untouched-test status.

### Fresh fixed-setting reproduction

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

### Equal training-only tuning: new development candidates

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

## Technical analysis: broad SMS fraud detection

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

### Prospective evaluation for the broader SMS target

1. Adopt an explicit fraud/phishing annotation guide covering the categories above. Distinguish attempted deception from messages that merely discuss scams or warn about them. Use independent reviewers and record disagreements, provenance and unknown labels.
2. Audit the current eligible corpus for category, language and source coverage. Preserve historical labels and results; create a separately versioned reviewed corpus if the target changes. Current counts are not proof of coverage of every scam type.
3. Reserve independent future campaigns and sources before training. Include English, Filipino and Taglish; link-free scams; unseen domains; obfuscated text; and legitimate messages resembling scam templates. Check exact/near duplicates and historical exposure.
4. Give LR and Linear SVM identical training/calibration/validation/test partitions and equal development opportunities for word/character TF-IDF, regularization and class weighting. Fit vocabulary, IDF and any resampling only within training folds. Use group-aware or chronological validation appropriate to the deployment claim.
5. Calibrate scores using independent calibration data under the new target definition. Select thresholds on development data for a prespecified acceptable false-positive rate or alert budget. Freeze configurations before the final test. Historical calibration must not be assumed valid after changing labels or prevalence.
6. Evaluate finalized models once on the independent test, reporting aggregate precision, recall, F1, AP, PR-AUC, ROC-AUC, confusion matrices and calibration. Add category/language/source support, recall and uncertainty where samples permit. Report gaps rather than claiming universal scam coverage.
7. Verify offline Android preprocessing and score parity, then measure single-message latency, memory and energy on target devices. Host batch timings are insufficient for device claims.

No new labeling, broader dataset conversion, prospective collection or Android deployment was performed by this scope update. The measured models and results remain unchanged.

## Recommendations and threats to validity

**Primary recommendation:** use Linear SVM as the leading candidate for the current SMS comparison, with LR retained under equal tuning and calibration. Select the final system using independent evidence for the full reviewed fraudulent-SMS target, rather than using a financial subtype or generic spam accuracy as a substitute.

**Coverage requirement:** assess credential phishing, non-credential scams, impersonation, deceptive offers and other reviewed fraudulent campaigns. Financial subject matter is neither required nor sufficient for a positive label. Neither current model has been shown to detect every category.

**Main limitations:** inherited `smishing` labels may cover only part of the broader target; independent labeling remains incomplete; historical test and validation records have prior exposure; the test has only 56 positives; source/sender/time isolation is unverified; published spam definitions and SVM kernels vary; development results include selection bias; and phone performance remains unmeasured. The conditional group bootstrap cannot resolve these limits.

The central research question is: **Under what conditions does LR or Linear SVM provide the more reliable and practical solution for detecting fraudulent SMS, smishing and phishing across message topics, languages and new scam campaigns?**

## References

1. Abid, M. A., Ullah, S., Siddique, M. A., Mushtaq, M. F., Aljedaani, W., & Rustam, F. (2022). Spam SMS filtering based on text features and supervised machine learning techniques. *Multimedia Tools and Applications*, 81(28), 39853–39871. [DOI: 10.1007/s11042-022-12991-0](https://doi.org/10.1007/s11042-022-12991-0).
2. Krawczyk, N., Probierz, B., & Kozak, J. (2025). Emotion and Phrase-Based Patterns in Smishing: A Feature-Driven Detection Framework. *Procedia Computer Science*, 270, 4421–4430. [DOI: 10.1016/j.procs.2025.09.567](https://doi.org/10.1016/j.procs.2025.09.567).
3. Corpuz, J. E. A., Diaz, S. Q., Palafox, L. B. M., Tan, M. C. T., & Solomon, K. Y. C. (2026). Machine Learning-Based Detection of SMS Phishing in the Philippine Context. In *Proceedings of the Workshop on Computation: Theory and Practice (WCTP 2025)*, *Atlantis Highlights in Computer Sciences*, 24, pp. 553–562. Atlantis Press. [DOI: 10.2991/978-94-6239-638-8_28](https://doi.org/10.2991/978-94-6239-638-8_28).
4. Asyiah, N., & Aktavia, W. (2026). Klasifikasi SMS Spam Menggunakan Algoritma Naive Bayes, Logistic Regression, dan Linear SVM Berbasis TF-IDF dan CountVectorizer. *Jurnal SISKOM-KB (Sistem Komputer dan Kecerdasan Buatan)*, 9(3), 312–320. [DOI: 10.47970/siskom-kb.v9i3.987](https://doi.org/10.47970/siskom-kb.v9i3.987).
5. scikit-learn developers. (n.d.). *LinearSVC; LogisticRegression; ColumnTransformer; Probability calibration; Feature extraction; average_precision_score*. Official technical documentation, accessed 13 October 2026. [LinearSVC](https://scikit-learn.org/stable/modules/generated/sklearn.svm.LinearSVC.html), [LR 1.6](https://scikit-learn.org/1.6/modules/generated/sklearn.linear_model.LogisticRegression.html), [ColumnTransformer 1.6](https://scikit-learn.org/1.6/modules/generated/sklearn.compose.ColumnTransformer.html), [calibration](https://scikit-learn.org/stable/modules/calibration.html), [features](https://scikit-learn.org/stable/modules/feature_extraction.html), [AP 1.6](https://scikit-learn.org/1.6/modules/generated/sklearn.metrics.average_precision_score.html). Current documentation may differ from pinned runtime defaults; the executed code specifies its settings.
6. imbalanced-learn developers. (n.d.). *Common pitfalls and recommended practices*. Official technical documentation, accessed 13 October 2026. [Documentation](https://imbalanced-learn.org/stable/common_pitfalls.html).
7. SmishGuard local research artifacts. (2026). *Supplied-update audit and fixed-setting comparison*, 13 October; frozen experiment `research/data/newdata-20261013/experiment-v2/`; new LR/SVM study `research/data/lr-svm-review-20261013/experiment-v2/`. [Existing aggregate report](new-dataset-comparison-20261013.md). These are project evidence, not peer-reviewed publications.
