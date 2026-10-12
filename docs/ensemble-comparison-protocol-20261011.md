# Fixed-setting retrospective comparison — 11 October 2026

This additional experiment is authorized by the user's retraining and ensemble
request. Preserve the October 5 expanded experiment byte for byte. Use its 3,340
records, labels, four partitions, five training folds, preprocessing, dependency
versions and seeds. The primary metric remains smishing-class F1. Class 0 is ham;
class 1 is smishing. This is retrospective: the existing test was already opened,
and labels are inherited source/rule labels awaiting independent confirmation.
No new split can repair that history. Do not describe these results as prospective.

Baseline LR/NB/SVM: refit the already selected hyperparameters, without calling a
grid search. Preserve each saved validation-selected threshold. Fit the original
sigmoid on the original calibration partition, as required by the baseline
protocol. mBERT: preserve the original two-epoch training settings and validation-AP
checkpoint selection, calibration partition and saved threshold. No new threshold
search is allowed. Baseline calibrated pipelines remain separate from additional
ensemble components. No app assets or historical results are replaced.

Voting: enumerate every subset of size 2, 3 and 4 of LR, SVM, NB and mBERT. Use equal
weights and a fixed 0.5 decision threshold. LR/NB use native class probabilities;
mBERT uses softmax of its independently trained logits. Linear SVM uses one sigmoid
fitted on group-out-of-fold margins exclusively within the training partition.
Every margin's vocabulary and IDF are fitted without that margin's held-out fold.
The final SVM is the identical refitted baseline classifier, with this distinct
training-only ensemble calibrator. Validate class ordering, finiteness, range and
probability row sums. Invalid probabilities are an experiment failure, not a reason
to silently repair scores. If a component lacks a probability interface, equal
hard voting is supported with ties assigned to class 0 (ham), fixed in advance.
All currently implemented components supply checked probabilities. Soft ties also
go to class 0. Baseline comparison remains >= its preserved threshold.

Stacking: (LR,SVM,NB)->LR and (mBERT,SVM,NB)->LR, separately. Reuse the original
five group folds. Meta-training sees one positive-class probability per base, one
OOF row per training record, never validation, calibration or test predictions.
For SVM OOF probabilities, fit its sigmoid from a second level of five grouped
folds inside that outer training fold; fit every TF-IDF on its own fitting fold.
Save both fold levels and all fitted pipelines. Fixed historical hyperparameters
are prespecified inputs to this new experiment, not reselected in these folds;
OOF scores are not an unbiased estimate of historical hyperparameter selection.
Meta LR uses C=1, solver=lbfgs, max_iter=2000, random_state=20260929. No scaling,
weight search, threshold search or meta-parameter search. Its fixed threshold is
0.5, with equality assigned to ham.

mBERT stacking bases train for exactly the original two epochs, with no outer
validation checkpoint selection. Each fold derives its token-length cap only from
that fold's training texts. All other training settings stay fixed. This is a
declared stacking-specific fitting procedure. Full-training epoch-2 weights can
be reused from the baseline training trajectory; reuse the selected baseline
checkpoint only if that checkpoint is epoch 2. Preserve final-epoch weights even
if baseline validation selects epoch 1. Use no baseline calibration or threshold
inside stacking. Cached OOF components are shared between the two stacks.

Freeze all available configurations and model hashes, rank by validation F1,
then evaluate all frozen entries once on identical test IDs. Ties in selection
use lexicographic experiment ID (no preference for LR). Report standalone,
voting and stacking separately; distinguish validation-selected entries from
descriptive test leaders. Record unsupported/failed entries with reasons. Never
alter a model following test results.

Report accuracy, positive precision/recall/F1, macro-F1, TN/FP/FN/TP, and measured
training and inference seconds. Training is fixed refitting, excludes historical
search, includes required OOF work for stacks/calibration. Shared costs are counted
once per hypothetical configuration, not again per cache access. Inference is
sequential CPU batch time including each component's input transformation, excluding
model load; combine overhead is added. Report record count and milliseconds/record.
GPU training and CPU inference are different conditions. Timing is descriptive,
not a physical-device benchmark. Keep predictions, IDs, weights and source snapshots
private; publish code, protocol and aggregate results only. Save artifact hashes,
code snapshots, environment versions, all configurations and split identifiers.

Before fitting, audit hashes, partition/fold group separation and coverage,
normalized view consistency, label orientation, training vocabulary isolation,
nonnegative NB features and prior exposure. Diagnose LR with validation-only
native/calibrated metrics at its preserved threshold and fixed 0.5, without using
these diagnostics to change any configuration. A diagnostic threshold is not a
new eligible baseline or a tuning exercise.
