# Candidate review — 25 September 2026

**`lr-calibrated-2` is under review, not deployed.** These are supplied candidate-procedure results, never performance of the currently shipped Android model. Only two aggregate CSVs were accepted from Mark's shareable ZIP. No private archive, dataset, model, source download or original private guide was opened. No fitting, model inference, export, conversion or APK build was performed.

## Provenance and disposition

Starting branch: `codex/thesis-completion-package`, clean at `a604e18eb2801bb557bbc54b500df965bb3c5750`; initial fetch confirmed zero ahead/behind. Mark's separate HANDOFF.md is byte-identical to the ZIP's handoff. Its instructions are proposals, not authorization to access private inputs or adopt a model.

[archive_review.json](archive_review.json) records all **28 files**, byte sizes, SHA-256 hashes, comparison against the starting repository, privacy-pattern counts and individual dispositions. Archive SHA-256: `a3d41169f4562a0d75bb787f430a9555c26139879452dd7655269485a6d302e0`. CRC, bounded sizes, paths, encryption, symlinks, text decoding and binary checks passed. Ten Python sources parse without execution. No credential-pattern match or fitted model export was found; the report includes fitted calibration parameters, which were not copied. These are bounded checks, not proof that arbitrary text is public.

| Supplied files | Decision |
|---|---|
| `training/calibration_metrics.csv`, `training/reliability.csv` | Accepted byte-for-byte here, as supplied aggregate evidence |
| All seven `backend/` files | Preserve existing backend. Five substantive differences; seed and ignore files differ only in line endings. Existing fixes include controlled-value/type validation, date/overflow handling, nonreflecting errors, Unicode authentication handling, separate demo totals, local fonts and pinned dependencies. Do not regress 45 tests to 37 |
| Three original training scripts, three original result CSVs, `lr_best_params.json` | Seven byte-identical duplicates; no copy |
| `training/MODEL_EVALUATION.md`, `THRESHOLD_POLICY.md`, `README.md` | Keep sanitized existing versions; record candidate findings here instead of overwriting them |
| `build_supplementary_ham.py` | Reviewed, excluded: private sources, automatic source-category labels and incomplete heuristic redaction; existing human intake workflow takes precedence |
| `train_calibrated_lr.py` | Reviewed, excluded: duplicate pipeline with private input/export side effects and unresolved methodology; existing `smishguard` workflow remains authoritative |
| `evaluate_fresh_messages.py` | Reviewed, excluded: loads model files and prints message excerpts; no safe independent inference without private weights |
| `run_training_demo.py`, `DEMO.md` | Reviewed, excluded: unsafe for this scope; see side effects below |
| `fresh_test_messages.csv`, `candidate_parity_cases.json` | Excluded: message-bearing files, each with one phone-shaped literal; publication eligibility unestablished. No literal/message copied or printed in the review |
| `calibration_report.md`, `HANDOFF.md` | Reviewed, not copied: replacement review separates claims, conflicting interpretations and research gates; report includes messages and fitted calibration parameters |

The builder's three mobile-pattern matches are its explicit dummy-number code/documentation, not evidence of three personal numbers. That does not make its outputs safe: regex masking cannot establish removal of names, URLs, alphanumeric identifiers or private context. The fresh CSV has 34 unique messages with group/label/message columns only; no authorship dates, label-review history, source permissions or preregistration. The parity JSON has 40 unique messages and finite scores, covering all 34 plus six phone-testing probes. Its code says it excludes guide references; this review did not open the private guide to establish that claim. Both files remain outside Git. Sanitizing their text would invalidate any claim that the supplied scores still apply.

## Independently verified

Verification here means inspection and arithmetic on shareable bytes, not refitting or scoring a model.

- Archive integrity, file comparison, ten script syntax checks and the absence of a candidate training unit-test suite in the ZIP.
- Exact schemas, 30 metric rows covering three protocol/variant pairs × five seeds × two score types; no missing/duplicate cells, finite/ranged metrics and consistent precision/recall/F1.
- Twenty reliability rows (ten bins per score type), valid scores/rates, integer implied scam counts, and equal pooled totals: **1,216 observations, 222 positive observations** per score type. These are repeated-split observations, not 1,216 independently sampled unique messages.
- Means and sample SDs in [aggregate_check.json](aggregate_check.json), recomputed without private inputs. Tests include malformed/missing cells, nonfinite values and arithmetic corruption.
- Supplied fresh labels versus saved parity scores at strict `> 0.5`: everyday chat 12/12; legitimate bank/service 8/8; bank-impersonation group 8/9; scams without links 3/3; outside-scope group 0/2; total **31/34**. This is consistency of two supplied files, not validation of their labels, freshness or inference. The everyday-chat scores span about 0.003–0.096.

