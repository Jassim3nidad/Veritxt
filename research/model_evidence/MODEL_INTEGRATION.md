# Android model integration contract

This describes the existing integration; it does not supply or authorize replacement of the private model. Training count reported: 1,276 rows (1,054 ham / 222 smishing).

Final fitting script and lr_best_params.json agree on TF-IDF lowercase unigrams and bigrams, max_features=5000, token pattern `\b\w+\b`, L2-normalized raw term frequency times IDF; Logistic Regression C=2, penalty=l2, solver=liblinear, class_weight=balanced. The comparative/default scripts intentionally use default C=1 and default solver, not those final tuned settings.

Source exports require `coef`, `idf`, `vocabulary`, `classes`, `ngram_range`, `intercept`. They are inputs to research/smishguard/convert_supplied.py. This repository has no ModelLoader.kt: ModelLoader is in android/app/src/main/java/ph/smishguard/model/SuppliedDetector.kt and delegates schema-v2 parsing to SuppliedDetector. Conversion maps source coef/intercept to runtime weights/bias and converts indexed vocabulary to an ordered list, with frozen Unicode and policy metadata. Copying the raw JSON directly to Android is not supported.

Runtime math: lowercasing with frozen Python 3.12 / Unicode 15.0.0 tables, matching word tokenization, consecutive unigrams/bigrams, raw counts times IDF, L2 normalization, dot product plus intercept, numerically stable sigmoid. Unknown tokens remain in sequence while forming bigrams; unknown features contribute zero. Strict score >0.5 means equality is not suspicious. No threshold or UI behavior changes are included in this handoff.

The sigmoid is an uncalibrated model score, never a probability or guaranteed confidence. No 95.3% unseen-traffic accuracy claim is supported. Existing guide-score records use absolute tolerance 0.00005; separate safe Android probes use 1e-10. The handoff's suggested 0.01 tolerance and named ScorerVerificationTest are superseded by the actual repository checks. A difference must be investigated, not hidden by rewriting expected values.

Full-data deployed weights have no prospective held-out evaluation. Software parity confirms implementation compatibility only. Automatic warnings remain denied, experimental results cannot form report payloads, DisabledReportingRepository stays installed, and INTERNET permission is absent.
