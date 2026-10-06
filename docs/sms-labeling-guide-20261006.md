# SMS labeling guide

Current scope: **all SMS phishing**, clarified by the team on 6 October 2026; adviser approval is not asserted. Revised thesis title: **Pending finalization**. Existing title and title-dependent wording remain historical/pending respectively.

Read the message independently. Do not consult model scores, inherited labels, source datasets, the other reviewer, or the results chapter while annotating. Do not visit links or contact senders. Judge the available redacted text; missing context is a valid reason for uncertainty.

Choose one decision:

| Decision | Definition |
|---|---|
| phishing | A deceptive SMS attempts to obtain credentials, personal information or money, or induce harmful action such as installing malicious software, through impersonation or a misleading pretext. Financial and nonfinancial themes are included. A URL is neither necessary nor sufficient. |
| genuine | Available content supports an ordinary legitimate communication and contains no deceptive solicitation. Absence of an obvious URL alone is insufficient. |
| out_of_scope | Non-SMS material or pure nonphishing spam/scam that cannot defensibly be labeled genuine. Document the reason. A sector, brand, job/loan theme or absence of a URL is never itself a reason to exclude phishing. Legitimate advertising can be genuine when the available evidence supports that decision. |
| uncertain | Redaction, missing context, mixed signals or unresolved scope prevents a defensible decision. |

For a job/loan message with a defensible phishing mechanism, select `phishing`; use `uncertain` when evidence is insufficient. The inherited dataset's blanket exclusion is historical and does not govern new labels. The 18 known conflicts require fresh independent review; no label is automatically changed. Record the guide version supplied to reviewers and disclose any mid-review change. If reviewers used conflicting definitions, create a new matched packet version and repeat the affected independent reviews.

Give a brief text-grounded rationale without reproducing personal identifiers. Mark `privacy_issue` as `yes`, `no` or `uncertain`. If a possible real name, phone number, account, address or usable personal link remains, flag it and stop sharing that row. Do not change the message yourself; request a matched revision through the coordinator. `zzurlzz`, `zzemailzz` and `zznumberzz` mark automatic minimization and do not imply either class. Names may have been removed. No automated process certifies complete privacy review.

Use the same definitions for English, Filipino and Taglish. Unfamiliar language should lead to uncertainty or a documented qualified-language review, not a guessed label. Add the actual reviewer code and UTC completion timestamp after deciding. Leave unreviewed rows blank. Neither confidence ratings nor model predictions are required.

Fictional practice examples (excluded from all research evaluation):

- “Your account is suspended. Verify your password at https://account.example now.” contains a credential-verification threat and is intended as a phishing practice example.
- “Bayad na po. Salamat sa tulong, kita tayo bukas.” is an ordinary conversational practice example.
- “New shirts on sale this weekend.” alone is insufficient to prove either phishing or legitimacy; use available context and retain uncertainty where necessary.

Practice examples teach the definitions, not lexical rules. Decisions on research records must remain independent.
