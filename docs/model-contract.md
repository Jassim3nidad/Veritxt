# Versioned offline model contract

1 October: **schema v4** is the separate `lrCalibrated4` build's `lr-calibrated-4` contract. Calibration is folded into source coefficients/intercept; the runtime applies one sigmoid and rejects executable calibration fields. It retains strict **score >0.50**, `calibration_status=fitted_unvalidated`, experimental Model score wording, input abstention and disabled reporting/warnings. Source/model identities, matching-guide checks and review limitations are in the [LR4 review](lr-calibrated-4-review.md). The generic loader still rejects v4; only the explicitly selected build loads it. v2 historical and v3 separate-calibration models are unchanged.

29 September complete package: schema v3 adds an explicitly selected calibrated LR candidate path; [review and blocker](mark-complete-findings.md). It preserves the source vocabulary, IDF, coefficients, intercept, and separate sigmoid slope/offset with `score >= 0.40`. Its calibration status is `fitted_unvalidated`, output remains an experimental **Model score**, and empty/unassessable input abstains. The generic loader and historical v2 paths do not accept v3; only `lrCandidate` selects it. No source asset or APK is installed until the actual content review is documented. This does not change v2's strict >0.5 behavior below or deploy the earlier `lr-calibrated-2` artifact.

25 September candidate review: `lr-calibrated-2` is **under review, not deployed**. [Supplied aggregate evidence and methodology findings](../research/candidate_review/README.md) do not alter this contract, calibration metadata, threshold, reference scores or Android behavior.

## Three different statuses

| Status | Supplied model in this milestone |
|---|---|
| Technically integrated | Converted without retraining or changing vocabulary, IDF, coefficients or intercept; reference scores reproduced; Android parity/offline checks recorded in verification |
| Experimentally evaluated | Procedure-level scripts and result tables supplied; conflicts documented in [evidence review](../research/model_evidence/MODEL_EVALUATION.md). Deployed full-data artifact remains unverified on prospective data |
| Approved for user-facing automatic warnings | **No.** Detector policy denies automatic SMS inference; reporting also disabled |

`0.2.0-dev` / package `ph.smishguard.dev` is a distinct development build for manual paste/share checks. The ordinary debug build has no model asset. Missing, invalid and inference-failure paths remain available. Neither synthetic fixtures nor unverified supplied results can form report payloads.

## Supplied schema v2

The conversion command in [research README](../research/README.md) validates contiguous unique vocabulary indices, one IDF/coefficient per feature, finite values, positive IDF, intercept, class order `[ham, smishing]`, positive class, lowercase and `[1,2]` n-grams. It checks the five guide examples to 0.00005 absolute tolerance, appropriate to four-decimal rounding. Actual errors are below that bound; full values and source/converted hashes are in [model-conversion.json](model-conversion.json).

The deployed math is raw unigram/bigram counts times supplied IDF, L2 normalization, dot product plus intercept, then sigmoid. Classification is **strictly score > 0.5**, not >=. Unknown terms contribute zero; all-unknown nonempty input uses the intercept. Empty/blank and >10,000 UTF-16-unit inputs fail gracefully in Android. No URL normalization, placeholder substitution, accent stripping, stemming or URL fetch is inserted into this supplied model's tokenizer.

Python `str.lower()` and Unicode `\b\w+\b` differ from Android/JVM regex and Unicode versions. Conversion freezes Python 3.12 / Unicode 15.0.0 word-character ranges, full lowercase mappings, cased/case-ignorable ranges and Greek final-sigma context. Android uses these tables, including single letters, ñ, accents, digits, underscores and supplementary code points. Unknown tokens are retained while forming consecutive bigrams so they cannot incorrectly bridge known neighbors. The original training Python version was not supplied; compatibility is against the documented algorithm, five references and this pinned reference implementation, not an assertion that the later supplied scripts establish the original environment or exact artifact reproduction.

Schema v2 separates `provenance` (user-supplied source hash and claimed training rows), `technical_compatibility=reference_verified`, `evaluation_status=unverified`, `calibration_status=uncalibrated`, `intended_use=manual_development`, `automatic_warnings_approved=false` and `synthetic=false`. The parser validates these combinations rather than treating software compatibility as evaluation. This v2 contract intentionally does not accept an approval flag flipped to true. A future reviewed deployment policy needs explicit implementation and evidence.

UI calls the sigmoid output an **uncalibrated model score**, never a validated probability/percentage. The 0.5 threshold is provisional. Results state experimental/unverified status and do not label a message definitively fraudulent or legitimate. The receiver checks `automaticWarningsAllowed` before calling a detector; this model denies it. Reporting is unavailable and experimental results are rejected by the report factory.

## Older research schema v1

The existing calibrated word-unigram `sg-ascii-v1` pipeline remains separate: ASCII folding, URL/email/digit placeholders, raw TF-IDF/L2 and linear margin with optional separately fitted sigmoid calibration. Export defaults `calibration_evaluated=false`. Synthetic fixtures stay synthetic. This format is not silently reinterpreted as the supplied Unicode unigram/bigram model. Automatic warnings are also disabled by default for legacy detectors; a calibrated flag alone is not approval.

## Verification boundaries

Fifteen safe full-precision probes cover English/Taglish, single-character and Unicode tokenization, unknown tokens, empty/blank and long text. Python portable math is compared with scikit-learn; Android tolerance is `1e-10` (double arithmetic, much tighter than guide rounding). The five guide references are processed locally without following their URLs; no guide/dataset messages are included in parity assets. Actual results are in [verification](verification.md).

The supplied source export has 5,000 features; converted asset is under the existing 8 MB loader bound. Only the necessary model and Unicode metadata enter the development APK. Raw dataset and original guide remain in ignored private research storage. Learned feature tokens can retain training information; the audit identifies numeric-token candidates for review. No pasted/shared text is persisted or transmitted by the app.

No retraining, calibration-quality claim, warning-threshold approval, research winner or physical-device performance follows from parity. New research fitting uses approved data and the frozen split/selection workflow; the already-used supplied rows cannot become prospective validation by being reshuffled.

## Safe handoff evidence update

Training and evaluation procedure documented with reproducible scripts and supplied result tables; dataset-dependent reproduction was not independently rerun in this handoff.

The tuned script records C=2, L2, liblinear, balanced; default comparison fits use C=1. Evidence reports 1,276 rows (1,054 ham / 222 smishing), consistent with the earlier aggregate audit. Source keys coef/idf/vocabulary/classes/ngram_range/intercept are converted; runtime schema uses weights/bias and ordered vocabulary. ModelLoader is an object in SuppliedDetector.kt, not a separate ModelLoader.kt file. No private model or policy metadata was changed.

See the [evaluation discrepancy ledger](../research/model_evidence/MODEL_EVALUATION.md): LR single-split 0.9453 accuracy, 0.8163 precision, 0.8889 recall and 0.8511 F1 are supplied procedure results; handoff five-seed claims conflict with its CSVs. Neither establishes calibration, real-world accuracy, prospective validation or automatic-warning approval. The [two-tier caution proposal](../research/model_evidence/THRESHOLD_POLICY.md) is unimplemented and requires review/usability tests. Strict >0.5 remains unchanged.
