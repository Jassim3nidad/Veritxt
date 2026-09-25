# Compact manual results and retraining readiness

## What caused 33.6%

Synthetic random letters, keyboard mashing and unknown-word probes tokenize but
match zero unigram/bigram features. With a zero TF-IDF vector, the LR margin equals
the intercept. Applying the unchanged sigmoid yields 33.6317%, displayed as 33.6%.
This is not evidence that random letters are legitimate SMS. Aggregate reproduction
is in `compact-result-score-diagnosis.json`; no learned terms or messages are exported.

## Narrow abstention policy

Before production inference, tokenize text outside explicit URLs, www links and
dotted host-like strings. Require at least one model-known alphabetic word with at
least two letters. Four-or-more repeated identical letters and contiguous sequences
of four-or-more letters from a QWERTY row (forward/reverse) cannot supply that evidence.
Blank, numeric-only, link-only, entirely unknown and those keyboard-only inputs
return `UnableToAssess`, a separate type with no score, not a synthetic zero.

There is no minimum word count, known-word fraction or minimum TF-IDF magnitude.
One usable known word suffices even alongside mostly unknown tokens/links/numbers.
Accepted inputs retain their original features, raw score and strict >0.5 decision.
`rawDetection` is internal and only bypasses abstention for mathematical parity tests;
the application uses `detect`. Unknown-token parity remains checked rather than
silently removing such probes from the reference suite.

This is model-coverage abstention, not semantic understanding or a complete gibberish
detector. A random string accidentally matching a usable learned word may pass.
A meaningful unseen word may abstain. In particular this asset recognizes the short
English greeting used in tests but has no feature for two tested common short English
and Tagalog replies. An initial test incorrectly assumed all such replies were known;
that expectation failed and was corrected to explicitly test honest abstention for
zero-evidence meaningful input. No dictionary exceptions were added to disguise the
intercept-only output. The explanation in the app states this limitation.

## Retraining was not performed

Inspected the existing data card, freeze summary, authorization record, research
README, candidate review and `train.py`, `compare.py`, `evaluate.py`. Local metadata
checks found zero `approved.csv` datasets and zero saved training `splits.json`
files. All 1,276 entries in the existing redaction-review packet remain `pending`.
See `compact-result-training-readiness.json`. Project development is authorized;
reviewed dataset eligibility, independent labels and a defensible split are not
established. Neither PRIVATE ZIP was opened. No dataset fitting, label fabrication,
candidate adoption or calibration claim was made.

The existing pipeline already fits preprocessing on training rows, separates
training/validation/calibration/final-test partitions, selects on validation, seals
the selection and evaluates the final partition separately. Duplicating it or
running inherited unreviewed labels through it would not resolve data eligibility.

## Candidate work once reviewed inputs exist

1. Complete permitted-use, redaction and independent financial-scope labels with
   adjudication. Collect legitimate short replies, OTP/transaction notices and
   English/Tagalog/Taglish hard negatives, alongside diverse verified phishing and
   link-free scams. Do not label generated nonsense as ham; treat it as an abstention
   diagnostic set without phishing labels.
2. Freeze source/template groups and train/validation/calibration/test partitions
   before selection. Keep all preprocessing and feature selection fold-local.
   Use chronology only with verified timestamps. Already-used supplied rows remain
   retrospective, even after reshuffling; reserve genuinely unseen messages for
   prospective evaluation. Do not search seeds for flattering scores.
3. Compare the existing word baseline with character n-grams/subword coverage under
   a predeclared experiment matrix. Character features can help spelling variation
   but can also give nonsense nonzero vectors; evaluate abstention coverage and
   false rejection separately by language, length, OTP and link/number-heavy groups.
4. Choose the model on validation only; assess sigmoid calibration using held-out
   calibration data and report held-out Brier/log loss, reliability bins, ECE and
   subgroup support. Classifier confidence cannot by itself establish meaningful input.
   Freeze thresholds separately; the shipped strict >0.5 rule remains unchanged.
5. Report recall/missed scams, false alarms, precision/PR-AUC, uncertainty and
   group-held-out results, including rejection rates and errors among accepted
   messages. Lower everyday scores alone do not justify adoption. Mark's supplied
   candidate improves everyday false alarms but its review records lower primary
   recall and missed SSS/courier/job examples. Address these with new independently
   reviewed examples; do not optimize and then validate on the same 34 handwritten
   exposed messages. Those remain development diagnostics.
6. Require untouched-message testing, calibration assessment, export consistency,
   Android score/feature/decision parity and a separate adoption review. A character
   candidate also needs a compatible Android tokenizer/export implementation. Keep
   private artifacts local and retain the currently shipped model until all gates pass.

## Interface and privacy

The manual screen keeps the message field, Check button and inline result together.
Successful production results show the requested decision, actual score at one
decimal place, and experimental disclaimer. A 48 dp explanation control opens a
scrollable accessible dialog with limitations and safety advice. Results use heading
and polite live-region semantics. Input is still cleared after scanning and on
background/navigation/recreation; editing clears stale results. Missing and invalid
models both show `Model not installed`, with distinct explanatory text. Synthetic
injected fixtures remain explicitly labeled instead of being presented as assessments.

Reporting and automatic warnings remain disabled. No internet permission, backend
connection, model changes or threshold changes were introduced.
