# Chapter 3 — Methods (draft)

Revised thesis title: **Pending finalization**. The existing manuscript title is retained as historical; title-dependent edits remain pending. This draft follows the team's clarification of **all SMS phishing**, without claiming adviser approval. See the [current scope record](scope-clarification-20261006.md).

This draft distinguishes the completed expanded development experiment from planned independent annotation, prospective evaluation and physical-phone testing. Bracketed placeholders require actual team evidence.

## 3.1 Research design and scope

The study developed and compared four offline SMS classifiers: Logistic Regression (LR), Multinomial Naive Bayes (NB), Linear Support Vector Machine (SVM) and multilingual BERT (mBERT). The completed comparison was a retrospective development experiment using source/rule-derived labels. All four algorithms received identical eligible records and partition assignments. The objective was to measure performance under a common protocol and verify deployment in separate Android variants, without selecting a predetermined winning algorithm.

The team clarified the scope as **all SMS phishing** on 6 October 2026. No adviser approval is assumed. Phishing includes deceptive SMS attempts to obtain credentials, money or personal information, or induce harmful actions, across financial and nonfinancial themes and with or without links. Genuine SMS form the negative class. A job, loan, delivery, government, reward or advertising theme alone neither excludes a phishing attempt nor establishes its label. Pure nonphishing spam and unresolved cases remain separately documented under the labeling guide.

The inherited historical package excluded advertising and job/loan fraud. That is a limitation of the completed cohort, not the current scope definition. Eighteen excluded job/loan records with possible phishing signals require independent review under the clarified definitions before admission to a new dataset version. Existing labels, membership and published historical scores are preserved. Broader scope does not establish representative coverage of every phishing type.

## 3.2 Data sources, audit and eligibility

The supplied archive contained 3,552 included messages: 3,084 ham and 468 smishing, with 2,594 supplied template groups and 71 flagged records. It also contained 2,272 excluded messages. The CSV, review workbook, documentation and builder were preserved unchanged in private storage. The builder was inspected before its pure definitions were used for auditing; its full source-loading/build procedure was not executed. Original raw sources were absent from the package, so validation of the delivered CSV is not an independent reproduction of the original dataset build.

Eligibility used previously documented, pinned source snapshots and use evidence. The expanded experiment retained 3,340 messages: 2,947 ham and 393 smishing. It held 60 GitHub-source records for unresolved permission evidence, 13 team/social records for unresolved origin/consent/use evidence, and 139 records for automated privacy concerns. The source-supported retained subset comprised ZERO/Tagalog records under CC0, Chua/marketing records under CC BY, and BwandoWando records restricted to local noncommercial research under CC BY-NC-SA. Existing attribution is preserved in the [source evidence](source-evidence.md). Content matching does not independently establish acquisition history or consent.

The audit checked schema completeness, duplicate IDs/text, conflicting normalized labels, template consistency, source counts and pending review status. No completed independent decisions were inferred from confidence fields, a “manually verified” description or a false review flag. The supplied 71 flagged and 300 validation-review entries had no completed labeler/final-label fields. Source/rule labels were used under explicit preliminary-development authorization and remain unconfirmed.

## 3.3 Privacy and feature preparation

Original files, ID crosswalks, message-level fingerprints, membership, fitted weights and predictions were kept outside public Git. Prediction features were restricted to redacted message text. Sender, source, rule category, confidence, review flags, IDs and dates were excluded from model inputs. These fields served only auditing, grouping or descriptive analysis.

All four algorithms shared a consistently minimized, case-preserving text view, replacing URL/email/digit content with the established placeholders. Conservative automated holds addressed possible names, addresses, obfuscated links and conflicts. Human privacy review remained pending. LR, NB and SVM then applied the established `sg-ascii-v1` preprocessing; mBERT retained case for its matching tokenizer. Learned vectorization was fitted exclusively within the relevant training folds and final training partition.

## 3.4 Template grouping, exposure and partitioning

The supplied template groups were audited rather than accepted as proof of independence. Label-blind unions combined supplied links and normalized near copies using SequenceMatcher similarity of at least 0.85. The audit merged 616 supplied groups and produced 1,848 retained components. The fixed split seed was 20260929. No component crossed partitions.

| Partition | Records | Ham | Phishing | Groups | Positive-bearing groups |
|---|---:|---:|---:|---:|---:|
| Training | 1,860 | 1,637 | 223 | 1,044 | 104 |
| Validation | 622 | 561 | 61 | 283 | 30 |
| Calibration | 410 | 357 | 53 | 270 | 25 |
| Test | 448 | 392 | 56 | 251 | 25 |

Calibration and evaluation partitions exceeded the protocol's minimum of 20 positives and 10 positive-bearing groups. Historical exact/near-copy checks compared the new records with earlier supplied corpora and frozen partitions. Detected overlap affected 3,269 of 3,340 retained records and 439 of 448 test records. Therefore, the new split did not establish independently unseen data. Imperfect automated groups and unavailable historical membership remain limitations.

## 3.5 Model training, selection and calibration

LR, Multinomial NB and Linear SVM used raw-count unigram TF-IDF with smooth inverse document frequency and L2 normalization. Five grouped training folds selected among C/alpha values 0.1, 1 and 10 using average precision, with vectorization refitted inside each fold. The selected values were LR C=10, NB alpha=0.1 and SVM C=10. Final pipelines were fitted on the training partition. A sigmoid calibrator was fitted once on the separate calibration partition. Validation F1 selected thresholds from 0.05 to 0.95 in 0.01 increments, with ties favoring the higher threshold. The resulting thresholds were 0.82, 0.63 and 0.59 respectively.

