# Complete-package integration review — 29 September 2026

The unchanged calibrated LR adapter and isolated `lrCandidate` build are prepared. **No candidate APK was produced:** four distinct phone-number-shaped tokens occur in 13 learned features, without evidence resolving their sensitivity. Nine features also contain masked identifiers; 45 contain long digit sequences (overlapping categories, not all personal data). This is an actual model-content packaging blocker, separate from pending research validation. No vocabulary/weight edits, review acceptance, contact permission, automatic warnings, networking or reporting were introduced. Historical LR assets/APKs and the minimalist UI remain intact.

## Integrated source

- `smishguard.complete_handoff`: private dataset/model/schema audit, independent scikit-learn arithmetic, split exposure reconstruction, rounded summary checks, and schema-v3 conversion preserving vocabulary, IDF, coefficients, intercept, calibration slope and offset. Only a hash-pinned, inspected reference scorer is executed; the notebook is never executed.
- Explicit candidate scoring path: frozen Python Unicode 15 tables, raw unigram/bigram TF-IDF/L2, `sigmoid(a*z+b)`, and **score >= 0.40**. Existing v2 remains **score > 0.50**. Calibration is marked fitted but unvalidated; UI retains “Model score” and its experimental disclaimer. Empty, meaningless, link-only and all-unknown input keep abstention; oversize input is rejected rather than silently truncated.
- `ph.smishguard.lr.candidate` / “SmishGuard · LR Candidate” can coexist with historical `ph.smishguard.lr` and `ph.smishguard.dev`. The build requires a real content-review reference bound to converted and source hashes. No review file was created for this model, and no model was installed in candidate assets.
- Existing comparison tooling now requires an ID-complete exposure ledger and rejects exposed/unknown prospective test records. It retains shared group splits, vocabulary fitting inside training folds, tuning within training, separate calibration and threshold partitions, frozen final artifacts and paired cluster uncertainty. Reports now include full pipeline bytes in addition to portable JSON bytes and explicitly describe marginal paired intervals.
- Backend: compatible response headers (local-resource CSP, no-store, no-referrer, nosniff, frame denial), tested on pages and errors. Existing payload validation, invented-demo separation, database and local-only operation remain. The supplied dataset-derived seeder, incompatible flagged-URL schema, raw-message/model-term routes, external fonts and contact downgrade were not imported.

## Supplied versus independently verified

The original Downloads archive is unchanged. An identical copy and path/link/size-checked extraction are under ignored `research/data/mark-complete-20260929/`. ZIP SHA-256: `9660c7e6cc2087399f8306ec4f68ec3397ceb00ef73bc07656fc12adbe096b14`. No archive code was executed during extraction. All real-message fixtures, score outputs, reconstructed roles and vocabulary findings remain there.

| Evidence | Outcome |
|---|---|
| Dataset claim: 2,521 rows, 2,270 ham / 251 smishing | Verified from both byte-identical CSV copies; unique IDs, expected five-column schema, no blank text/invalid labels |
| Three identical LR exports | Verified SHA-256 `d6a15d8d2b3c72c2ee1604654c1a526684c1cdae9c4d3bb63f09f7f42e9b3dbe`; 292,377 bytes including vectorizer |
| Schema/numeric/preprocessing | Verified 5,000 unique contiguous feature indices, equal vector lengths, finite values, positive IDF, lowercase unigrams/bigrams and L2 normalization |
| Positive class | Notebook explicitly sign-orients coefficients to smishing; reference and 9 rounded fixtures agree. Source JSON omits classes; original fitted estimator is absent, so training origin cannot be independently certified |
| Training on 2,016 rows | Supplied metadata; consistent with reconstructed train+validation sizes, not independent reproduction of fitting |
| Python/Kotlin parity claim | Independently verified supplied Kotlin and adapter against scikit-learn on all 2,521 private records plus 20 probes. Maximum errors: reference 3.33e-16, supplied JVM 3.33e-16, adapter JVM 4.44e-16; tolerance 1e-10. All 9 supplied rounded fixtures agree within 0.001 |
| Cross-platform claim | JVM parity verified; historical model and candidate software-policy fixture tested on API 36. The real candidate was not packaged or tested on Android. Supplied Kotlin depends on platform Unicode/lowercasing and truncates text; corpus agreement is not proof for every Unicode string/API. Adapter uses existing frozen tables |
| Source/annotation/redaction evidence | New source/category attributions and notebook procedure exist. No source-download/license records, independent annotator responses, adjudication, redaction sign-offs or completed training-history manifests supplied |
| Training history | Notebook has zero saved outputs and zero execution counts. Run info states sklearn 1.6.1; complete environment, selected per-run hyperparameters, row-level split/prediction logs, calibration tables and fitted NB/SVM artifacts are absent |

