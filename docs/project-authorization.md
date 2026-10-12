# Authorization and operation-specific checks

The team reports that it has the go signal to proceed. **Project/client authorization is recorded as reported authorized**, supported by the attached signed client-request letter. Do not repeatedly request the same project approval. This supersedes earlier wording that conflated project authorization with dataset eligibility.

## What the supplied letter shows

The image is an LPU-Cavite College of Information Technology and Computer Science letter dated **September 11, 2026**, addressed to the City Mayor of Dasmariñas through the head of the Information Technology Department. It describes the SMISHGUARD financial-institution SMS phishing thesis and requests that the city government, through IT, serve as official client during **Thesis 1 and Thesis 2**, providing insights, consultation and feedback. It includes an academic-use/confidentiality undertaking.

Visible signatures appear in the research-leader, course-facilitator, thesis-adviser and IT-department approval areas. The Mayor's Office **RECEIVED** stamp is dated **September 14, 2026**. The mayor's printed approval block is visible; this image does not clearly establish a separate mayoral signature. The receipt stamp establishes receipt as shown, while the go-ahead is reported by the team. This is a description of the supplied image, not independent signature authentication.

The letter supports the thesis/client arrangement. It is **not blanket dataset licensing, participant consent for every message, or formal ethics clearance**. No such status is invented or required again merely to continue software development. The original image stays in Downloads; its hash and a nonidentifying description are recorded in [the status record](project-authorization.json). Contact details and signature images are not copied into Git, the source ZIP or APK.

## Separate statuses and checks

| Operation/status | Current basis and applicable check |
|---|---|
| Project/client work | Reported authorized. Continue implementation, local inspection, model conversion, offline parity, safe-fixture emulator tests and evaluation tooling. No repeated project approval gate. |
| Dataset permitted use | Assess each source/version and intended activity separately. Record original-source identity, applicable terms/permission and a controlled evidence reference. A hosting platform name neither qualifies nor disqualifies records. |
| Labels/redaction | Review record-level financial scope, identifiers and independent labels; hold uncertain/disputed cases until adjudication. A client letter cannot substitute for these checks. |
| Primary versus supplementary research | Explicit study-role assignment under the study protocol. UCI remains supplementary as planned; reviewed aggregator records may enter primary research if their documented permitted use and study-role decision support it. |
| Research fitting/evaluation | Use reviewed inputs for the selected role, train-only preprocessing, disjoint partitions and frozen selection. Previously used records remain retrospective; minimum-size and calibration/evaluation checks remain specific to research claims. |
| Data/model redistribution | Check that documented terms cover the intended redistribution; do not infer this from permission for local academic analysis. Raw data remains excluded from deliverables. Learned identifier-like model terms still need review before broader distribution. |
| Automatic warnings | Enabled in the app on 2026-10-12 at the team's request for the experimental supplied model. Evaluation, calibration/threshold requirements and a reviewed deployment policy are still outstanding, so warnings are labelled experimental and may be wrong. |
| Reporting | Disabled; no endpoint/privacy/retention implementation has been supplied. |

## Gate changes implemented

The importer now accepts truthful `aggregator`, `public_archive`, `social_post` and `external_collection` source types alongside existing origins. `permitted_use_status` and `permitted_use_reference` record operation-specific evidence. `study_role` separates primary, supplementary and undecided records. Donation consent is required for donation records; it is not used as a substitute license flag for public collections. Redaction and independent-label checks apply to both.

Use `--review-reference` for the intake decision record. The legacy `--approval-reference` option and output column remain compatible but mean **intake review**, not a new project/ethics approval. The software checks the declaration/reference structure; researchers must verify the linked evidence. No real package rows were auto-approved or relabeled by this change.
