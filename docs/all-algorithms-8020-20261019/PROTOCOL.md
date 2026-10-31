# All-algorithm 80/20 extension — frozen before fresh fitting

User request: retrain every previously used algorithm, including combined models,
with 80% training and 20% testing. Reuse the exact eligible records, cleaning and
80/20 membership from `research/runs/holdout-8020-20261019/run-v1`.
That earlier comparison was already opened; this extension is retrospective.

Include all previous algorithm families: LR, Linear SVM, Multinomial NB, Random
Forest, KNN and mBERT. Include A–E word/word+character family-winning settings,
the latest five NB settings/SVM reference, legacy ensemble components, all eleven
equal-weight soft votes and the two previous LR meta stacks. A–E are reported in
raw/native and training-OOF sigmoid modes. No parameter search, label change,
favorable seed search, new exclusions or test-based model change is permitted.
XLM-R was never trained; INT8 mBERT is a quantization derivative.

All training fits and OOF/meta/calibration fits must exclude the 684 test rows.
Three group folds within the 2,734 training rows create OOF predictions. Every
fold fits its own vocabulary and classifier. Calibrated OOF predictions require
additional inner grouped folds within each outer fitting subset. Final models
refit all training records. For mBERT, independently fine-tune from the pinned
local base for two fixed epochs for the full training partition and each of its
three OOF folds. No checkpoint depends on outer/test labels. Save fitted fold
artifacts/membership for review. Preserve case for the native mBERT tokenizer.

Use fixed default thresholds: raw Linear SVM margin >=0; other standalone
scores >=0.5. Historical validation-tuned thresholds are not carried into the
different allocation. Soft votes/stacking use >0.5; ties are ham as in the earlier
ensemble protocol. Voting LR/NB/mBERT use native probabilities; SVM uses its
training-only sigmoid. Stacks train LR(C=1) on the same aligned OOF probability
columns. Do not report meta training resubstitution as held-out CV.

Seal source, input, splits, settings, all model/fold artifacts and ensemble
specifications before one exclusive test pass. Primary metric is smishing F1;
also report accuracy, precision, recall, macro F1, false-positive/negative rates,
confusion counts and available source/language support. Report test leaders as
descriptive, without selecting or installing a deployment winner. No statistically
independent prospective claim follows from the inherited historically exposed
labels, source concentration, uneven CV folds or only nine test components.

Keep populated models, text, vocabularies and row predictions in ignored private
run folders. Publish aggregate reports only. Preserve previous runs/app assets.
