# Provenance of the 1,200-record rule

The number is a **documented study feasibility target**, not a universal statistical minimum. It was not invented solely by the training code. However, the evidence inspected does **not establish that the particular methodology version containing it has been formally approved**, nor does it establish a separate explicit team decision approving the code's stricter interpretation.

## Sources checked on 29 September 2026

| Source | Location and finding | Evidence boundary |
|---|---|---|
| Supplied `SmishGuardPH_Chapter1_Introduction_1.docx` | Scope of the Study; paragraph 32 in document XML order: “The target is 2,500 messages, with 1,200 as the least workable number.” | Establishes the numerical target in the supplied Chapter 1. Does not by itself establish final methodology approval or a statistical power calculation. |
| Local `SmishGuard-PH_Thesis_Proposal.md` / `.docx` | Section 9.2.3, Corpus Targets and Feasibility. Minimum table: 1,200 total; 450 fraudulent financial impersonation, 300 legitimate financial/transactional, 450 other legitimate; at least 90 fraudulent template clusters. Preferred total: 2,500. | Related proposal variant, not automatically the controlling approved protocol. It also excludes Kaggle primary data, whereas later repository instructions assess aggregators individually. Do not silently adopt all its provisions. |
| Same proposal, fallback immediately after that table | Below minimum: drop temporal and secondary experiments, use repeated grouped folds with uncertainty, reduce transformer comparisons and frame modeling as preliminary. | A fallback is described; “all modeling is universally prohibited below 1,200” is not what this source says. A concrete applicable fallback still needs a versioned team/adviser decision before execution. |
| Supplied `SmishGuardPH_Chapter2_RRL_1.docx`, `SmishGuard_ProjectBrief_Client.docx` | No 1,200/2,500 occurrence found. | The project/client authorization does not establish the sample-design rule. No repeat project authorization is requested. |
| Git `b3c11e7`, `docs/decisions.md`; current `train.py` and `fair_compare.py` | Initial implementation records the target and introduces a hard guard on eligible primary rows. | Implementation of a sourced target, with additional interpretation. Later repository repetitions and the user's instruction to retain pending-data status are not independent evidence of approval. |

Source hashes (files remain private in the user's Downloads folder): Chapter 1 `9254297b3e952018ca5f094c7be31d0335a24f614fe3d3f3d4db46d67b743f5a`; proposal DOCX `7ba84639104d31664a606b98b566534df9156b355f4330ff23cc40f11d16241e`; Chapter 2 `a390f1eee50f3297400fbb536f796c7419ac7dd6cf8fe7f6108584624c5a767a`; client brief `70133e3672cf493d53a066a9cc218f982d4466356b7b84b63830c0dd8f31e01c`. Exact local extraction context is preserved under ignored `research/data/preparation-20260929/methodology-trace-private.json`. Paragraph indices are not page numbers.

## Implementation interpretation that needs resolution

The present importer requires `financial_scope=true` even for legitimate negatives. Both training entry points require 1,200 records **after** primary eligibility filtering. The proposal's minimum table includes 450 “other legitimate” records; those would not necessarily satisfy that financial-only importer. The code also does not enforce the proposal's per-category and 90-cluster targets. Thus the guard is not a complete or exact implementation of that proposal's sample design.

The team/adviser should record the controlling document/version and its approval evidence, the intended legitimate-negative scope, applicable total/class/group support requirements, and a precise fallback if support is inadequate. Use `research/templates/methodology-decision.csv`, populated privately. A sample-size rationale depends on class support, independent groups, precision of the desired estimates and evaluation design; a bare total is not a guarantee of statistical adequacy.

No guard was lowered and no training was run in this preparation task. The guard remains a conservative configured constraint while its applicability is resolved. Dataset rights, redaction, independent labels and leakage prevention remain necessary even if a lower-sample exploratory protocol is selected. No source document or approval record was rewritten.
