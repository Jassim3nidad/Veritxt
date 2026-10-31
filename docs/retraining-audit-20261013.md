# Retraining audit, recorded before implementation

This work preserves the existing uncommitted Android integration and every prior
dataset, notebook, report, model and APK. New fitted outputs go in a fresh ignored
`research/runs/retraining-20261013/` directory. No production pointer is changed.

## Findings from repository inspection

- Existing code covers LR, NB, SVM, mBERT, ensembles, source-transfer checks,
  private review workflows and Kotlin offline scorers. The established notebook is
  `research/SmishGuard_Model_Training_and_Evaluation.ipynb`; preserve it and add the
  requested `research/Model_Training_and_Evaluation.ipynb`.
- The October 13 baseline notebook corpus has 2,554 messages: 2,229 ham and 325
  inherited smishing labels. Its original input has 3,340 records; the recorded
  cleaning held 59 flagged records and removed 727 duplicate masked texts.
- The baseline uses approximate 60/20/20 grouped partitions and three-fold
  training-only OOF sigmoid calibration for SVM. Validation selects settings and
  thresholds. Word features may remove English stopwords. Combined word/char
  features are research-only in the existing runtime.
- The installed experimental candidate uses word unigrams/bigrams, English
  stopwords, SVM C=10 and a fitted sigmoid, threshold >=0.37. Its prior 498-record
  test has TN/FP/FN/TP=421/4/3/70, precision 94.59%, recall 95.89%, F1 95.24%.
  These are saved historical results; a replay will be recorded separately.
- Prior model selection and many reports have already exposed the entire corpus.
  Repartitioning it cannot create an untouched evaluation cohort. Every new result
  on this corpus must remain retrospective, including any locked holdout evaluation.
- Source prevalence varies sharply: bwandowando contains positives only. A source
  string, URL, urgency, or broad spam category is not phishing ground truth.
  Label-lineage consistency checks are present, but independent labels are pending.
- Metadata has English and combined Filipino/Taglish, not independently verified
  Tagalog and Taglish. Categories are inherited; banking/OTP/conversation subgroups
  cannot be assigned ground truth from keywords. Receipt timestamps and reliable
  sender/conversation identities are unavailable. Template grouping is heuristic.
- Existing redaction replaces URLs, emails and numbers with markers. New fitting
  must describe this as a masked input view, not original unmodified SMS. Existing
  raw-SMS adapter parity checks this transformation. Preserve original private
  bytes and labels; do not restore identifiers or publish texts/vocabularies.
- `docs/source-evidence.md` records source versions, hashes and historical terms:
  Tagalog-SMS CC0, Chua marketing CC BY 4.0, bwandowando CC BY-NC-SA 4.0. Acquisition,
  privacy and labeling boundaries remain separate. No blanket redistribution or
  thesis authorization is inferred. Personal/social and unresolved rows remain held.
- Kotlin consumes validated JSON coefficients/IDF/vocabulary/Unicode tables, not
  a scikit-learn pickle. The current scorer supports word features only and exposes
  an experimental score with `probability=false`. Automatic incoming warnings are
  an existing team choice. Preserve that app behavior and its honest score wording.
- Python 3.12.5/Unicode 15 is installed. The research environment has sklearn,
  matplotlib and notebook tools; PyTorch/Transformers and an XLM-R cache are absent.
  Prior mBERT evidence is not an XLM-R experiment.

## Proposed changes and affected files

Add `research/smishguard/retraining.py` and associated tests: strict CSV/JSON/ZIP
input, lossless audit trail, label conflicts held for review, exact/near grouping,
70/15/15 grouped splitting with fail-closed feasibility checks, A–E tuning,
raw/calibrated diagnostics, validation-only operating policy, sealed evaluation,
subgroup/robustness/shortcut diagnostics, artifact metadata and plots. Reuse the
existing grouping and Unicode utilities with explicit contracts.

Add a separate native candidate scorer and JVM/instrumentation parity tests for
word/character TF-IDF. Keep it disconnected from production selection. Add notebook
generation/execution tooling, requirements, public aggregate reports and private
versioned artifacts. Update the research README to point to this dated work.

Provisional research operating policy: validation precision >=90%, FPR <=2%, at
least five detected positives; maximize recall, then F1, average precision, then
smaller artifact. This is a transparent experimental policy, not an approved
real-traffic service requirement. If infeasible, do not appoint a deployment winner.
Compare original distribution before balanced weighting. No resampling or SMOTE.

Calibration follows training-only grouped OOF predictions with fold-local
vectorizers and a final training-only refit. Its possible score shift and limited
positive support require reliability diagnostics and independent confirmation.

## Research basis

[scikit-learn calibration documentation](https://scikit-learn.org/stable/modules/calibration.html)
requires separation between classifier fitting and calibrator fitting.
[Version-matched TF-IDF documentation](https://scikit-learn.org/1.6/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html)
defines word and padded within-word character analyzers. Neither implies an
automatic benefit on this corpus. [The XLM-R paper](https://arxiv.org/abs/1911.02116)
and [checkpoint card](https://huggingface.co/FacebookAI/xlm-roberta-base) establish
the multilingual model's provenance; they provide no SmishGuard detection result.
The checkpoint card lists MIT. No checkpoint was downloaded or trained here.
