# VeriTxt thesis defense study guide

Prepared 26 October 2026 from this repository's recorded experiments, implementation, and acceptance report. Suggested answers are speaking aids: adapt them to the final approved manuscript. The reasons offered for design choices explain the recorded procedure; they do not establish what the team originally intended or what the adviser approved.

**Start here: identify the version you will demonstrate.**

There are multiple fitted models and application variants. Their datasets, features, thresholds, and metrics are different.

| Version or experiment | Classes | Training design | Appropriate evidence |
|---|---|---|---|
| Latest UAT target: Grouped SMS Previews APK, package `ph.smishguard.svm.oldbinary` | Ham / Smishing | Approximate grouped 60/20/20; 1,540 / 516 / 498 messages | Extracted-model training record and October 13 grouped experiment |
| Separate SVM 60% application | Ham / Smishing / Gambling | 2,281 / 761 / 761 messages | October 20 multiclass study; SVM-60 row |
| Separate SVM 80% application | Ham / Smishing / Gambling | 3,042 fitting messages; 761 shared test messages | October 20 multiclass study; SVM-80 row |
| Separate Cashback Review application | Ham / Smishing / Gambling | Same frozen three-class SVM-60 | Same model metrics; separately changed application risk rule |

The latest documented UAT target is the binary version; that does not prove which version is installed on your defense phone. Check its application label, package, and model status before preparing screenshots. A three-class result table must not be presented as the binary APK's accuracy. No training or test evaluation was rerun to prepare this guide.

**1. Explain the study in one minute.**

Suggested answer:

> Our study addresses SMS phishing, or smishing, in which deceptive messages attempt to make recipients disclose sensitive information or take harmful actions. We developed VeriTxt, an Android application that assesses SMS locally using a trained text-classification model and supporting risk indicators. Users can paste or share messages for checking and can enable incoming-SMS assessment with consent and the required permissions. We compared documented machine-learning configurations and examined both classification performance and software integration. The application supports user judgment; an assessment cannot establish that a sender or message is authentic.

Use the exact approved thesis title and objectives from your manuscript. The repository records historical scope changes and does not establish a final approved title.

**2. Know what the app actually does.**

- Native Android implementation using Kotlin and Jetpack Compose.
- Manual text entry, paste, and Android plain-text sharing.
- Offline inference using model parameters packaged in the APK.
- Optional incoming-SMS assessment, requiring consent, scanning opt-in, and Android permissions.
- Risk level, an ordinal risk index, visible supporting indicators, and recommended action.
- English and Filipino interface text; themes and preferences.
- A user-confirmed handoff to Android's blocked-number settings. Android and the user perform the actual blocking.
- Temporary message/checking state rather than a persistent scan-history database.

Important boundaries:

- This is SMS assessment. It does not monitor Messenger, WhatsApp, or RCS.
- The selected build uses one active classifier. Historical LR, NB, SVM, and mBERT builds are alternatives.
- The phone performs inference, not model training or automatic retraining.
- The current manifest declares RECEIVE_SMS and POST_NOTIFICATIONS; it does not declare INTERNET or READ_SMS.
- There is no live sender-authentication service, URL reputation lookup, or link-destination inspection.
- Reporting is disabled in Android. The Flask/SQLite backend is a separate prototype with an unresolved payload-contract mismatch.
- Recent grouped notifications can show bounded message previews and numeric senders in the unlocked notification shade. Do not promise that text is never visible outside the result screen. Notifications are hidden on the lock screen under the documented policy, and Android may retain notification history.

Suggested answer to “Why offline?”:

> We perform detection locally so checking does not require sending SMS text to an inference server and can work without an internet connection. This supports local processing and availability. The tradeoff is that the app cannot consult current threat intelligence or verify a link's destination.

**3. Understand the complete flow.**