mBERT fine-tuned the full `google-bert/bert-base-multilingual-cased` model at revision `3f076fdb1ab68d5b2880cb87a0886f315b8146f8`, with its matching tokenizer and a binary classification head. All 177,854,978 parameters were trainable. The fixed configuration used seed 20261005, two epochs, Adafactor at 2e-5, weight decay 0.01, microbatch size 1, gradient accumulation of 8, gradient checkpointing and float16 CUDA autocast. Epoch 2 was selected by validation average precision. Calibration used only the calibration partition and threshold selection used validation, yielding approximately 0.89; the exact frozen serialized value governs comparisons.

Training-set token lengths determined the mBERT sequence length. The 95th percentile was 151.05 tokens, leading to a 160-token limit. This truncated 67 of 1,860 training records, compared with 193 at 128 tokens. Training ran on an RTX 3050 Laptop GPU with 4 GiB VRAM, within a predeclared 45-minute budget. Optimizer, scaler and random-state checkpoints supported resumption. The configuration was a practical bounded experiment rather than an exhaustive architecture or hyperparameter search.

## 3.6 Evaluation and uncertainty

All four selected pipelines were frozen before the final test opening. The same 448 records were evaluated once, and paired predictions were saved privately. No changes were made in response to unfavorable test predictions. Measures included phishing precision, recall and F1; macro-F1; accuracy; confusion counts and false-positive rate; Brier score and log loss; and reliability plots. These calibration measures reflect agreement with inherited labels, not established real-world probabilities.

Confidence intervals used 2,000 template-group bootstrap resamples with seed 20260929, holding fitted models fixed. Paired F1 differences used common resamples. These intervals omit fitting and selection uncertainty and do not apply a multiple-comparison correction. Source, language and category breakdowns were descriptive; full subgroup metrics required at least 20 records and at least five examples of each class. Sparse subgroups reported support only.

Classifier metrics and app policy were separated. App abstention was recorded as coverage and was never credited as a correct negative. All 448 test records were scored by each deployed pipeline in this completed experiment. Validation reuse for selection and threshold setting, inherited labels, historical exposure and source sampling constrain interpretation. Scores from earlier datasets cannot alone establish improvement.

## 3.7 Offline Android implementation and engineering verification

Separate LR, NB, SVM and mBERT variants retained the completed minimalist UI, “Model score” wording, privacy controls and distinct application IDs. Inference required no INTERNET permission. Reporting and automatic model-driven warnings remained disabled. mBERT used a faithful float32 ONNX export with its original architecture; no quantization or replacement was introduced.

Verification included Android build/lint/JVM checks, model guards, tokenizer/preprocessing and output parity, offline paste/share, missing/invalid assets, long/empty/random input, English/Taglish examples, repeated scanning and lifecycle/privacy checks. All four were timed in one API 36 x86_64 emulator session with four virtual CPUs and 4096 MiB configured RAM. Conditions used airplane mode, Wi-Fi off, one app process at a time, four identical fictional probes, 20 warmups and 200 measured scans. Cold loading was separate from warm inference. These measurements are not physical-phone results.

An additional packaging audit on 6 October removed unreferenced incremental ZIP space from mBERT. It preserved every referenced file's content and the fitted model assets. The original APK remains preserved, and the rebuilt artifact has separate integrity and emulator evidence. This engineering change did not retrain the model or alter the frozen research metrics.

## 3.8 Independent review and prospective validation (prepared, not completed)

Two blinded annotation packets were prepared for the 3,340 retained records. They contain unrelated random IDs, separately shuffled orders, redacted text and blank responses, without inherited labels, rule categories, confidence or model predictions. Two independent reviewers are to select `phishing`, `genuine`, `out_of_scope` or `uncertain` and provide rationales. Cohen's kappa and raw agreement will be calculated before third-person adjudication, retaining uncertainty and reporting missing responses. [Insert reviewer qualifications, actual independence attestations, dates, coverage, agreement and adjudication evidence.] No human decisions have been invented.

A separate prospective intake protocol locks the current models and thresholds before new collection. It records receipt/source/privacy evidence, screens against all available historical tables and archives, checks new-batch duplicates and requires human semantic-group review. Collection ends at the first 200 approved distinct groups or 30 days after the recorded freeze, whichever occurs first. New labels and cohort membership must be frozen before a single evaluation. [Insert recruitment channel, actual collection dates, screened counts and final cohort evidence.] Existing records are not designated fresh. Any later test-driven model changes require a new model version and future cohort.

Groupmates will use a shared fictional-probe phone-test guide and blank results form. [Insert actual phone models/Android versions, APK hashes, returned evidence and measurements.] Until those returns exist, physical-device checks remain pending.

Evidence: [frozen protocol](expanded-comparison-protocol-20261005.md), [completed report](four-model-comparison-20261005.md), [reproduction guide](expanded-comparison-reproduction-20261005.md), [annotation workflow](blinded-validation-workflow-20261006.md), [prospective plan](prospective-validation-plan-20261006.md), [phone guide](remote-phone-test-20261006.md).
