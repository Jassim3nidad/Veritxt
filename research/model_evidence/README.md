# Sanitized model procedure evidence

Training and evaluation procedure documented with reproducible scripts and supplied result tables; dataset-dependent reproduction was not independently rerun in this handoff.

This directory is a sanitized derivative of `smishguard_model_evidence.zip`, not a dataset or a replacement model. Original ZIP bytes were not modified. The private training ZIP was not accessed. Scripts and aggregate tables are retained for review; do not execute training in this public checkout. The scripts expect an excluded private CSV at `../data/smishguard_dataset.csv` and write fitted model artifacts that are ignored. Their presence does not authorize data access, training, model replacement or deployment.

Sanitization removes identifier-like vocabulary literals, full guide-reference SMS examples and a literal model intercept from documentation. The final training script's embedded SMS verification section was removed; fitting/export code is otherwise preserved. Documentation was rewritten to correct inaccurate claims, with discrepancies recorded in MODEL_EVALUATION.md. No reference SMS text or model parameters are needed to review the aggregate evidence.

| File | Supplied procedure |
|---|---|
| comparative_analysis_v2.py | Five classifiers, stratified 80/20 split, seed 42; CV on pre-vectorized training data; also exports an SVM, not the deployed LR |
| lr_tuned.py | Grid search, then five stratified random splits; writes tuned table and parameter JSON |
| lr_5seed_bootstrap.py | Default LR across five splits; bootstrap on seed 42 only |
| train_final_lr.py | Fits tuned LR on all supplied rows; private export, not held-out evaluation |
| Three CSVs | Supplied aggregate results, preserved without numerical edits |
| lr_best_params.json | C=2, L2, liblinear, balanced |

The handoff reports Python 3.14.3 and scikit-learn 1.8.0 as a later reproduction environment, not the original training environment. pandas/numpy/joblib and complete package versions are not locked by the handoff. Existing research dependencies are a separate pinned environment. Syntax and table arithmetic checks do not establish data-dependent reproducibility.

Logistic Regression was selected for compact, portable on-device inference, not because it won accuracy or because its score was calibrated. Default-vs-tuned differences are small; tuning suggests the default was already near-optimal within these supplied comparisons, not a meaningful breakthrough. Do not change expected parity values merely to make changed model weights pass.

See MODEL_EVALUATION.md for conflicts, MODEL_INTEGRATION.md for actual Android schema conversion, and THRESHOLD_POLICY.md for the unimplemented proposal.