## Internally consistent but not reproduced

| Supplied five-seed grouped means | Primary only, sigmoid calibrated | With everyday, sigmoid calibrated |
|---|---:|---:|
| Everyday false-alarm rate | 0.045296 | 0.005421 |
| Primary smishing F1 | 0.913243 | 0.898298 |
| Primary precision | 0.946716 | 0.940648 |
| Primary recall | 0.883333 | 0.860707 |
| Primary Brier score | 0.024768 | 0.028609 |

Within the with-everyday condition, raw versus sigmoid-calibrated Brier is 0.031889 versus 0.028609; log loss 0.139848 versus 0.102024; ECE 0.067986 versus 0.026201. These agree with the supplied report after rounding. Random-split calibrated F1 is 0.848513 versus grouped 0.898298. No raw predictions, fold membership or private labels were available to independently recompute those metrics.

The candidate report describes 1,276 primary rows plus 1,050 supplementary ham rows, 66 duplicate groups covering 155 rows, numeric-feature removal, deterministic fitting and exported-score parity. Those are supplied claims, not independently recounted/reproduced. The handoff's current-model everyday comparison and Python/Kotlin parity claims were not rerun. No candidate Kotlin test is in this ZIP.

## Method and conflicts

1. **Fold-local fitting is improved, but selection is not fully nested.** In `out_of_fold_scores`, each inner StratifiedGroupKFold fits vocabulary, IDF and LR on inner training rows only. `train` fits Platt scaling on those out-of-fold margins, then refits the base classifier on the outer training set. `evaluate` scores held-out outer rows. This is a defensible design for exploratory calibration evidence. However, `lr_best_params.json` comes from the old grid search, whose TF-IDF precedes inner CV and whose selection rows may occur in later test partitions. The new evaluation does not reselect parameters inside outer training folds or erase that history.
2. **Grouping has limits.** Similarity groups are built once using label-free TF-IDF on the entire corpus, including outer test text. That is a transductive grouping step, distinct from classifier feature fitting; disclose it. Cosine >=0.90 grouping does not prove all shared campaigns/templates/sources are isolated, and it is not source/time-held-out validation. Five repeated first-fold holdouts can overlap. Higher grouped scores do not prove absence of leakage. Neither the group manifests nor unique exposure counts were supplied.
3. **Calibration has supporting reported metrics, not established deployment quality.** Brier/log loss/ECE and reliability bins are more evidence than merely using a calibrator. They remain retrospective and unverified on raw outputs. Calibration is fitted to the mixed training distribution, while the reported calibration metrics cover primary rows only. Sparse bins, reused observations, old parameter selection and deployment base-rate differences limit inference. For example, the calibrated 0.1–0.2 bin reports mean score about 0.15 and observed scam fraction about 0.41 (n=32). Overall ECE can hide local error. Final full-data coefficients have no prospective holdout; out-of-fold calibration on refits does not validate the final artifact automatically.
4. **Threshold evaluation is exploratory.** Thresholds 0.30–0.50 are all measured on outer test predictions. No independent threshold-selection partition or frozen loss/utility rule is supplied. Choosing from that table consumes the test evidence; repeat evaluation on untouched data afterward. Per-seed threshold confusion counts/predictions are absent from the retained CSVs, so that report table cannot be independently reconstructed. The old policy names `lr-calibrated-1` and section 3, while the supplied report names `lr-calibrated-2` and puts thresholds in section 4. No caution band or threshold change is justified here.
5. **Report interpretations overreach.** A drop in F1/recall smaller than a seed SD does not establish equivalence or “not measurably affected.” The primary-only to augmented comparison loses about 0.015 F1 and 0.023 recall while improving everyday false alarms. Grouping cannot guarantee results “cannot be inflated” by repeated text. The earlier five-seed/RF prose conflicts remain as recorded in [the existing discrepancy ledger](../model_evidence/MODEL_EVALUATION.md); the duplicate CSVs have not resolved them.
6. **Freshness is unproven.** The 34-file is read for export probes and by the standalone evaluator, not directly by fitting, calibration or threshold code. That supports no direct programmatic training use, but cannot establish no human model selection/tuning after seeing results. Six separate everyday probes are explicitly motivated by phone-test failures. The handoff uses fresh results to recommend further retraining. Treat all exposed probes as development diagnostics, not a future independent test cohort. Labels are supplied by authors without documented independent adjudication; the SSS example is grouped as bank impersonation, illustrating unresolved scope taxonomy.
7. **Known misses must remain visible.** The handoff highlights an SSS ayuda scam (saved candidate score about 0.323) and a courier/parcel scam (about 0.466), both below 0.5. The saved table also misses a job-themed outside-scope example (about 0.017); the handoff's two highlights are not an exhaustive failure count. The claim that relevant scams are absent from training cannot be checked without private data. The proposed additional SSS/DSWD/parcel examples require source eligibility, redaction, independent human labels, leakage checks and a new evaluation plan before any inclusion. Nothing was added to training.
8. **Demo reproducibility is overstated.** `run_training_demo.py` invokes comparison, tuning, stability, full-data export, supplementary-data construction and candidate training. It reads private primary/supplementary/source files and a private guide; writes tables, fitted JSON/joblib, a guide and message-bearing parity outputs; and may read an app export using a layout that differs from this repository. Contrary to DEMO.md, the builder writes to `data/` outside `training/`. The demo's “MATCH” checks verdict agreement, not the required numeric tolerance, can accept an empty reference list, and returns success without enforcing all reference matches. It was never run. Later Python/sklearn claims and alphabetic tie-breaking do not pin the full environment or establish cross-version identical weights.