```text
Development computer:
Labeled corpus -> eligibility/cleaning -> related-message groups -> partitions
-> training-only text features -> validation/tuning -> frozen model
-> held-out evaluation -> export parameters -> Python/Android parity checks

Android application:
Paste/share/permission-authorized incoming SMS -> input checks
-> build-specific preprocessing -> frozen text features -> classifier
-> separate supporting-indicator risk policy -> result/notification/advice
```

Training learns parameters. Validation chooses settings. Testing measures the frozen configuration. Export transfers the learned parameters; it is not another training stage.

The indicator list explains visible rule matches. It is not a complete explanation of every learned SVM feature contribution.

**4. Know the terminology.**

| Term | Plain explanation |
|---|---|
| Supervised learning | Learning a mapping from messages to supplied labels |
| NLP | Methods for processing language; here, text normalization, tokens, and features |
| Feature | A numerical input such as a weighted word or two-word sequence |
| Vocabulary | The feature names learned from fitting messages |
| Sparse vector | A numerical representation with mostly zero entries |
| Hyperparameter | A setting chosen outside the coefficient-fitting procedure, such as SVM C |
| Parameter | A learned quantity, such as an SVM feature weight |
| Overfitting | Fitting patterns that do not transfer well beyond the development data |
| Generalization | Performance on other messages, sources, or future conditions |
| Leakage | Information crossing an evaluation boundary in a way that compromises the intended assessment |
| Calibration | Mapping scores toward empirical event frequencies; fitting such a map does not establish reliability in future traffic |
| Ablation | Comparing a configuration with a feature or component removed |
| Retrospective study | Evaluation using an existing corpus rather than a newly collected future cohort |

**5. Explain TF-IDF.**

TF-IDF means term frequency multiplied by inverse document frequency. It turns text into weighted numerical features. A term receives more weight when it appears in a message but is relatively uncommon across the fitting corpus. L2 normalization scales each nonzero message vector to unit Euclidean length.

With smoothed IDF and raw counts, the basic calculation is:

```text
idf(term) = log((1 + number_of_fitting_messages) / (1 + document_frequency(term))) + 1
feature(term, message) = occurrence_count(term, message) * idf(term)
then apply L2 normalization
```

Unigrams are single tokens; bigrams are adjacent token pairs. For the illustrative phrase “claim reward now,” possible features include “claim,” “reward,” “now,” “claim reward,” and “reward now,” subject to the variant's tokenizer and stopword rules.

Suggested answer:

> We used TF-IDF to represent messages numerically for the classical classifiers. Unigrams capture individual terms, while bigrams capture short phrases. We learned the vocabulary and IDF only from fitting data and reused those learned values when transforming validation, test, and application inputs.

