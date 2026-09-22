# Evidence based drafting materials for Chapters 3 to 5

These are drafting notes, not a final manuscript. Use past tense only for procedures backed by saved evidence. Replace `Pending evidence` only after checking the referenced artifact and its scope. Source manuscript objectives are mapped in `requirements-traceability-matrix.md`; do not adopt quoted literature performance as this project's result.

## Chapter 3 Methodology

**Research design.** The planned study compares financial-institution SMS impersonation classifiers while controlling duplicate leakage and simple lexical/URL clues. The current completed work is a software prototype and reproducibility preparation. Research model comparisons have not been conducted on an independently reviewed primary dataset.

**Dataset construction and inclusion.** A supplied package was preserved and audited by SHA-256. It contains 1,276 rows with inherited labels and language fields. Primary inclusion requires documented permitted use for the chosen activity, human redaction, financial scope and resolved independent judgments. UCI stays supplementary; nonfinancial scams remain separate; personal/social examples stay excluded from development while evidence is pending. Target 2,500/minimum 1,200 applies after eligibility review. Planned participant collection and on-device redaction form remain unfinished; ethics evidence must precede new collection under the manuscript.

**Cleaning and privacy.** Keep originals under ignored restricted local storage. Record hashes and anonymous IDs, not raw text, in review summaries. Redact uniformly using the labeling guide; preserve evidence separately from annotators. Exact and normalized duplicates plus label-blind near-copy connected components identify potential leakage. Human review is still required for residual identifiers, semantic equivalence and conflicting groups. Automatic grouping is a heuristic, not known campaign identity.

**Annotation.** Two annotators independently label reviewed blinded messages in four categories. Freeze original responses before adjudication. Report raw pairwise agreement, Cohen's kappa for two raters or Fleiss' kappa for equal cohorts of more raters, disagreements and final category counts. Undefined agreement is reported explicitly. Missing rows fail validation. Actual completed responses and agreement: **Pending evidence**.

**Model procedure.** The supplied development LR export is kept unchanged and was trained on the full supplied collection. It cannot establish held-out performance on those records. Prepared LR/NB/linear-SVM baselines fit vocabulary/IDF on training text only. Calibration has a separate partition, validation chooses thresholds and candidate, and sealed artifacts precede final evaluation. Default group policy uses deterministic stratified group folds where support allows, otherwise group shuffle, and rejects class-degenerate partitions without seed searching. Random and chronological comparisons explicitly disclose possible template leakage; time-group purges crossing components. Chronology needs genuine receipt timestamps, currently absent. calamanCy and the two transformer runs remain planned, with vetted checkpoints and a common protocol required.

**Experimental design.** Freeze seed, dataset hash, group membership, conditions, metrics and selection before final-test access. Compare word/character features, text-only/text-plus-URL facts and placeholder/shape/punctuation controls. Never infer unknown URL facts as zeros. Already used samples remain retrospective; independent supplied-model confirmation requires a genuinely unseen reviewed cohort and overlap checks.

**Metrics.** Report confusion TN/FP/FN/TP; accuracy=(TP+TN)/N; precision=TP/(TP+FP); recall=TP/(TP+FN); specificity=TN/(TN+FP); F1; FPR=FP/(FP+TN); FNR=FN/(FN+TP). Current implementation defines no-predicted-positive precision/F1 as zero and undefined class-dependent rates as null. ROC-AUC and trapezoidal PR-AUC require both classes; average precision is a separate metric. Use fixed-prediction cluster percentile bootstrap 95% intervals (1,000 replicates, recorded seed), report valid replicate counts, and disclose that model-selection/training uncertainty is not included. Brier/log loss/ECE/reliability bins assess calibration. Source/language subgroups below 20 rows or 5 per class report support only. These floors do not imply adequate statistical power. Base-rate projections at 0.1%, 1% and 5% remain hypothetical.

**Android implementation.** Kotlin/Compose Activity and transient ViewModel invoke a local validated detector. Frozen Python Unicode 15 normalization/tokenization and TF-IDF unigram/bigram math implement the supplied schema. Manual input clears after use/navigation/background/recreation. Preferences store settings, not scans. No INTERNET permission, reporting implementation or automatic-model warning approval exists. Safe fixed probes compare tokens, feature indices/values, scores and decisions with absolute tolerance 1e-10. Five original guide scores use rounding tolerance 0.00005. This is bounded technical compatibility, not accuracy evidence.

