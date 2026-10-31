# Veritxt System Overview and Project Modules

Prepared for the team's Project Task Log. Updated: 14 October 2026.

## Overall current system status

**Overall project status: In Progress — functional experimental Android prototype, with model training and software verification completed for documented builds; independent research validation and final acceptance remain pending.**

Veritxt already supports offline manual SMS checking, Android text sharing, detection results, privacy consent, settings, English/Filipino interface text, and permission-based incoming-SMS checks. The selected-SVM build can issue experimental warnings with consent and the required permissions. A development-signed **Veritxt 0.3.0 Linear SVM APK** has been built and packaged for testing. Reporting is disabled and the backend analytics dashboard remains a disconnected local prototype.

| Area | Current status | Evidence / remaining work |
|---|---|---|
| Core Android application | Implemented and software-tested | Manual checks, share/paste, result display, session clearing, consent, settings, bilingual UI, and help are present. Final team acceptance is separate. |
| Integrated detection model | Implemented and software-verified | The delivered selected-SVM APK uses the frozen word-based Linear SVM with its matching raw-SMS adapter. Reference-to-Android score checks passed. |
| Incoming SMS and warnings | Implemented; experimental and permission-dependent | The selected-SVM emulator tests exercised actual model-based SMS alerts, multipart messages, and notification permission states. Availability on a phone also depends on Android and device restrictions. |
| Model training and comparison | Completed for documented retrospective experiments | LR, NB, SVM, and mBERT experiments exist. Additional LR/NB/SVM retraining and source-based improvement experiments were completed on 13 October. Their results do not establish future-message accuracy. |
| New research candidates | Trained; separate from the delivered app model | A newer word/character SVM was selected in the source-based experiment; it still needs its own app integration and parity verification. A separate retraining experiment selected NB under a different protocol. These results must retain their experiment identities. |
| APK packaging and software checks | Completed for the documented selected-SVM delivery | The 13 October record reports successful build/lint, 32 JVM tests with 4 conditional skips, 29 specialized API36 tests, 9 additional recovery/privacy/bilingual tests, and 2 final UI tests. The packaged APK is present locally. These are existing records, not new tests run for this overview. |
| Physical-device acceptance | Prior phone checks reported; latest-build acceptance pending | Earlier user-reported phone checks are recorded. No new physical-phone measurement for the selected-SVM delivery is documented in its integration report. Record installation, permissions, layout, loading, and performance against the exact APK tested. |
| Independent research validation | Pending | Independent label review/adjudication and a genuinely new evaluation cohort remain outstanding in the latest research records. Inherited labels and historical exposure limit the current accuracy claims. |
| Reporting and backend dashboard | Disabled / local prototype | App submission is unavailable. The standalone backend is disconnected and its historical payload contract requires reconciliation before integration. |
| Final release and project acceptance | Pending | The current APK is development-signed. Final team acceptance, retained reporting scope, production release arrangements, and final thesis review remain separate completion work. |

### Remaining work for the task log

1. Record physical-device checks for the exact delivered APK, including offline checks, incoming SMS, notifications, denied permissions, layout, and loading.
2. Complete independent label review and adjudication, then evaluate a genuinely new cohort under the documented protocol.
3. If the team adopts a newer research candidate, complete its model-specific Android integration and reference/JVM/device parity checks before replacing the app model.
4. Confirm whether reporting and the backend dashboard remain in the final scope; if retained, reconcile their contracts and complete integration and acceptance testing.
5. Complete final usability/accessibility acceptance, thesis updates, and the release/handoff work retained by the team.

### Summary your leader can copy

> Veritxt is currently a functional experimental Android prototype. Its main app features and the integrated Linear SVM model have passed documented software and emulator checks, and a testing APK is available. Model training and retrospective comparisons have been completed, while independent label validation, fresh-data evaluation, and acceptance testing of the latest APK on physical devices remain pending. Reporting is disabled and the backend dashboard is a standalone prototype. Overall project status: In Progress.

## Module count for the task log

**Use 13 main modules, including Model Training and Evaluation.**

This is a suggested project-management grouping of the current app and research workflow, not a count of source files or screens. Use the exact module names below in the spreadsheet's **Module** column. A module can appear on several task rows.

Two additional modules exist as disabled or standalone prototypes: **Reporting** and **Backend Analytics Dashboard**. If the leader includes these in the project scope, the task log will contain **15 module categories**. Record their prototype status; they are not working end-to-end services.

The four training algorithms belong under one training module. They can have separate task rows without increasing the module count.

## System overview

**Veritxt** is an experimental Android application for checking SMS messages for possible phishing. The current team scope covers financial and nonfinancial SMS phishing. Users can type or paste a message, share text from another app, or enable incoming-SMS checks with consent and Android permissions.

Message analysis runs offline using a model packaged with the selected app build. The interface displays a classification and an experimental model score, or explains when the message cannot be assessed. The score is not a guarantee that a message is safe or fraudulent.

Training and evaluation run separately on a development computer; the phone performs inference rather than training. The project contains Logistic Regression, Multinomial Naive Bayes, Linear SVM, and multilingual BERT experiments and app variants. The documented `selectedSvm` build integrates the earlier frozen word-based Linear SVM. Newer research candidates are separate experiments and are not automatically installed into that APK.

## Main modules

Availability describes the current code and documented work. It is not an assertion that every task has passed final team acceptance or physical-device validation.

