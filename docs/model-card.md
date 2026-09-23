# Supplied experimental model card

Version: SmishGuard 0.2.0-dev, converted schema 2. Intended use: authorized local manual paste/share software testing only. Research performance, calibration and automatic warning approval are unverified. Never describe the score as a fraud probability or guarantee.

Model: supplied binary logistic regression, raw term-frequency TF-IDF, L2 normalization, word unigrams/bigrams, sigmoid score. Tokenization uses frozen Python Unicode 15.0.0 behavior, preprocessing `python-unicode-word-v2`. Positive class is `smishing`; decision is strict score >0.5. Unknown terms are ignored; empty feature vectors use the intercept. Empty/blank and over-10,000 UTF-16-code-unit Android inputs fail. Safe probes check compatibility, not language accuracy.

Provenance: original model SHA-256 `3ec2fa27951588447fa59800bfb5de0e7d0b61526bb1ff1352358db755ce768a`; converted asset SHA-256 `9026c925679f9667b5bd09e34f31dd884cdb72607650d97f9a0708c86fa6bab2`. Training-data file SHA-256 `554df67a04b65425e81b7bd577f36b82ddaf48287f2a61677f940213fb66269b`. The guide says all 1,276 rows were used. Procedure scripts and seeds are now supplied in research/model_evidence; the original training environment, calibration evidence and prospective held-out evaluation of deployed weights remain unresolved. No retraining or parameter change was performed here.

Technical evidence: `model-conversion.json` records five rounded guide references (absolute tolerance 0.00005) and Python/sklearn safe-probe agreement. `SuppliedModelTest` checks fixed non-sensitive probes, tokens, feature indices/normalized values, scores (1e-10 tolerance), final decisions and fail-closed metadata. Both minimum API26 and project target API36 test records are linked from current verification. This is supplied-model compatibility on fixed probes, not real-message parity or predictive validation.

Limitations/risks: inherited labels, source bias, English-dominant sample, unknown acquisition lineage, full-data training, unsupported deployment generalization and two learned numeric identifier-like vocabulary terms requiring human privacy review. Model redistribution terms are unresolved. Keep model and APK private; public source does not include parameters. Automatic warnings and reporting remain disabled. Do not replace this model with a newly trained candidate until separate evaluation/export/parity review is complete.

Future independent evaluation uses `smishguard.supplied_evaluate` after intake review and a documented unseen cohort. It validates the frozen model/training hashes and refuses exact/near-template overlap. Heuristics and a user-entered evidence reference cannot prove true independence; researchers must establish it. No such real-data evaluation was run.

## Procedure evidence update

Training and evaluation procedure documented with reproducible scripts and supplied result tables; dataset-dependent reproduction was not independently rerun in this handoff.

Supplied final settings: C=2, L2 penalty, liblinear, class_weight=balanced, max_features=5000. Supplied dataset counts: 1,276 total, 1,054 ham, 222 smishing, consistent with prior aggregate records but not recounted here. LR comparison results: accuracy 0.9453, smishing precision 0.8163, recall 0.8889, F1 0.8511. Selection favored compact portable inference, not accuracy dominance.

Handoff-reported five-seed F1 default 0.8635, tuned 0.8664, improvement +0.0029 conflict with the retained CSV means 0.8610, 0.8643 and +0.0033. RF has the highest single-split smishing F1; the claim of highest CV variability is false in the supplied tables (Naive Bayes is highest). See [full discrepancy and methodology review](../research/model_evidence/MODEL_EVALUATION.md). Small tuning gains suggest near-optimal defaults, not a breakthrough. No 95.3% unseen-traffic claim is supported.

The private deployed model contains identifier-like numeric vocabulary terms inherited from training data. The model therefore remains excluded from the public repository. Future retraining should remove standalone numeric tokens of five or more digits and re-run parity and evaluation tests.
