# Team scope clarification and title status

Revised thesis title: **Pending finalization**. Preserve the existing title in the original manuscripts as historical. No replacement title is proposed or adopted; title-dependent edits remain pending. This does not block engineering, methods, validation or results documentation.

On 6 October 2026 the team clarified the research scope as **all SMS phishing**. This records the team's instruction, not adviser approval. Earlier references to an adviser-directed expansion are unverified package descriptions and must not be used as approval evidence. Financial-only definitions and blanket job/loan exclusions in older records describe historical experiments, not current eligibility.

Current working research questions:

1. How do the four frozen LR, NB, SVM and mBERT classifiers compare in detecting SMS phishing across financial and nonfinancial themes on the same independently labeled cohort?
2. What agreement and disagreements arise when two blinded reviewers apply the all-SMS-phishing definition, and how does documented adjudication affect a separately versioned dataset?
3. How do historical exposure, template overlap, language/source support and app abstention limit interpretation of retrospective and prospective performance?
4. What accuracy, model-size, inference-speed and Android-compatibility differences arise from a separate quantized mBERT deployment using the same fitted reference model?

Corresponding working objectives are to validate independent labels; screen and freeze a new cohort; compare the four unchanged pipelines and disclose uncertainty/coverage; and assess quantization separately with preserved original assets. Actual phone checks address installation, crashes, loading and layout only when groupmates return device evidence. These scope-aligned questions and objectives are working documentation, not a claim of final manuscript or adviser approval.

Methods and discussion must use the [current labeling guide](sms-labeling-guide-20261006.md), [review completion workflow](review-completion-20261006.md) and [prospective plan](prospective-validation-plan-20261006.md). Phishing mechanisms determine positives; sector, brand and link presence do not determine eligibility. Genuine financial and nonfinancial SMS are negatives. Pure nonphishing spam/scam, uncertainty and privacy/source holds are separately counted, never silently converted to negatives. Historical sampling exclusions remain disclosed as limits on coverage.

The four evaluation models, exact serialized thresholds and historical reports remain frozen. Quantization is a fifth, experimental deployment condition; it cannot replace the float32 mBERT member of the four-model comparison. Reporting and automatic warnings remain disabled. Synthetic fixtures validate software, not human judgments or real-world accuracy.

Older financial-only import/training tools remain available for reproducing historical artifacts. Use the versioned review-completion path for current all-SMS-phishing annotation and evaluation; do not force new data through legacy financial-only fields or retrain the frozen models. Retain original source documents and past results as historical evidence, with current guidance taking precedence for new work.
