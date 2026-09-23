# Proposed threshold policy: research evidence only

Not implemented or approved. Android retains strict score >0.5 and its existing user-visible behavior. Automatic SMS warnings remain disabled/unapproved.

| Score | Research proposal |
|---|---|
| >0.50 | Current alert-tier classification threshold, not permission for automatic alerts |
| >0.35 and <=0.50 | Proposed soft caution, requires human approval and usability testing |
| <=0.35 | No caution under the proposal |

Scores are uncalibrated: 0.35 does not mean a 35% probability. The handoff reports refits over five stratified 80/20 splits, using 1,276 rows (1,054 ham / 222 smishing). No threshold-evaluation script, per-seed predictions or independently reviewed prospective cohort was supplied. These are handoff-reported results, not reproduced findings:

| Policy | Alert smishing / ham | Caution smishing / ham | Smishing missed | Legitimate OTP alerted / cautioned |
|---|---|---|---|---|
| Single 0.50 | 38.2 / 5.2 | none | 6.8 | 1.2 / 0 |
| Single 0.35 | 43.2 / 10.2 | none | 1.8 | 3.0 / 0 |
| Two-tier 0.35 / 0.50 | 38.2 / 5.2 | 5.0 / 5.0 | 1.8 | 1.2 / 1.8 |
| Two-tier 0.40 / 0.50 | 38.2 / 5.2 | 2.8 / 2.8 | 4.0 | 1.2 / 0.8 |

The proposed caution band contains roughly equal smishing and legitimate cases, including legitimate OTP messages. This raises alert-fatigue and trust concerns; no benefit is established for users. OTP identification was a keyword heuristic, not independently adjudicated subgroup evidence. Counts imply 45 smishing cases per split, despite the original text approximating 44. Do not infer statistical significance from these means or reuse them as live prevalence.

Prospective evaluation, independent labels, calibration analysis, threshold selection isolated from final testing, human review and usability testing remain pending. There is no approval for automatic warnings or production deployment.
