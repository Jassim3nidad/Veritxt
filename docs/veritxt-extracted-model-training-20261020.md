# Model extracted from Veritxt-0.3.0-Updated.zip

The supplied ZIP contains one file, `Veritxt-0.3.0-Updated.apk`. Its `assets/model.json` is a binary supervised Linear SVM for **Ham / Smishing**, with 18,473 learned word features. The model was extracted without changing its bytes.

The latest local app build already integrates this exact model through the `oldSvm` variant. A fresh assembly, lint and JVM check of the current workspace succeeded. The delivery bundle is `deliverables/Veritxt-Extracted-Model-20261020/`, containing the current signed APK, extracted `model.json`, required raw-SMS adapter, this report and an identity audit. Open **VeriTxt · Ham/Smishing** after installing the APK. It uses package `ph.smishguard.svm.oldbinary` and a local debug signing key.

## How the training method was identified

The APK alone identifies the feature and scoring contract, but does not include the training data split or SVM hyperparameters. Those details were recovered from matching local training records, rather than inferred from the APK's filename.

The extracted model is byte-identical to the frozen export under `research/runs/bantaytext-20261013/validation-v2/parity/selected-model.json`. Its vocabulary, IDF, SVM weights, bias, calibration slope/offset and threshold also match the saved `notebook-run-v3/grouped/svm-C-10.0/pipeline.pkl` exactly. That pipeline's hash matches both the candidate freeze and validation snapshot. This establishes the connection between this particular APK model and the training procedure below.

| Artifact | SHA-256 |
|---|---|
| Original APK inside the supplied ZIP | `47c511970ac8dfb4ff09e4ea35bd5862c29af1e8faf902d4cdaa7b37dfe8997a` |
| Extracted model | `15cc0105b0e51e5342682ea36896c4436e515c39d165faf040476046b6b8059c` |
| Matching fitted training pipeline | `761e9e4de331b0229eaf337d14ce63a4ea3a1482563c2ff07ee0aa4a0a5947d6` |
| Raw-SMS adapter retained by the latest app | `11c3ee93fb7523e72b5658bec9f4bc5ee7389d9e5add25d5ca3fceceeedb5b8c` |

## Training procedure

1. **Prepare labeled SMS.** The recorded input contained 3,340 messages. Placeholder cleanup, whitespace normalization, deduplication and holding flagged rows left 2,554 messages: 2,229 Ham and 325 Smishing. The records report 727 duplicates removed and 59 flagged messages held. Original source/rule labels were retained.
2. **Group similar messages before splitting.** Label-blind template groups use supplied template identifiers, normalized-text equality and a similarity threshold of 0.85. `StratifiedGroupKFold(n_splits=10, shuffle=True, random_state=42)` allocates six folds to training, two to validation and two to test. The selected model came from the grouped track; a separate random-split comparison was also run.
3. **Learn word TF-IDF from training messages.** Lowercase Unicode word tokens of at least two code points; remove the 318 scikit-learn English stopwords before forming word unigrams and bigrams. Use raw term counts, smoothed IDF and L2 normalization. `min_df=1`, no feature cap, `sublinear_tf=False`. Vocabulary and IDF are learned on training data only. The final fit has 18,473 features.
4. **Fit a linear support-vector classifier.** `LinearSVC(C=10.0, penalty='l2', loss='squared_hinge', class_weight=None, dual='auto', max_iter=10000, random_state=42)`. The saved estimator also records `tol=0.0001` and a fitted intercept. The training code does not apply SMOTE or other class resampling in this path. `max_iter` is an optimization iteration limit, not a neural-network epoch count.
5. **Fit sigmoid calibration using training-only predictions.** Three stratified group folds generate out-of-fold SVM margins. Each fold learns its own vocabulary and IDF. `LogisticRegression(C=1, solver='lbfgs', random_state=42)` fits the sigmoid to those margins. The final TF-IDF/SVM is fitted on all 1,540 training records; validation and test records are excluded from this fit and the calibration fit.
6. **Select the candidate and operating threshold using validation.** Thresholds from 0.05 to 0.95 in 0.01 steps are evaluated. The criterion maximizes F1 subject to precision >=0.90 and at least five true positives; ties prefer recall, fewer false positives, then a larger threshold. Grouped validation chooses `svm-C-10.0` among feasible improved candidates, with ties resolved by smaller measured serialized size then candidate ID. Its threshold is approximately **0.37**, inclusive. The frozen candidate is then evaluated on the test partition without refitting on validation or test.

| Partition | Messages | Ham | Smishing |
|---|---:|---:|---:|
| Training | 1,540 | 1,345 | 195 |
| Validation | 516 | 459 | 57 |
| Test | 498 | 425 | 73 |

This is approximately **60/20/20**, with actual proportions determined by template-group sizes. The saved split reports zero template-group overlap between these partitions. The recorded libraries are Python 3.12 / Unicode 15.0.0, scikit-learn 1.6.1, NumPy 2.2.6, SciPy 1.15.3 and joblib 1.6.0.

## Scoring and integration

The model expects an already masked, case-preserving input view. The app's existing adapter prepares raw SMS as `clean(mask(clean(raw)))`, preserving the training behavior for identifiers and URLs. Use the included adapter with the native `SelectedSvmDetector`; the extracted JSON is not a TFLite or ONNX model.

After TF-IDF/L2, the SVM computes `margin = weights · features - 0.6095835823537551`. The fitted score is `sigmoid(6.038254124838936 * margin + 1.8278951208606713)`. A score >= the stored threshold `0.36999999999999994` maps to Smishing; otherwise it maps to Ham. The app can abstain on unassessable input. The UI's separate risk index is not this classifier score.

The model's calibration status remains `fitted_unvalidated` and the training labels remain independently unverified. The historical data had prior exposure, so this split does not establish prospective accuracy. Extracting and integrating this model does not improve its learned parameters.

## Verification

The current workspace passed `scripts/build_old_binary_svm.ps1`: app/test APK assembly, lint and JVM checks. The application signature verifies under APK Signature Scheme v2. The current APK and prior delivered APK are byte-identical, so the existing API36 emulator evidence applies to the same APK: 515 model fixtures, 33 raw-input fixtures and 20 Android tests passed. Maximum recorded Android model-score error was 4.44e-16. No new emulator or physical-phone run was performed in this extraction pass; no emulator was connected.

The final APK contains only the frozen model and raw-SMS adapter in its assets. The standalone model and the model embedded in that APK are byte-identical to the supplied APK's model. The bundle's `verification.json` and `SHA256SUMS.txt` record final identities and the current check results.

## Local source evidence

- [Training and candidate selection code](../research/smishguard/bantaytext_workflow.py)
- [Frozen export implementation](../research/smishguard/predeployment_validation.py)
- [Native scorer](../android/app/src/main/java/ph/smishguard/model/SelectedSvmScorer.kt)
- [Native raw-input detector](../android/app/src/main/java/ph/smishguard/model/SelectedSvmDetector.kt)
- [Existing APK integration and verification](old-binary-svm-20261020/RESTORATION.md)
- [Original SVM integration report](linear-svm-app-integration-20261013.md)

The fitted pipeline, partition manifests and message-bearing evidence remain in the existing ignored `research/runs/` storage. The delivery bundle includes the extracted inference assets, not the training messages or executable pickle.
