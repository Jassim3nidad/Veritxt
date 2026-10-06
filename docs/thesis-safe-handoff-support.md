# Proposed manuscript support: Chapters 3, 4 and 5

Revised thesis title: **Pending finalization**. The original manuscript title remains historical; title-dependent edits are pending. Current scope is **all SMS phishing**, clarified by the team without assuming adviser approval. See [current scope and working questions/objectives](scope-clarification-20261006.md).

Current workflow: [review completion and frozen evaluation](review-completion-20261006.md). Earlier milestone descriptions below are historical; their financial-only constraints and pending-model status do not govern current all-SMS-phishing work. Use the dated Chapter 3/4 drafts for current four-model evidence.

25 September supplement: [candidate evidence review and adoption checklist](../research/candidate_review/README.md), with [independent software verification](verification-candidate-review.md). The candidate remains under review, not deployed. Supplied grouped results report everyday false alarms falling from about 4.5% to 0.5%, alongside primary scam recall falling from about 0.883 to 0.861. No equivalence claim follows from seed variation. Saved fresh-case scores miss SSS ayuda, courier/parcel and a job-themed outside-scope example; fresh labels/independence remain unverified. These are candidate-procedure claims and arithmetic, not shipped-model or prospective performance. Independent labels, permissions, leakage-controlled selection/calibration, unseen evaluation, Android parity and usability/safety remain pending. Reporting stays disabled; physical Xiaomi testing stays blocked by secure FRP.

Separate drafting material; no approved Chapters 1 or 2 were edited.

## Chapter 3 methodology

The application implements offline manual paste/share scanning with an experimental Logistic Regression detector. The supplied training procedure uses lowercase word unigrams/bigrams, token pattern `\b\w+\b`, TF-IDF with max_features=5000 and L2 normalization, then LR with C=2, L2 penalty, liblinear and balanced class weights. The handoff reports 1,276 rows: 1,054 ham and 222 smishing. Counts agree with prior aggregate audit records, but private data were not re-opened or independently recounted.

Training and evaluation procedure documented with reproducible scripts and supplied result tables; dataset-dependent reproduction was not independently rerun in this handoff.

The single-split comparison uses seed 42 and a stratified 80/20 split; repeated-split tables use seeds 42, 7, 123, 2024 and 99. Inner CV uses pre-vectorized data, creating a preprocessing-leakage limitation. Reused tuning across overlapping splits is not nested validation. Final export fits all rows, so the shipped weights have no prospective held-out evaluation. Later reported Python/scikit-learn versions do not prove the original artifact's environment. State these limitations, rather than describing an ideal Pipeline as already executed.

## Chapter 4 results evidence summary

Supplied default LR single-split accuracy is 0.9453, smishing precision 0.8163, recall 0.8889 and F1 0.8511. These are procedure-level results. The handoff prose claims five-seed means of 0.8635/default and 0.8664/tuned (+0.0029), but arithmetic on its CSVs yields 0.8610 and 0.8643 (+0.0033). Mark final five-seed manuscript values **pending run-provenance reconciliation**. Preserve both sources; do not fabricate agreement.

Random Forest has the highest single-split smishing F1 in both sources, although its reported values differ. Naive Bayes, not RF, has the largest CV SD. LR was selected for compact portable inference, not maximum accuracy. Tuning suggests near-optimal defaults within this comparison, not a meaningful breakthrough. No 95.3% accuracy claim applies to unseen traffic.

Software testing results belong in a separate table sourced from verification-safe-handoff.md. Include passes, failures, skips and blocked tests explicitly. Backend tests use invented metadata; Android parity probes are software fixtures, not a performance benchmark or physical-device SMS test.

## Chapter 5 limitations and future work

Calibration is not established. Prospective unseen-data evaluation, independently reviewed labels/rights/source lineage, leakage-controlled model comparison, uncertainty analysis, usability and acceptance remain pending. The two-tier >0.35 to <=0.50 caution band is only a proposal: scores are uncalibrated, roughly equal legitimate/smishing cases enter the reported band, and legitimate OTPs are affected. Human approval and usability testing must precede implementation; automatic warnings remain unapproved.

The backend is a local readiness prototype; reporting is disabled in Android and every deployment gate remains pending. Voluntary report counts cannot establish unique victims or citywide prevalence. The private model retains identifier-like numeric features; future retraining must remove standalone numeric tokens of five or more digits and repeat evaluation/parity review. Neither data nor weights are public.

Physical Xiaomi installation remains blocked by secure FRP. Physical SMS delivery, offline latency/battery behavior on the intended phone and vendor-specific operation remain pending. Emulator success cannot substitute for those results. Obtain an authorized working test device or official support resolution; no security bypass is proposed.
