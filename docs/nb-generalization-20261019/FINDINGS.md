# What the NB retraining established

The earlier 99.71% accuracy does not establish general reliability. Retraining
and broader holdouts reveal substantial source-transfer weakness. These checks
do not establish that NB simply memorized exact messages.

The old test had 684 messages, but 606 (88.60%) belonged to one component. Exact
normalized-text overlap and stored group overlap were both zero. The additional
nearest-training character-cosine audit found zero test messages at similarity
>=.90; median similarity was .430 and the 95th percentile was .676. This is a
heuristic check, not proof of independent campaigns or complete absence of leakage.

Five new, disjoint 80/20 folds each contain **60 test components**. Every eligible
message is predicted once by a model that excluded its component from fitting.
For the original NB alpha=.1, average training accuracy is **99.94%**, pooled
held-out accuracy **98.07%**, and scam F1 **90.00%**. Individual fold F1 ranges
from **82.26% to 97.14%**. Giving components equal weight reduces accuracy to
**82.20%**, showing how large groups affect the headline row-weighted result.

Entire-source holdouts expose a larger weakness. Excluding all Tagalog-SMS rows
and purging related components gives original-NB F1 **22.22%**, with **274 false
alerts among 2,149 ham messages** (12.75%). It detects 41/54 scams. This changes
both source and prevalence: fitting has 189/560 scams, versus 54/2,203 in the
held-out source. It does not isolate a single cause such as memorization.
On the positive-only bwandowando source, original NB detects only 75/153 scams
(49.02% recall); that source cannot estimate false-positive rate.

Dataset shortcuts matter: a diagnostic NB receiving **only dataset source, with
no SMS text**, achieves **93.86% accuracy**. This demonstrates source/label
confounding; it does not prove that the text model explicitly uses source
metadata. An all-ham classifier achieves 89.38% accuracy while missing every
scam. The separate randomized-label control gives only 1.08% scam F1, as expected
when the learned text/label relationship is broken; it is not a significance test.

Removing URLs, emails, numbers and amounts, restricting rare/common terms and
capping vocabulary did not consistently fix transfer. Reduced NB alpha=.1 has
**88.53%** group-CV F1 and **19.86%** Tagalog-source F1. Increasing alpha to 1
gives **75.26%** group-CV F1. A lower score or stronger smoothing is not by itself
evidence of a better model.

All original, identifier-reduced and more strongly smoothed models were freshly
fitted and retained. First-fold reference pipelines use 2,734 fitting messages;
their 684 test messages were excluded. No candidate was chosen by these new test
rankings or installed in the app. Independent labels and genuinely unseen messages
are still unavailable; these are retrospective diagnostics.

See [all measured results and reproduction commands](RESULTS.md) and the
[prespecified protocol](PROTOCOL.md). Private models, neighbors and row predictions
remain in `research/runs/nb-generalization-20261019/run-v1/`.