Reference: [scikit-learn TfidfVectorizer](https://scikit-learn.org/1.6/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html).

**6. Explain Linear SVM and C.**

Linear SVM learns a linear decision function from weighted features. For a binary model:

```text
margin = weight_vector dot message_vector + intercept
```

Its optimization trades off a small weight norm with penalties for margin violations. C controls this tradeoff: larger C places greater emphasis on fitting violations, while smaller C applies stronger regularization. Larger C does not guarantee better performance.

Suggested answer:

> Linear SVM learns a decision boundary from the TF-IDF message features. It is a suitable candidate for sparse text and permits a compact numerical inference implementation. We selected its configuration through validation and checked its errors, rather than assuming it must outperform the alternatives.

The binary deployed model has C=10, L2 regularization, squared-hinge loss, no class weighting, and max_iter=10,000. This is an optimizer iteration ceiling, not 10,000 training epochs. The three-class study uses a separate max_iter=20,000 configuration and native one-versus-rest classification.

Reference: [scikit-learn LinearSVC](https://scikit-learn.org/1.6/modules/generated/sklearn.svm.LinearSVC.html). Exact project settings come from the local experiment records.

**7. Compare the algorithm families.**

| Algorithm | How it makes a decision | Main reason to examine it | Limitation to discuss |
|---|---|---|---|
| Multinomial Naive Bayes | Combines class priors and class-conditional feature evidence | Simple text-classification baseline | Its conditional-independence assumption is imperfect for correlated terms and bigrams |
| Logistic Regression | Learns a weighted linear function with logistic classification probabilities | Alternative linear baseline | Fitted probabilities still require calibration evaluation for the intended population |
| Linear SVM | Learns discriminative linear margins | Strong candidate for sparse text | Raw margins do not directly express probabilities |
| mBERT | Fine-tunes a pretrained multilingual transformer using contextual token representations | Contextual multilingual comparison | In the recorded experiment it required substantially greater training and packaging resources |
| Random Forest | Combines many decision trees | Additional nonlinear benchmark | Its result is specific to the supplied feature and tuning configuration |
| KNN | Classifies by labels of nearby feature vectors | Similarity-based benchmark | Prediction depends on the chosen representation, distance, neighbors, and retained reference data |

Do not say “Naive Bayes just counts scam keywords” or “SVM understands the whole meaning.” Both classical models learn from numerical text features and can fail on wording or sources that differ from training.

NB alpha is additive smoothing: it prevents an unobserved class-feature pair from receiving zero estimated likelihood. The three-class experiment searched seven alpha values and selected 0.01. This is a validation result, not a universal best value. TF-IDF values are fractional, although the estimator is called MultinomialNB; scikit-learn documents their practical use with this estimator.

References: [MultinomialNB](https://scikit-learn.org/1.6/modules/generated/sklearn.naive_bayes.MultinomialNB.html), [LogisticRegression](https://scikit-learn.org/1.6/modules/generated/sklearn.linear_model.LogisticRegression.html), [Google multilingual BERT](https://github.com/google-research/bert/blob/master/multilingual.md), [RandomForestClassifier](https://scikit-learn.org/1.6/modules/generated/sklearn.ensemble.RandomForestClassifier.html), [KNeighborsClassifier](https://scikit-learn.org/1.6/modules/generated/sklearn.neighbors.KNeighborsClassifier.html).

**8. Explain why 60/20/20 was used.**

60/20/20 is a data-partitioning design, not an algorithm. A defensible justification is that it assigns a majority to learning while retaining separate portions for development decisions and final evaluation. No ratio is automatically optimal.

| Portion | Role | What it must not become |
|---|---|---|
| 60% training | Learn vocabulary, IDF, and fitted classifier parameters | A pool silently enlarged with test messages |
| 20% validation | Choose permitted configurations and, in the binary study, a decision threshold | Final unbiased evidence after repeatedly choosing against it |
| 20% test | Evaluate the frozen configurations | A tuning set for changing C, threshold, features, or split |

Ready-to-say answer:

> We used an approximately 60/20/20 design to separate learning, model selection, and final evaluation. Training data fitted the representation and classifier. Validation data supported configuration and threshold selection. The test set was reserved for evaluating the frozen configuration. We also kept related message templates together to reduce leakage from near-copy messages. We do not claim this ratio is universally best; it is a practical design whose adequacy depends on the class support and independence of the partitions.

If asked “Why not 80/20?”:

> An 80/20 design can also be appropriate when tuning takes place entirely inside the 80% training portion. Our separate three-class experiment used five group-aware folds within that portion. The key issue is preserving an outer test set while performing all development decisions within the development portion.

If asked “Why not 70/15/15?”:

> That is another reasonable allocation. We cannot prove 60/20/20 is superior without a prespecified comparison. We can defend the distinct roles of the partitions and report their realized class and group support.

These answers describe the method's rationale. Do not attribute the ratio to an adviser, published standard, or a search for the highest test accuracy unless you have direct evidence.

**9. Explain stratification and grouping.**

Stratification attempts to preserve class proportions. Grouping keeps related records together. They address different concerns.

Example: “Your account is locked, verify at LINK A” and the same template with LINK B should not be treated as independent training and test examples just because the URL differs.

The binary grouped experiment used label-blind template components and ten stratified group folds: six folds for training, two for validation, two for testing. Groups cannot be split just to obtain exact row percentages. Its actual 1,540/516/498 partition is approximately 60.30%/20.20%/19.50%.

The separate multiclass study used constrained whole-component allocation to produce near-exact 60/20/20 row and class counts. It is a different splitter from the binary study.

Suggested answer:

> We considered message relationships as well as class proportions. Keeping related templates together reduces the chance that evaluation mainly measures recognition of near-copies. The audit found no computed group crossing in the grouped split, although heuristic grouping cannot prove all campaigns or paraphrases are independent.

In the binary random-split track, 97 computed template groups crossed training and test. The grouped track had zero detected crossings. Because the tracks have different test memberships, their numerical difference cannot be attributed solely to removing leakage.

References: [StratifiedGroupKFold](https://scikit-learn.org/1.6/modules/generated/sklearn.model_selection.StratifiedGroupKFold.html), [data leakage guidance](https://scikit-learn.org/1.6/common_pitfalls.html#data-leakage).

**10. Memorize the deployed binary model's training procedure.**

1. Recorded input view: 3,340 messages.
2. Hold 59 flagged messages and remove 727 duplicates in the masked casefolded view.
3. Retain 2,554: 2,229 Ham and 325 Smishing. Labels are inherited source/rule labels.
4. Construct related-message groups, then allocate grouped training, validation, and test partitions.
5. Fit word-unigram/bigram TF-IDF using lowercase Unicode tokens of at least two code points, the 318-word scikit-learn English stopword list, smoothed IDF, raw term counts, and L2 normalization. Learn the vocabulary only from fitting records.
6. Fit LinearSVC with C=10 and the recorded settings. No SMOTE or class weighting is applied in this selected path.
7. Generate margins using three training-only group-aware out-of-fold fits, each with its own vectorizer. Fit a logistic sigmoid to those margins.
8. Use validation to select the candidate and score threshold. Search 0.05 through 0.95 in 0.01 steps, maximizing F1 subject to precision at least 0.90 and at least five true positives, with the recorded tie rules.
9. Freeze the selected pipeline and its approximately 0.37 inclusive threshold. Evaluate on the 498-message test set.
10. Export the exact parameters and preprocessing contract, then verify native inference consistency.

| Partition | Total | Ham | Smishing |
|---|---:|---:|---:|
| Training | 1,540 | 1,345 | 195 |
| Validation | 516 | 459 | 57 |
| Test | 498 | 425 | 73 |

The final binary vocabulary contains 18,473 features. Raw app input must use the matching cleaning/masking adapter; it is not interchangeable with the later raw-text multiclass tokenizer.

**11. Explain calibration and the 0.37 threshold correctly.**

The deployed binary path maps a raw SVM margin through a fitted sigmoid and compares the score with the stored validation-selected threshold, approximately 0.37.

Suggested answer:

> The raw SVM margin is not a probability. Our binary pipeline fits a sigmoid using training-only out-of-fold predictions, then selects its classification threshold using validation under the recorded precision/F1 criterion. The fitted transformation has not been independently validated as a reliable real-world fraud probability.

If asked “Why not 0.5?”:

> A default cutoff need not achieve the desired precision/recall tradeoff. We selected the allowed cutoff using validation and froze it before the run's final evaluation. This does not establish that 0.37 is optimal for future traffic.

The logistic fit is a calibration component of this binary SVM pipeline. It does not mean the phone is running a voting ensemble of separate SVM and LR classifiers.

**12. Know the binary results and calculate the metrics.**

The selected grouped `svm-C-10.0` model produced:

| Actual / predicted | Ham | Smishing |
|---|---:|---:|
| Ham | 421 | 4 |
| Smishing | 3 | 70 |

Taking Smishing as positive: TN=421, FP=4, FN=3, TP=70.

```text
Accuracy  = (TP + TN) / all messages = 491 / 498 = 98.59%
Precision = TP / (TP + FP)          = 70 / 74   = 94.59%
Recall    = TP / (TP + FN)          = 70 / 73   = 95.89%
F1        = 2TP / (2TP + FP + FN)  = 140 / 147 = 95.24%
FPR       = FP / (FP + TN)          = 4 / 425   = 0.94%
FNR       = FN / (FN + TP)          = 3 / 73    = 4.11%
```

The accuracy above is arithmetic from the reported confusion matrix. These are retrospective classifier metrics under the experiment's inherited labels. They are not accuracy estimates for the newer combined risk policy or all Philippine SMS.

Suggested answer:

> On its recorded 498-message grouped test set, the selected binary model detected 70 of 73 Smishing messages and incorrectly flagged four of 425 Ham messages. That corresponds to 95.89% recall and 94.59% precision. The result is encouraging within this retrospective experiment, with label, source, and historical-exposure limitations.

Precision asks “How many flagged messages were labeled Smishing?” Recall asks “How many labeled Smishing messages did we detect?” False positives can erode trust in legitimate messages. False negatives can leave harmful messages undetected. Both matter.

**13. Explain the controlled three-class comparison.**

The October 20 experiment compared LinearSVC with MultinomialNB on the same Ham/Smishing/Gambling task. It began with 4,261 supplied records and used 3,803 eligible records: 3,055 Ham, 363 Smishing, and 385 Gambling. There were 458 exclusions; overlapping exclusion reasons must not be added together.

| Partition | Total | Ham | Smishing | Gambling |
|---|---:|---:|---:|---:|
| train60 | 2,281 | 1,833 | 218 | 230 |
| validation20 | 761 | 611 | 73 | 77 |
| test20 | 761 | 611 | 72 | 78 |
| train80 = train60 + validation20 | 3,042 | 2,444 | 291 | 307 |

Both classifiers used identical TF-IDF settings and fitting memberships at each training size. This feature policy preserves URL/number/currency tokens and uses 13 conservative English stopwords. It differs from the binary app model's masked input and broad English stopword list.

For 60% fitting, choose C or alpha by validation macro F1, then fit the selected setting on the same 60% only. For 80% fitting, choose the setting using five shared training-only group folds, then fit it on all 80%. The same 761 test messages are used for all four prespecified configurations.

| Configuration | Accuracy | Macro F1 | Smishing precision | Smishing recall | Correct / 761 |
|---|---:|---:|---:|---:|---:|
| SVM-60 | 97.24% | 94.13% | 100.00% | 79.17% | 740 |
| NB-60 | 96.98% | 93.61% | 98.36% | 83.33% | 738 |
| SVM-80 | 97.63% | 95.06% | 100.00% | 83.33% | 743 |
| NB-80 | 97.11% | 93.67% | 96.77% | 83.33% | 739 |

All selected SVM settings use C=10; both NB settings use alpha=0.01. The three-class SVM chooses the largest of its one-versus-rest margins. It has no binary sigmoid cutoff of 0.37.

Suggested answer:

> In the controlled three-class experiment, SVM had the higher observed macro F1 at both training sizes. At 80%, SVM reached 95.06% macro F1 compared with 93.67% for NB. However, both detected 60 of 72 Smishing messages, so both had 83.33% Smishing recall. SVM's advantage involved fewer Gambling errors and higher Smishing precision. At 60%, NB actually had higher Smishing recall. Our preference for SVM is therefore provisional and depends on which errors we prioritize.

**14. Explain why macro F1 was primary.**

The three-class corpus is approximately 80.33% Ham. Predicting Ham for every eligible record would already yield about 80.33% corpus accuracy while detecting no Smishing or Gambling.

Macro F1 computes F1 separately for every class, then averages those F1 values equally. Weighted F1 instead weights class F1 by class support. Macro F1 is not generally the harmonic mean of macro precision and macro recall.

Suggested answer:

> We used macro F1 for the three-class comparison because the classes are imbalanced and we wanted each class to contribute equally to the primary summary. We also reported class-specific precision and recall, particularly Smishing recall, because a single average cannot show the safety-relevant mistakes.

Reference: [scikit-learn classification metrics](https://scikit-learn.org/1.6/modules/model_evaluation.html#classification-metrics).

**15. Explain uncertainty and cross-validation.**

Cross-validation repeatedly fits on part of the development data and validates on the remaining fold. It helps configuration selection; the outer test set stays outside these folds.

The 80% experiment's tuning mean macro F1 was 88.74% for SVM and 89.56% for NB. Their fold population standard deviations were 6.34 and 3.83 percentage points. NB thus had the higher tuning mean even though SVM had the higher final test score. Fold SD is not a confidence interval or an independent-sample standard error.

The paired whole-component bootstrap used 2,000 replicates. For SVM-80 minus NB-80, the macro-F1 difference was 1.39 percentage points, with a conditional 95% interval of -0.67 to +4.24 points. It includes zero. The 60% algorithm difference and within-algorithm training-regime differences also have intervals including zero.

Suggested answer:

> SVM performed better on the observed test partition, but the paired group-bootstrap interval includes zero, so we cannot establish a stable general advantage. These intervals describe the frozen models on the observed test components and do not include all uncertainty from training, labels, or source selection.

More training data was not the only changed factor between 60% and 80%: tuning changed from a single validation set to five-fold grouped CV. Do not describe the difference as a pure causal effect of training size.

**16. Keep older comparisons in their own context.**

The October 5 four-model experiment used a different binary corpus and four partitions, including a separate calibration portion. Its 448-message test contained 392 Ham and 56 Smishing messages.

| Model | Accuracy | Smishing precision | Smishing recall | Smishing F1 |
|---|---:|---:|---:|---:|
| LR | 94.20% | 96.88% | 55.36% | 70.45% |
| NB | 91.07% | 83.33% | 35.71% | 50.00% |
| Linear SVM | 98.21% | 98.00% | 87.50% | 92.45% |
| mBERT | 92.63% | 100.00% | 41.07% | 58.23% |

SVM had the highest observed Smishing F1 in that run. mBERT's zero observed false positives did not make it the best detector: it missed 33 of 56 Smishing examples. This demonstrates why precision alone is insufficient. It does not establish universal SVM superiority over transformers. In that experiment, 439/448 test records had detected historical overlap.

The October 19 all-algorithm experiment used another binary test of 684 messages, only nine computed components. Its largest component held 606 messages. A separate generalization review qualified earlier 99.71% claims. Do not rank its accuracies directly against the 498- or 761-message experiments. Different feature paths also mean some rows compare full configurations rather than only estimator choice.

Suggested answer to “Why do the reports show different scores?”:

> They describe different experiment versions, eligible datasets, class definitions, preprocessing, and evaluation designs. I will identify the run and test set for each figure. A higher score on a different test set does not establish improvement over the deployed model.

**17. Explain why SVM-60 might be demonstrated when SVM-80 scored higher.**

Suggested answer:

> The SVM-60 application was packaged as a separate requested testing build. Its existence is not evidence that 60% is the best training size. In the controlled study, SVM-80 had higher observed overall performance, with an uncertain difference. The application demonstration and research comparison must each identify the exact frozen model being used.

Both frozen three-class models predicted Ham on the documented cashback example. Switching from 80% to 60% did not repair that classification. The separate Cashback Review profile added an application risk cue while leaving the model's Ham prediction unchanged.

Do not say the 60% model is better because it uses fewer training messages, avoids memorization automatically, or performed better on one chosen demonstration input.

**18. Separate model category, model score, and app risk.**

| Output | Meaning |
|---|---|
| Ham / Smishing / Gambling | Class predicted by the three-class classifier; binary builds omit Gambling |
| Binary fitted score | Sigmoid-transformed SVM margin compared with its frozen threshold |
| Three-class margins | Raw one-versus-rest decision values; the largest selects the class |
| Risk index 0-100 | Capped sum of provisional supporting-indicator weights |
| Low / Medium / High | Bands of that displayed risk index: 0-29 / 30-69 / 70-100 |
| Unable to assess | No scored assessment because input/evidence/model execution is insufficient |

In the documented risk policy, the model flag contributes 40 points, so it alone produces Medium Risk. Other indicators can raise the result. A direct request to disclose credentials is a stronger cue. These weights are engineering choices, not fitted SVM coefficients or thresholds established by a cited standard.

Suggested answer:

> The classifier output and risk index are separate. The model predicts a category; the application combines its model signal with visible supporting indicators to produce an ordinal risk level. A score of 70 means the indicators reached our High Risk band, not that fraud has a 70% probability. A Ham category can coexist with a risk warning when separate rules identify concerning content.

Classifier-only test metrics do not validate the combined rule-based risk output. Changing a rule is not model retraining and needs its own evaluation.

**19. Explain what was tested.**

There are three different forms of evidence:

1. Classification evaluation: compare model predictions with the dataset's labels.
2. Software parity and workflow testing: check that exported Python and Android inference match and app actions work.
3. Human/user acceptance: evaluate usability, accessibility, intended device behavior, and stakeholder criteria.

Parity asks whether Android faithfully computes the selected model. It does not ask whether that model is correct about fraud.

The latest October 26 UAT report recorded 44 Pass, 3 Fail, 3 Not executed, and 11 Blocked across 61 tracker cases. Its decision was NOT READY FOR FULL SIGN-OFF. All 25 grouped-notification checks passed; supplemental instrumentation retained 21 passes and two failures. It was one API36 emulator run, not a new physical-phone acceptance study.

Suggested answer:

> We have documented software tests and model-parity evidence for specific builds. The latest acceptance run also records failures and missing human/device evidence. We distinguish implemented and tested functions from full stakeholder sign-off, and we retain those unresolved findings in our limitations and remaining work.

**20. Be prepared for the strongest limitations question.**

Suggested answer:

> The main limitations are inherited labels without complete independent confirmation, historical corpus exposure, uneven source representation, imperfect grouping, and limited evidence for future traffic. Our grouped partitions reduce detected template overlap within a run, but they cannot establish complete independence or representativeness. The model can miss unfamiliar phrasing, and local processing cannot authenticate a sender or inspect a link destination. We therefore present VeriTxt as an experimental decision-support prototype.

Specific evidence behind this answer:

- Binary held-source stress results varied substantially; the recorded post-selection Tagalog-source diagnostic had F1 of about 35.09%. It was not an unbiased nested source-held-out estimate, but it exposes a transfer concern.
- Only ten binary grouped-test positives were Filipino/Taglish. This is insufficient to claim broad local-language reliability.
- The multiclass test's largest computed component contained 417/761 messages, or 54.80%.
- The marketing source contributed 616/761 multiclass test messages, or 80.95%.
- Group separation and source imbalance are different issues; solving one does not solve the other.
- A new split does not erase earlier exposure of the same corpus during development.
- Zero false positives on a finite test does not establish zero future false positives.

**21. State the contribution and future work accurately.**

Suggested answer to “What is novel?”:

> Our contribution is the applied system: a local Android SMS-assessment workflow, explicit model and risk outputs, documented comparative experiments, and a verified path from the frozen Python model to Android inference. We used established algorithms; we do not claim to have invented SVM or a new learning algorithm. The exact contribution should be assessed against the related work in our approved manuscript.

Suggested answer to “How would you improve it?”:

> I would prioritize independently adjudicated, newly collected SMS from the intended population, including ordinary legitimate messages and difficult Filipino/Taglish cases. I would freeze the full model and risk policy before future evaluation, use source/time-aware separation, and report per-class errors and abstentions. I would also complete physical-device, accessibility, and human acceptance checks. Model changes should follow those findings rather than tuning against selected demonstration messages.

**22. Rapid panel practice with answers.**

| Panel question | Core answer |
|---|---|
| Is 60/20/20 your algorithm? | No. It is the allocation of training, validation, and test data. The classifier is Linear SVM. |
| Does the app learn from every checked SMS? | No. It uses frozen packaged parameters; it does not retrain from user scans. |
| Is this just keyword matching? | The SVM learns weighted combinations of TF-IDF features. Separate application indicators do use explicit rules. |
| Does mentioning a bank make a message fraudulent? | No. A claimed organization name does not authenticate the sender or establish fraud. |
| Why not use 100% of the records for training? | A performance study needs data excluded from fitting and development decisions. A later full-data deployment fit would need separate evaluation evidence. |
| Does 98.59% accuracy mean a checked message is 98.59% safe? | No. It is a retrospective aggregate classification rate on the named binary test set. |
| Why not choose only the highest accuracy? | Class imbalance and the cost of missed Smishing require class-specific precision/recall and appropriate F1 summaries. |
| Is Gambling identical to Smishing? | No. The three-class study treats them separately under supplied labels; gambling-related fraud may be labeled Smishing. |
| What happens if checking cannot run? | The app should show Unable to assess, not label the message safe. |
| Does the app block numbers automatically? | No. It offers a confirmed handoff; the user adds/confirms the actual sender in Android. |
| Are visible indicators a full SVM explanation? | No. They explain matched application cues, not every learned contribution. |
| Why did the newer model perform differently? | Check the experiment's dataset, features, class definitions, and tuning before attributing a change to the algorithm. |
| Can you guarantee privacy? | State the implemented local-processing and storage boundaries precisely; notifications, screenshots, and explicit clipboard actions have separate exposure paths. |
| Can you guarantee detection? | No. Report the documented errors, coverage, and scope limitations. |

**23. What to memorize first.**

1. Your approved problem statement, objectives, intended users, and scope.
2. The exact APK and class set you will demonstrate.
3. The difference between training, validation, testing, calibration, and software parity.
4. Your concise 60/20/20 justification and whole-group separation.
5. How TF-IDF and Linear SVM operate, and what C controls.
6. Binary counts: 2,554 eligible; 1,540 train / 516 validation / 498 test.
7. Binary confusion counts: 421 TN / 4 FP / 3 FN / 70 TP.
8. Binary precision 94.59%, recall 95.89%, F1 95.24%, accuracy 98.59%.
9. Three-class comparison: SVM-80 macro F1 95.06%, NB-80 93.67%; both Smishing recall 83.33%.
10. Risk index is not a probability; Low Risk does not authenticate a message.
11. The strongest limitations and what remains unvalidated.
12. The contribution is the system and evaluation work using established algorithms.

Practice aloud. For each answer: state the decision, explain the reason, name the relevant evidence, then give the practical limit. Do not substitute memorized percentages for understanding what their denominators represent.

**Project evidence to consult.**

- [Exact binary APK model and training procedure](veritxt-extracted-model-training-20261020.md).
- [Binary grouped/random experiment, baseline comparisons, and diagnostics](bantaytext-comparison-20261013.md).
- [Controlled three-class report with full confusion matrices and uncertainty](multiclass-comparison-20261020/THESIS-REPORT.md).
- [Three-class protocol and tuning rules](multiclass-comparison-20261020/PROTOCOL.md).
- [SVM-60 deployment and its distinction from SVM-80](svm60-android-20261020/DEPLOYMENT.md).
- [Separate Cashback Review rule](cashback-review-20261020/REVIEW.md).
- [Application risk-index policy](risk-policy.md).
- [Grouped notification previews](grouped-sms-previews-20261021.md).
- [Historical four-model comparison](four-model-comparison-20261005.md).
- [Historical all-algorithm comparison](all-algorithms-8020-20261019/RESULTS.md).
- [Latest acceptance findings](../outputs/uat-20261026/UAT_Report.md).

The architecture/module overviews contain older milestones. Use the latest variant-specific integration and behavior records when they differ. Historical “not installed” statements in a research report do not override a subsequent separately documented integration, and later integration does not strengthen the research accuracy evidence.