**Testing strategy and safeguards.** Python fixtures test intake, blinding, leakage and evaluation boundaries; JVM/instrumentation test runtime and flows; dedicated API26/36 emulators exercise offline and privacy cases. Report passes, failures and skips separately using the current verification record. No real messages are sent through test instrumentation. Xiaomi physical validation is pending official resolution of secure FRP. Emulator tests do not substitute for carrier, battery/vendor or human usability validation.

## Chapter 4 Results and Discussion template

| Section | Evidence that can be inserted | Still pending |
|---|---|---|
| Dataset characteristics | `dataset-audit.json`, `dataset-freeze-summary.json`: supplied counts, missingness, lengths, indicators and groups, identified as inherited/unverified | Eligible cohort and independently reviewed language/scope counts |
| Annotation agreement | No real agreement artifact available | Raw agreement, kappa/method, cohort/exclusions, disagreement/adjudication table |
| Model comparison | Pipeline fixture tests only; do not insert their scores | LR/NB/SVM/transformers, common conditions, selected candidate |
| Confusion matrix and metrics | No research results available | Saved final-test report, N, TN/FP/FN/TP, metrics and intervals |
| Calibration/threshold | Supplied model is uncalibrated, strict >0.5 provisional | Reliability analysis and justified warning policy |
| Error analysis | Anonymous export tooling exists | Reviewed error categories, subgroup support and redacted examples approved for publication |
| Android functional results | `verification-20260923.md`, linked test artifacts | Untested accessibility/lifecycle/vendor cases disclosed |
| Emulator results | API26/API36 saved JSON from the current source | APIs between endpoints and broader screen/device coverage |
| Physical-device results | User-reported installation restriction only | All checklist outcomes remain Pending |
| Literature comparison | Use Chapter 2's original papers after verification | Compare task, language, split/leakage, annotation and prevalence before comparing headline scores |

Discussion prompts: How many nominal rows survive eligibility? Does grouping reduce apparent performance? Do word models beat the weak controls? Does URL ablation affect false alarms on legitimate financial messages? Which languages have insufficient support? How much calibration changes threshold behavior? Answer only from saved results; absent results are **Pending evidence**.

## Chapter 5 Provisional outline

1. State the verified engineering finding: a supplied experimental model can be integrated for local manual inference, within the tested software scope.
2. Address O1–O5 individually. Dataset validity, model comparison, generalization, shortcut effects and calibrated warning effectiveness remain **Pending evidence**. Do not conclude real-world effectiveness.
3. State limitations: inherited labels, unresolved eligibility, full-dataset model fitting, English-dominant sample, unknown receipt dates, source/label confounding, heuristic groups, limited emulator coverage, unmeasured device latency/memory and absent physical installation.
4. Recommend independent labeling and unseen confirmation, more legitimate financial and Filipino/Taglish samples, approved transformer/calamanCy comparisons, wider accessibility/device testing and controlled client service completion.

## Threats to validity and reproducibility

Construct validity: category judgments cannot verify sender identity; keyword indicators are not truth. Internal validity: repeated templates, preprocessing/source clues and repeated final-test access can inflate results; freeze group splits and selection. External validity: curated language/source distributions and emulator endpoints cannot represent ordinary traffic or Xiaomi behavior. Statistical validity: correlated rows reduce effective sample size; cluster bootstrap does not remove sampling bias or training uncertainty. Ethical validity: authorization, permitted use, consent, redaction and redistribution are distinct statuses.

Public reproduction covers source/tests/templates; licensed private data and the supplied model require controlled access. Record Python/JDK/SDK versions, source commit, input hashes, split seed and manifest, feature contract and evaluation timestamp. See `reproducibility-guide.md`. App scans remain separate from research collection; the application does not upload scans. The OS clipboard, keyboard, default SMS app and private research storage have separate data lifecycles. These are scoped engineering statements, not a blanket legal-compliance certification.
