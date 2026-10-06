# SMS labeling guide

Read the message independently. Do not consult model scores, inherited labels, source datasets, the other reviewer, or the results chapter while annotating. Do not visit links or contact senders. Judge the available redacted text; missing context is a valid reason for uncertainty.

Choose one decision:

| Decision | Definition |
|---|---|
| phishing | A deceptive message attempts to obtain credentials, personal information or money through impersonation, false rewards or a misleading verification/payment request. A URL is neither necessary nor sufficient. |
| genuine | Available content supports an ordinary legitimate communication and contains no deceptive solicitation. Absence of an obvious URL alone is insufficient. |
| out_of_scope | Advertising or a job/loan solicitation without an identifiable phishing mechanism, or other content outside the defined binary task. Do not treat these messages as genuine by default. |
| uncertain | Redaction, missing context, mixed signals or unresolved scope prevents a defensible decision. |

For a job/loan message that also uses impersonation, a false verification request or another phishing mechanism, record `uncertain` and explain the conflict for adjudication. The inherited dataset excluded job/loan fraud; this boundary needs a documented scope decision before future admission. Do not silently redefine it during annotation.

Give a brief text-grounded rationale without reproducing personal identifiers. Mark `privacy_issue` as `yes`, `no` or `uncertain`. If a possible real name, phone number, account, address or usable personal link remains, flag it and stop sharing that row. Do not change the message yourself; request a matched revision through the coordinator. `zzurlzz`, `zzemailzz` and `zznumberzz` mark automatic minimization and do not imply either class. Names may have been removed. No automated process certifies complete privacy review.

Use the same definitions for English, Filipino and Taglish. Unfamiliar language should lead to uncertainty or a documented qualified-language review, not a guessed label. Add the actual reviewer code and UTC completion timestamp after deciding. Leave unreviewed rows blank. Neither confidence ratings nor model predictions are required.

Fictional practice examples (excluded from all research evaluation):

- “Your account is suspended. Verify your password at https://account.example now.” contains a credential-verification threat and is intended as a phishing practice example.
- “Bayad na po. Salamat sa tulong, kita tayo bukas.” is an ordinary conversational practice example.
- “New shirts on sale this weekend.” illustrates advertising outside the binary task.

Practice examples teach the definitions, not lexical rules. Decisions on research records must remain independent.
