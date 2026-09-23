# Model evaluation: supplied evidence and independent checks

Training and evaluation procedure documented with reproducible scripts and supplied result tables; dataset-dependent reproduction was not independently rerun in this handoff.

## Dataset and provenance

The handoff consistently reports 1,276 total rows: 1,054 ham and 222 smishing. This agrees with existing repository aggregate audit records, but the dataset was not opened or recounted in this run. Original labels, permitted use, source lineage and independent annotation remain research questions. Full-data final fitting is visible in train_final_lr.py; no split of those same rows can establish prospective performance of the deployed weights.

## Supplied single-split evidence

The Logistic Regression CSV row and handoff prose agree: accuracy 0.9453; smishing precision 0.8163, recall 0.8889 and F1 0.8511. This is the default comparison fit, not the final C=2 full-data model. None of these numbers describes unseen real-world traffic.

The three result CSVs are preserved without changing their numerical values. The following conflicts must be reconciled by the researchers before manuscript adoption:

| Quantity | Handoff prose claim | Independently calculated/read from supplied CSVs |
|---|---|---|
| Default LR five-seed mean smishing F1 | 0.8635 | 0.86101736 (0.8610) |
| Tuned LR five-seed mean smishing F1 | 0.8664 | 0.86434582 (0.8643) |
| Tuning gain | +0.0029 | +0.00332845 (+0.0033) |
| Default F1 sample SD | 0.0292 | 0.02446741 |
| Tuned F1 sample SD | 0.0309 | 0.02976577 |
| Random Forest accuracy | 0.9727 | 0.9688 |
| Random Forest smishing precision / F1 | 1.0000 / 0.9157 | 0.9744 / 0.9048 |
| Random Forest CV macro F1 mean / SD | 0.9141 / 0.0259 | 0.9124 / 0.0202 |

Both versions put Random Forest first for single-split smishing F1. The claim that it has the highest cross-validation variability is contradicted by BOTH versions: Naive Bayes has SD 0.0283, above RF's claimed 0.0259 and CSV 0.0202. RF variability does exceed LR's 0.0138. Do not present the inaccurate superlative as a finding. There is no statistical test establishing ranking stability.

The requested values 0.8635, 0.8664 and +0.0029 remain recorded only as handoff-reported claims, not independently confirmed results. Both sets suggest a small tuning difference; tuned F1 is worse on seed 42, identical on two seeds and better on two. Tuning confirmed near-optimal defaults within this limited comparison, not a performance breakthrough. LR's selection rationale is compact portable inference, not accuracy dominance or established calibration.

## Static methodological limitations

The outer 80/20 split fits TF-IDF on training only. However, comparative_analysis_v2.py and the tuning grid feed an already-vectorized matrix into cross-validation; vocabulary/IDF are not refitted within each CV fold. That creates preprocessing leakage into inner validation. A future corrected experiment must use a Pipeline fitted per fold and report fresh results separately. Do not retrospectively relabel these tables as leakage-free.

The grid is selected on seed-42 training rows, then reused across five overlapping random splits. Other seeds' test sets may overlap rows used in selection. This is not nested validation or five independent datasets. Bootstrap intervals use predictions from seed 42, not a confidence interval for the deployed artifact or all five seeds. Duplicate/template grouping is absent in the supplied scripts. Threshold/learning-curve tables have no corresponding executable script or per-seed predictions in this safe handoff. Original training environment is unknown; later reproduction and vocabulary-overlap claims are handoff-only.

## Handoff-only reproduction claims

The handoff reports 4,965/5,000 vocabulary terms shared with a later refit, with 35 tie-frequency differences and up to 0.0025 reference-score drift, attributed to library ordering. Neither the private vocabulary nor that refit was inspected or rerun here. These claims do not establish exact artifact reproduction or justify loosening the existing 0.00005/1e-10 compatibility tolerances.

## Reference compatibility

Five rounded reference scores match docs/model-conversion.json within its 0.00005 rounding tolerance: 0.9081, 0.4698, 0.7279, 0.1555, 0.8875. The largest previously recorded rounding deviation is below 0.000038. Comparing these saved numbers is independently possible without the messages. It is not a fresh inference rerun on those original messages. Existing SuppliedModelTest uses separate safe software probes and a 1e-10 tolerance. The handoff's ScorerVerificationTest/ModelLoader.kt names do not describe files in this checkout; see MODEL_INTEGRATION.md.

## Privacy

The private deployed model contains identifier-like numeric vocabulary terms inherited from training data. The values are intentionally omitted. The model remains excluded from the public repository, and future retraining should remove standalone numeric tokens of five or more digits.

Any future retraining must re-run parity and evaluation tests; its privacy/performance cost has not been established. No model weights, vocabulary, raw SMS or dataset rows are included here.

## Status

Procedure-level evidence: supplied and documented, with unresolved inconsistencies. Calibration: not established. Prospective unseen-data evaluation: pending. Automatic warnings: disabled/unapproved. Production readiness: not established. Android's evaluation_status=unverified remains unchanged because supplied procedure evidence does not validate the deployed artifact.
