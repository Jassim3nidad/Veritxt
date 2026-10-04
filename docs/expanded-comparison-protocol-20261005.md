# Expanded SMS phishing development protocol — 5 October 2026

Frozen before training or test predictions. This is a separate experiment from the
1,068-record comparison; its files, splits, scores and APKs remain preserved.

The supplied package reports adviser direction to cover all SMS phishing. This is
a supplied scope statement, not independently verified adviser approval. Positives
are deceptive attempts to obtain credentials, money or personal information through
impersonation or false rewards. Negatives are purported genuine messages. The
package excludes advertising and job/loan fraud; excluded messages with phishing
signals are flagged for scope adjudication and never silently admitted as ham.

The user authorizes preliminary training with source/rule-derived labels. No field
such as high confidence, manually verified or needs_review=false establishes an
independent human decision. Preserve the original package and pending review fields.
Use direct cleaned matches to the existing hash-pinned source copies and recorded
source-use evidence. ZERO CC0 and Chua CC BY support local development; BwandoWando
CC BY-NC-SA is restricted to this noncommercial local research experiment, with
attribution and no public data, weights or APK redistribution. Hold unresolved
GitHub and team records. Matching does not prove original acquisition or consent.

Package IDs are version-specific. Keep private original/cleaned/redacted content
fingerprints and the original metadata; publish only aggregate file fingerprints.
Source cleaning removes the package's named masking placeholders and whitespace.
Automated minimization applies the established case-preserving URL/email/digit
placeholders to every algorithm, and holds likely names, addresses, obfuscated
links and conflicting normalized labels. Human privacy review remains pending.
Only redacted message text is a prediction feature. Baselines then use sg-ascii-v1;
mBERT keeps case. Review/source/sender/ID/date/category/language fields are audit only.

Audit supplied template keys; merge identical normalized views and near copies
using label-blind connected components at SequenceMatcher ratio >=0.85, plus all
supplied template links. Use the existing deterministic split policy with seed
20260929, approximately 55/15/15/15 train/validation/calibration/test. Require each
evaluation/calibration partition to have >=20 positives and >=10 positive-bearing
groups before training. If it fails, record a development-only grouped CV amendment
before model fitting; do not search split seeds. Exact and near-copy exposure to all
four previous partitions and earlier supplied training corpora is retrospective
evidence, never a claim that unmatched messages are independently unseen.

LR, Multinomial NB, Linear SVM use existing five-fold grouped training-only AP
selection over C/alpha={0.1,1,10}; fit fresh TF-IDF inside each fold. Refit only on
training. Fit a separate sigmoid once on calibration. Select threshold on validation
F1 over 0.05..0.95 in 0.01 increments, breaking ties toward higher thresholds.

mBERT is google-bert/bert-base-multilingual-cased revision
3f076fdb1ab68d5b2880cb87a0886f315b8146f8 with matching cased tokenizer and a new
binary head; all parameters trainable. Reuse the pinned dependency lock. Seed
20261005, two epochs, Adafactor 2e-5, weight decay .01, microbatch 1, accumulation 8,
gradient checkpointing, deterministic CUDA, float16 training autocast. RTX 3050
Laptop 4 GiB; at most 45 minutes of training. Training p95 lengths rounded to 16,
minimum 64, maximum 256. Report truncation at 128 and selected length. A 256-token
cap is practical with checkpointing/microbatch 1; OOM recovery may lower to 128 only
before a successful training step, recording the failure. Save resumable optimizer,
scaler, RNG and model state each epoch and every 200 training records. Select epoch
by validation AP only; then calibration and validation threshold as above.

Freeze every pipeline before the single final test opening. Report identical-ID
paired predictions privately, metrics including macro-F1, accuracy, confusion,
FPR, Brier, log loss, reliability bins/plots, 2,000 group-bootstrap intervals and
paired F1 differences. Descriptive subgroup metrics require >=20 records and >=5
of each class; otherwise support only. Intervals condition on fitted models and
imperfect groups; no simultaneous testing or fitting uncertainty is included.
App abstention coverage is separate from classifier metrics.

No test-driven retuning, predetermined winner or improvement claim from comparison
with the older scope. Export float32 mBERT faithfully; quantization requires a new
version. Verify actual Python/JVM/Android parity and all four offline variants on
one emulator, with cold loading separate from warm scans. Keep the minimalist UI,
Model score wording, privacy controls, disabled reporting/automatic warnings and
absence of INTERNET permission. Preserve rollback artifacts before asset staging.

Public output: code/tests, aggregate findings, file hashes, attribution and
reproduction instructions. Private: all IDs, messages, review worksheets, membership,
weights, predictions, test fixtures and APKs. No raw-build reproduction is claimed
unless all original raw inputs are present and verified. Do not execute the supplied
builder's hard-coded paths; a separate configurable adapter is required for that.