## Requires private-data work by researchers — prioritized adoption gates

All items below are **pending**, not authorized/completed by this review.

1. Confirm source permissions, acquisition lineage, task scope and redistribution rules; human-review redaction and vocabulary leakage, including alphanumeric identifiers. Have independent annotators label eligible primary/supplementary and proposed scam examples, adjudicate disagreements and retain uncertainty. Source categories and hand-written labels are not substitutes.
2. Freeze dataset/version hashes, group/source/time split manifests and a new evaluation protocol before seeing final outcomes. Fit feature selection/TF-IDF, parameter selection and calibration within the appropriate training folds. Freeze threshold selection on separate validation data with a documented safety cost policy. Preserve all exposure history.
3. Reproduce candidate fitting and aggregate metrics privately in a locked environment. Retain auditable out-of-sample predictions/confusion counts privately. Assess calibration using reliability curves, Brier/log loss/ECE, uncertainty, subgroup support and plausible prevalence shifts; do not infer calibration from a flag or sigmoid alone.
4. Reserve a prospective unseen cohort independently authored/collected and labeled after model/threshold freeze. Include eligible SSS/aid, courier, ordinary-chat, bank/OTP and job-scam scope cases. Do not recycle these 34 or six exposed probes as an independent final test. Evaluate errors, not just overall accuracy.
5. Only after approval, review candidate export/schema/privacy and Python 3.12/Unicode compatibility, then run independent Android parity with safe probes and separately reviewed references. Keep existing reference expectations until a separately approved adoption; no tolerance relaxation to hide drift.
6. Complete usability/safety review and physical-device testing. Xiaomi testing remains blocked by secure FRP; resolve via authorized owner/support channels or use an authorized working device. Automatic warning approval and backend/reporting readiness are separate gates.

The shipped model, `calibration_status=uncalibrated`, strict `> 0.5`, reference expectations and app UI are unchanged. No caution band, automatic warnings, networking or INTERNET permission was added. `DisabledReportingRepository` remains in use. No APK implies candidate adoption. API 36 fixes at the starting commit were preserved, not redone.

## Safe setup and verification

The new reviewer uses Python 3.12 standard library only, existing research structure and no additional dependencies. From repository root:

```powershell
python scripts/verify_candidate_handoff.py
$env:PYTHONPATH='research'
python -m smishguard.candidate_evidence
python -m unittest discover -s research/tests -p test_candidate_evidence.py -v
# Optional, only for the explicitly supplied shareable archive:
python scripts/verify_candidate_handoff.py --archive "$env:USERPROFILE\Downloads\smishguard_repo_update.zip"
```

The archive verifier requires the reviewed hash and membership, parses source without importing it, and never extracts files or displays messages. It refuses other archive names. Use the existing pinned research environment for the full suite; no private inputs are needed. [Verification record](../../docs/verification-candidate-review.md) records actual commands, counts and limitations. `.gitignore` and index checks protect candidate exports/raw probes in addition to existing exclusions; tracked files still require index review.