The new corpus has 742 exact stripped-text matches to the earlier supplied corpus. Existing review packets/IDs and statuses were not overwritten. Source strings attribute 1,446 rows to Tagalog-SMS, 972 to PH Spam + Marketing SMS, 90 to Philippine Spam/Scam SMS, and 13 to social/personal sources. Attribution is not permission or financial-scope eligibility. The new private exposure ledger conservatively records this supplied/evaluated corpus as exposed; it does not fabricate human review decisions.

[Machine-readable aggregate audit](mark-complete-audit.json) contains hashes, recalculated statistics and private-test aggregate outcomes. Parity demonstrates inference compatibility, not research accuracy, reliable real-world probabilities or approval for automatic warnings.

## Comparison findings and corrections

All five summary rows reproduce from supplied per-seed CSVs, including sample standard deviations, error totals, rounded timing and classifier-only sizes:

| Algorithm | Mean phishing F1 | Across-seed sample SD | Missed / false alarms, summed |
|---|---:|---:|---:|
| Linear SVM | 91.776% | 3.703 percentage points | 17 / 25 |
| Logistic Regression | 91.025% | 3.026 percentage points | 17 / 29 |
| K-nearest neighbors | 90.187% | 1.288 percentage points | 29 / 19 |
| Multinomial NB | 87.437% | 2.739 percentage points | 47 / 11 |
| Random Forest | 81.007% | 4.501 percentage points | 73 / 9 |

**SVM has the higher supplied mean phishing F1. LR is not established as the winner, and the difference is not statistically established.** These are arithmetic checks of supplied results, not reproduced training/evaluation. Error totals count repeated predictions, not unique incidents.

1. **Repeated-split exposure:** reconstruction using the supplied seeds and pinned sklearn finds 2,087 records changing roles. Of 505 first-seed test records, 504 occur in other runs' development sets, including 169 in their validation sets. The modal LR C and pooled threshold selection therefore depend on runs that expose the designated final test. These records cannot become unseen through reshuffling. The new corpus is not fed into research training.
2. **Uncertainty:** the notebook resamples pooled repeated predictions as independent observations, omitting repeated-record/template dependence and paired algorithm differences. Per-record prediction logs are absent, so its CI endpoints cannot be independently reconstructed. Across-seed SD does not repair this. The corrected workflow evaluates common frozen models once, resampling common template groups jointly for paired F1 differences; insufficient group/class support suppresses intervals. Intervals remain conditional on fitted models and do not establish population generalization or simultaneous multi-comparison significance.
3. **Different evaluated artifact:** comparison rows precede final LR refitting, OOF calibration and threshold changes. They do not evaluate the delivered calibrated 0.40 LR. OOF calibration uses stratified record folds, without template isolation, and threshold selection reuses the labels used to fit the calibrator. The corrected workflow separates calibration and threshold selection and evaluates each final calibrated/thresholded model on the same final partition.
4. **Template overlap:** exact notebook normalization removes zero rows. Existing broader label-blind grouping finds 1,884 groups, 245 multi-record groups and a largest group of 66. This automated sensitivity result requires human group review; it is not a completed grouping decision or exact proof of semantic duplication.
5. **Size and timing:** table sizes pickle only the classifier and omit TF-IDF vocabulary/IDF. The supplied LR JSON is 292,377 bytes; the faithful Unicode-table adapter is 437,027 bytes. Python per-message timings include host vectorization/prediction and are not Android latency. Current historical-emulator timing is separately identified in its verification record, never attributed to the candidate.
6. **Missing algorithms:** only LR was exported. Existing NB/SVM variants, own-model identity guards, exact linear exports and synthetic Python/JVM/Android parity remain available. Current workflow uses the declared ASCII-unigram feature contract; Mark's notebook uses Unicode unigrams/bigrams. These are different experiments. Do not silently drop bigrams or label an LR artifact as NB/SVM. Any alternate feature contract must be frozen and faithfully exported before the final comparison.

See [protocol v1.1](algorithm-comparison-protocol.md) and [data review commands](comparison-data-review.md). No previously exposed record, permission status, independent label, calibration validation or unseen-test designation was upgraded by this integration.

## Candidate delivery and verification

Candidate model version: `mark-lr-20260929-0351`. Private adapter: `research/data/mark-complete-20260929/parity/model.json`; SHA-256 `e31d9c0cd950e05eee3ac84372176ab906344516570e04be34302839782015b3`. This is a model file, **not an APK checksum**. Intended app identity: `ph.smishguard.lr.candidate`.

