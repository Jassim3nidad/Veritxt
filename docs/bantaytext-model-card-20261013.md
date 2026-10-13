# BantayText experiment research candidate model card

Latest 13 October clarification: inherited labels are a documented research
limitation, not an added blanket requirement for another human-labeled upload.
The user reports physical-phone checks completed. [Raw-SMS validation](bantaytext-raw-sms-validation-20261013.md)
now replays the source preparation on all 2,554 records and checks a native raw-input
adapter without changing fitted parameters. The observed Tagalog-source transfer
failure remains the reason to avoid claiming general deployment readiness.

**Status: research candidate only; retain the existing active model.** Selection uses grouped validation, not test ranking. No automatic-warning, deployment, calibration-quality or physical-device approval follows from these experiments.

Additional [predeployment validation](bantaytext-predeployment-validation-20261013.md)
now verifies the actual frozen SVM's features/scores on JVM and an offline API36
emulator, using 498 private test views and 17 synthetic probes. A test-only native
contract exists; production loading and raw-SMS integration remain unchanged.
Stricter source-complement threshold/calibration testing still gives Tagalog-held-out
F1 0.3896. The supplied ZIP is identical to the previously used data and contains
no completed independent labels. Release remains unapproved.

Intended use: retrospective comparison of offline Philippine SMS phishing algorithms, toward future financial-institution scam detection. The available source/rule dataset includes courier, government, marketing and other broader phishing cases, so the metrics are not financial-only estimates.

Candidate: `svm-C-10.0`, LinearSVC C=10, class_weight=None, dual=auto, max_iter=10000, seed 42. Features are unrestricted Unicode word unigrams/bigrams with sklearn English stopwords, raw TF-IDF, smooth IDF and L2 normalization. `min_df=1`, `max_features=None`; Filipino/Taglish stopwords are not removed. Three training-derived stratified group folds each learn their own vectorizer and produce OOF margins. LogisticRegression C=1/lbfgs maps these margins through a sigmoid. This fitting establishes a score transform, not calibrated real-world risk.

Labels: 0=ham, 1=smishing. Inherited source/rule labels are independently unverified. The selected validation threshold is **score ≥0.37**, maximizing validation scam F1 subject to precision ≥.90 and at least five true positives. The cost trade-off favors reliable positive alerts while retaining scam recall; the criterion is provisional. It does not alter the app's current decision policy.

Data: the authorized masked fitting view initially contains 3,340 records. Hold 59 flagged rows and remove 727 masked casefold duplicates; retain 2,554 (2,229 ham/325 smishing). Group by supplied templates and normalized SequenceMatcher ≥.85 connected components. The grouped split has 1,540 train, 516 validation and 498 test records, with no detected component crossing. All messages were historically exposed; these tests are held out of this run's fitting/selection, but are not prospectively unseen.

Grouped validation F1: **0.9655**. Retrospective grouped test: precision **0.9459**, recall **0.9589**, F1 **0.9524**, AP **0.9853**, ROC AUC **0.9973**; TN/FP/FN/TP=**421/4/3/70**. FPR=.00941, FNR=.04110. Brier=.01567 and log loss=.06074 under inherited test labels; they do not establish traffic calibration. Standard grouped unigram SVM baseline F1=.8971. Random validation independently selects `svm-combined`; its different test set must not be treated as equivalent.

Known risks: source identity strongly predicts labels; source rules used content/sender/URL signals to create some binary labels. No complete human review or verified receipt chronology exists. Automated masking can merge otherwise different messages. Template grouping can miss campaigns or overmerge independent texts, and normalized ASCII grouping loses accent distinctions. There are only ten grouped-test Filipino/Taglish positives; its class-specific FNR is suppressed. Bank/e-wallet-specific legitimacy labels are unavailable. Original-source OTP/government/ads/notification FPR counts are descriptive inherited-label evaluations, not verified legitimacy rates.

Vocabulary coverage: the selected training vocabulary includes `po`/`na` but has no observed `paki`/`nyo`/`ninyo` features; stopword filtering does not remove them, but the available fitting view does not supply them. Held-out analyzed-feature coverage is 75.34% for English and 80.36% for Filipino/Taglish, counting word unigrams/bigrams. Coverage is not language accuracy. Character/combined experiments did not become the grouped validation choice.

Generalization warning: fixed post-selection source stress F1 is .8821 for bwandowando, .9371 for marketing and **.3509 for Tagalog**. Source fits exclude held-source template groups, but settings/threshold were chosen earlier using validation from all sources; these are diagnostic stress tests, not unbiased nested source-heldout estimates. This variability, historical exposure and label uncertainty prevent a defensible production-winner claim.

Deployment compatibility: the candidate's exact pipeline, ordered features, coefficients, calibration and threshold are stored privately in `research/runs/bantaytext-20261013/notebook-run-v3/grouped/svm-C-10.0/pipeline.pkl`. The existing Android comparator contract only supports its declared ASCII word-unigram feature path, so this candidate cannot be installed by copying the artifact. Unicode English-stopword bigram inference requires a separately reviewed native contract and parity tests. No architecture change was justified without adequate deployment evidence.

An actually fitted `lr-portable` comparator was exported and verified solely to test the existing word-unigram Android contract. It is not the selected SVM, does not validate that SVM's compatibility, and is not installed. Active-model parity uses unchanged supplied weights and safe synthetic probes. Neither yields a real-message accuracy guarantee.

Artifacts remain private because learned vocabulary may retain training information. Public [JSON](bantaytext-comparison-20261013.json) records hashes, complete measured metrics, resource costs and configuration; [notebook](../research/SmishGuard_Model_Training_and_Evaluation.ipynb) records executable code and actual aggregate outputs. Host timings and sparse feature storage are measured separately from phone inference: no physical-device benchmark is available. The active supplied model, consent/permission behavior, reporting controls and offline architecture remain unchanged.
