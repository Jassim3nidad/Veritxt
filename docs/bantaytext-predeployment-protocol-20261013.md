# Additional predeployment validation protocol

Frozen before additional predictions. The final research candidate remains the saved
`notebook-run-v3/grouped/svm-C-10.0/pipeline.pkl`, threshold score >=0.37. No test-driven
hyperparameter, threshold, vocabulary or calibration change is permitted. The active
model and all previous experiment evidence remain unchanged.

The supplied Downloads October 12 ZIP has SHA-256
`38d00a999306ff11b05a431d9488f167589bd94e701f410edb24e8202bf3b3e6`, identical to the
previously audited package. It contains no completed independent labels. Reuse can
support retrospective stress tests, not prospective deployment validation.

Additional analysis, seed 20261013:

1. Verify the user-supplied ZIP and each member against the original intake hashes;
   inventory actual review completion and prospective intake without treating blank
   cells as decisions. Preserve existing fitted parameters and splits by hash.
2. Compute 2,000 paired whole-template bootstrap draws of fixed grouped-test
   predictions versus the original standard SVM baseline. Report confidence intervals
   conditional on fitted models/inherited labels; do not infer prospective validity,
   fitting uncertainty or correction for model selection.
3. For each source, hold out that source and every overlapping template group. Use
   five stratified group folds in the remaining source complement: first fold is inner
   validation, other four inner training. Train-only three-fold grouped OOF calibration
   applies to SVM. Fixed NB alpha=.1, LR C=10 and SVM C=10 use word unigrams/bigrams and
   English stopwords. Choose each operating threshold only on source-complement
   validation with the previously declared precision>=.90/TP>=5 criterion. Freeze fits
   and threshold before outer-source prediction. NB/LR use native scores. These fixed
   settings were historically selected using this corpus, so even nested operating
   points remain retrospective; do not claim unbiased algorithm-selection evidence.
4. Describe fixed-candidate test score calibration with reliability bins, Brier,
   log loss and ECE, and targeted original-source OTP/government/ads/notification
   false-positive counts with Wilson intervals. No bank/e-wallet-specific truth is
   inferred from broad notification categories. No score is approved as fraud risk.
5. Run prespecified casing, whitespace, punctuation, URL-placeholder removal,
   inserted Taglish wording and bank-term obfuscation stress transformations of fixed
   grouped-test inputs. Count decision changes and finite scores. Only case and
   whitespace tokenization parity have mathematical invariance expectations; other
   changed decisions are diagnostics, not automatically misclassifications.
6. Export the actual selected frozen SVM into a test-only native scorer contract.
   Preserve its Unicode-15 lowercase/word rules, >=2-codepoint token length, exact
   English stopword set, unknown-token adjacency, word(1,2), ordered vocabulary,
   raw TF-IDF/IDF/L2, coefficients, one sigmoid, class mapping and inclusive threshold.
   Compare scores/features on all 498 private grouped-test views and safe synthetic
   inputs in Python, JVM and an offline API36 emulator. This contract expects the
   already masked case-preserving training view. Raw SMS masking compatibility is
   tested separately; no production loader or app policy is changed. Synthetic OTP,
   bank, e-wallet and malicious-style cases are software probes, not accuracy labels.
7. Measure test-only emulator load/inference latency and memory proxies, validate
   empty/OOD abstention, reject invalid metadata/numbers, and rerun available privacy,
   permission, offline and Android build checks. Emulator values are not physical-phone
   benchmarks. No real SMS is transmitted or used for emulator receiver tests.

Deployment stays blocked unless a genuinely unseen cohort has documented source-use,
privacy review, independent A/B labels and adjudication, and was frozen before model
prediction. Existing retrospective blinded packets have no completed decisions;
software may validate returned evidence but must never invent human signatures,
reviewer identities or ground truth. A candidate-specific new prospective freeze is
created for future evidence without rewriting the older four-model freeze.

Engineering parity cannot compensate for weak source transfer or unverified labels.
No candidate is installed into production by this validation run.