Actual attempted `:app:assembleLrCandidate` stops at `:app:verifyLrCandidateModel`: “LR candidate blocked: model-content review and private assets required; unresolved identifiers must be reviewed.” No candidate APK exists, so candidate APK asset identity, permissions, signature, checksum, installation/coexistence and real-model Android latency are **not verified**. No synthetic substitute was delivered as the candidate.

Rollback remains at `deliverables/algorithm-comparison-20260929/SmishGuard-lr-supplied-lr-0.2.0-historical-experimental-debug.apk`; historical development/LR model SHA-256 remains `9026c925679f9667b5bd09e34f31dd884cdb72607650d97f9a0708c86fa6bab2`. Existing deliverable hashes were recorded privately and checked for preservation.

Software checks and actual limitations are recorded in [verification results](mark-complete-verification.json) and [historical API 36 checks](mark-complete-historical-emulator.json). Research tests use software fixtures only. The private parity suite has 2,541 cases, with 2,533 scored and 8 abstentions in the adapter policy. Two of three ordinary Taglish software probes cross the candidate threshold; this behavior is preserved and reported, not patched with special-case predictions. It remains a known model-quality problem, without estimating a real-world false-positive rate from three probes.

## Exactly what the team must supply next

1. **Candidate content:** review the private `parity/content-findings.json`, identify whether the four phone-shaped tokens and other identifier features refer to people or are documented synthetic/public service identifiers, and provide a reviewer/evidence record covering the entire vocabulary, bound to the source model hash. If sensitive identifiers remain, provide a separately redacted and legitimately retrained/reviewed export; do not edit fitted vocabulary or weights in place. Research eligibility gaps alone are not an experimental APK blocker.
2. **Dataset eligibility:** source-specific row mapping/download references and permitted-use basis for the intended research operation; donation consent where applicable; completed redaction review, language/financial-scope decisions, two independent annotation responses, independence evidence and adjudication of disagreements. Reuse existing matching-record review IDs; coordinate unmatched records separately. The current 2,521 labels are supplied labels, not independent truth.
3. **Study protocol/history:** approve the controlling sample-size/financial-scope interpretation already tracked in the project; supply the completed training-history template with exact dataset/code/environment hashes, prior probe use, tuning/calibration/test memberships, dates and seeds. Preserve known exposure. For prospective claims, collect/reserve new independently documented records and review their template separation before any development use.
4. **NB/SVM:** either provide their actual fitted full pipelines privately (vocabulary/order, IDF, NB class log-priors and both class feature log-probabilities, or SVM coefficients/intercept, class orientation, preprocessing, calibration slope/offset, threshold, version/environment and source hashes), or complete the reviews needed to train them with the existing comparison workflow. Provide safe full-precision parity probes and frozen split/model manifests. Missing exports are not available models.
5. **Defensible comparison:** one reviewed group manifest common to all algorithms, ID-complete exposure ledger with actual references, development-only tuning/calibration/thresholding, all final artifacts frozen before opening a common final set, private per-record predictions/group IDs for paired uncertainty, abstention coverage, complete model sizes, and separately measured Android/device latency. Supply original per-seed prediction/selection logs to audit the old claims; new fitting cannot retroactively make the old test unseen.

## Reproduction

After reviewing the archive, keep its extraction in ignored private storage. From the repository root:

```powershell
$env:PYTHONPATH='research'
research/.venv/Scripts/python.exe -m smishguard.complete_handoff research/data/mark-complete-20260929/extracted/SMISHGUARD research/data/mark-complete-20260929/parity docs/mark-complete-audit.json
research/.venv/Scripts/python.exe scripts/verify_research.py
research/.venv/Scripts/python.exe scripts/verify_safe_handoff.py
backend/.venv/Scripts/python.exe -m unittest discover -s backend -p test_backend.py
.\scripts\build.ps1 -Variant lr
```

Private candidate JVM checks use `-PcandidateParityDir=<absolute private parity directory>` with `:app:testLrUnitTest` or `:app:testDebugUnitTest`. The independent supplied-scorer harness and its copied sources are private JVM-only inputs, never APK assets. The converted model and per-record cases remain private. The source hash guard prevents executing a changed reference scorer without a new inspection.

After actual content review, place only the converted model and truthful `review.properties` in `android/app/src/lrCandidate/assets/`. Required properties: `algorithm=lr`, `modelVersion`, `sourceSha256`, converted `sha256`, `contentReview=documented`, and the real `contentReviewReference`. Build with `scripts/build.ps1 -Variant lrCandidate`; then complete candidate-specific APK and emulator verification before delivery. No sample accepted review is supplied.