| ID | Module name for the task log | Purpose and tasks / features | Current availability |
|---|---|---|---|
| M01 | Onboarding and Privacy Consent | Introduce the app, explain local processing and limitations, present the privacy notice, and record acceptance. | Implemented in the app. |
| M02 | Home Dashboard | Show model and scanning status; provide navigation and quick actions for checking messages. | Implemented; this is the phone's home screen. |
| M03 | Manual SMS Checking | Type or paste one message; clear input; handle empty or long input; start an offline check. | Implemented. |
| M04 | SMS Sharing | Accept plain text through Android Share and open it in the checking flow. | Implemented. |
| M05 | Message Preprocessing | Apply the active model's text preparation, tokenization and feature extraction; handle unsupported input and model input limits. | Implemented with model-specific pipelines. |
| M06 | Phishing Detection | Load and validate model assets; perform offline inference; apply the saved decision rule; handle unavailable or invalid models. | Implemented; the available model depends on the build. |
| M07 | Detection Results | Display the classification, model score, explanation, and temporary checked-message preview; allow another check. | Implemented; results remain experimental. |
| M08 | Incoming SMS Monitoring | Receive new SMS with scanning consent and permission; combine multipart messages; route eligible messages for checking. | Implemented; availability depends on Android/device permissions and the build. |
| M09 | Warning Notifications | Show a private alert when an eligible model flags a new SMS; show a check prompt when automatic verdicts are unavailable; support opening the check from a notification. | Experimental automatic warnings are enabled in the development and selected-SVM builds; comparison variants remain manual-only. |
| M10 | Settings and Permissions | Enable or disable incoming checks; manage SMS/notification permission flows; show permission status; test notifications; reset local preferences. | Implemented. |
| M11 | Language and Accessibility | Provide English/Filipino interface text, language selection, reduced transparency, readable layouts, and accessible controls. | Implemented features; broader accessibility acceptance remains a testing task. |
| M12 | Help and Troubleshooting | Explain scanning behavior and limitations; provide guidance for permission, notification, and device setup issues. | Implemented. |
| M13 | Model Training and Evaluation | Prepare and split data; train and compare models; select operating thresholds; evaluate errors; export candidates and verify Android prediction parity. | Research tools and retrospective experiments exist; independent validation remains separate work. |

## Training tasks to add to the spreadsheet

For every row below, enter **Model Training and Evaluation** in the Module column.

| Task / feature | Description |
|---|---|
| Dataset preparation | Check source provenance, privacy/redaction, labels, duplicates, and eligibility; record unresolved cases. |
| Dataset splitting | Freeze experiment-specific training, calibration, validation, and test partitions; check template overlap and historical exposure. Some experiments use different partition arrangements. |
| Logistic Regression training | Fit the LR pipeline using the training partition and preserve its fitted parameters. |
| Naive Bayes training | Fit the Multinomial NB pipeline using the training partition and preserve its fitted parameters. |
| Linear SVM training | Fit the Linear SVM pipeline using the training partition and preserve its fitted parameters. |
| mBERT training | Fine-tune the multilingual BERT model under the documented experiment configuration. |
| Calibration and threshold selection | Apply the experiment's calibration method and select the decision threshold using the designated development partitions. |
| Model comparison and evaluation | Compare accuracy, precision, recall, F1-score, confusion matrices, false alerts, and coverage on the same evaluation cohort. |
| Error and robustness analysis | Review false positives and missed phishing; examine source/language support, unsupported inputs, and transfer limitations. |
| Model export and Android verification | Export an eligible candidate, package its assets, and check that Android preprocessing, scores, and classifications match the reference pipeline. |
| Independent validation | Obtain actual independent label review and evaluate a genuinely new cohort when available; retain these as pending tasks until evidence exists. |

These are task labels for recording actual work, not instructions to retrain frozen models. Existing comparison models and historical results should retain their experiment identities.

## Additional prototype modules

| ID | Module name | Tasks / features | Current status |
|---|---|---|---|
| P01 | Reporting | Reporting screen, limited report-payload preparation, and a future voluntary submission flow. | The screen exists, but submission is disabled. Experimental detections are not eligible for the current payload builder. The app sends no reports. |
| P02 | Backend Analytics Dashboard | Local report endpoint, payload validation, prototype storage, and aggregate dashboard views. | Standalone local Flask prototype; disconnected from Android. Its historical city-based contract differs from the current app payload and needs reconciliation before integration. |

## Scope and task-log guidance

- Veritxt currently has no user login, registration, or account-management module.
- It has no persistent scan-history database. The checked-message preview is temporary; local preferences are stored separately.
- Incoming monitoring covers new SMS, not RCS, Messenger, WhatsApp, or other chat services. It does not replace the default SMS app or block/delete messages.
- Home Dashboard and Backend Analytics Dashboard are separate entries with different purposes and availability.
- Testing, documentation, APK packaging, and device checks can be task rows under the relevant module or separate project activities. They are not included as extra product modules in the count above.
- Owners, start dates, due dates, and spreadsheet statuses must reflect the team's actual assignments and evidence. This overview does not invent those values.
- Completed retrospective training and software parity checks do not establish independently validated future-message accuracy.

## Source references

This overview was checked against current app source and recent project records. Older documents may describe earlier feature policies.

- [Project overview and latest milestones](../README.md)
- [App screens, settings, reporting UI, and language controls](../android/app/src/main/java/ph/smishguard/MainActivity.kt)
- [Screen routing and temporary checking state](../android/app/src/main/java/ph/smishguard/CheckViewModel.kt)
- [Model loading and disabled reporting repository](../android/app/src/main/java/ph/smishguard/SmishGuardApp.kt)
- [Incoming SMS handling and warning notifications](../android/app/src/main/java/ph/smishguard/sms/IncomingSmsReceiver.kt)
- [Research workflow and training experiments](../research/README.md)
- [Selected Linear SVM integration](linear-svm-app-integration-20261013.md)
- [Latest separate retraining experiment](retraining-experiment-20261013.md)
- [Latest source-based research candidate](source-robustness-results-20261013.md)
- [Local backend prototype](../backend/README.md)
