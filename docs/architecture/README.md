# Veritxt system architecture

Veritxt is an Android application that checks SMS messages for possible phishing. Message analysis runs offline on the phone using a packaged model. This overview describes the selectedSvm build and the code inspected on **19 October 2026**.

![Veritxt system architecture](veritxt-system-architecture-illustrated.png)

## System components and functions

| Component | Function |
|---|---|
| **User** | Types, pastes or shares a message for checking, reviews the assessment and chooses whether to open Android's blocking settings. |
| **New SMS input** | Receives newly delivered SMS through Android broadcasts when privacy acceptance, scanning consent, telephony support and SMS permission allow processing. Combines multipart messages and obtains available sender metadata. |
| **Veritxt Android app** | Provides the checking interface, coordinates offline analysis and displays results. Includes privacy consent, onboarding, settings, help and English/Filipino language support. |
| **Text preparation** | Cleans the SMS, masks URLs, email addresses and numbers, and converts text into the token and TF-IDF features expected by the selected model. |
| **Linear SVM model** | Uses packaged model parameters and a stored decision threshold to classify assessable SMS as suspicious or not suspicious. Returns an unassessable or error state when checking cannot be completed. |
| **Risk policy** | Combines visible indicators, such as credential requests, payment requests, urgency and deceptive URL patterns, with a usable suspicious-model signal to produce the risk assessment. |
| **Risk result** | Displays Low, Medium or High Risk, or Unable to assess, with supporting indicators, limitations and a temporary preview of the checked message. |
| **High Risk SMS alert** | Notifies the user when an eligible incoming-SMS check produces High Risk. Requires an automatic-warning-enabled detector, scanning consent and the necessary SMS/notification permissions and channel availability. Notifications contain generic text rather than the message body or sender. |
| **Pending notification check** | Temporarily holds incoming text and an optional numeric sender in process memory, associated with a single-use ID. Tapping the notification starts a fresh check. Entries expire after ten minutes or disappear when the process ends. Builds without automatic warnings can offer a neutral check prompt. |
| **Local preferences** | Persists privacy acceptance, onboarding status, incoming-scanning consent and reduced-transparency settings. Application language is managed separately through Android/AppCompat. |
| **Manual blocking handoff** | After user confirmation, attempts to open Android's blocked-number settings or provides fallback instructions. The user adds and confirms the sender in Android; Veritxt does not modify the blocklist itself. |
| **Model training and evaluation** | Runs on a development computer to prepare data, train and compare LR, NB, SVM and mBERT experiments, evaluate candidates and export model assets for a specific app build. These models are alternatives; they do not all run together in the selected-SVM app. |
| **APK model packaging** | Validates and bundles the chosen model and its preprocessing contract into the APK. This is build-time delivery rather than a live connection between the phone and training computer. |
| **Flask API — separate prototype** | Validates report metadata submitted to the standalone local backend. Android reporting is currently disabled, so the app sends no reports to it. |
| **SQLite — separate prototype** | Stores validated report metadata and separately identified demo records for the local backend. It is not the Android app's scan-history storage. |
| **Dashboard — separate prototype** | Displays aggregate report information from the backend's SQLite database through a Flask-rendered web interface. |

## Risk assessment

| Result | Meaning |
|---|---|
| **Low Risk: 0–29** | No significant indicators under the implemented policy for assessable input; this does not guarantee safety. |
| **Medium Risk: 30–69** | Indicators warrant caution and further verification. |
| **High Risk: 70–100** | Strong or combined indicators warrant a warning. Eligible incoming-SMS checks can trigger an alert. |
| **Unable to assess** | The available content, model or processing state does not support an assessment. No numeric risk score is assigned. |

The risk score is an evidence index, not a probability or an accuracy percentage. Model classification and risk scoring are separate functions.

## Data handling

Checked messages and results remain in temporary application memory and clear when the checking session ends. The app has no persistent scan-history database or cloud inference service. Preferences persist locally. Sender information comes from available Android SMS metadata; numbers found in message text are not assumed to identify the sender.

The backend remains disconnected from Android. The current app uses DisabledReportingRepository and declares no INTERNET permission.

For implementation details and links to the supporting source files, see the [full architecture description](../VERITXT-SYSTEM-ARCHITECTURE.md).
