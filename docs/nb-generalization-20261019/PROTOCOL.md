# Naive Bayes memorization/shortcut audit — 19 October 2026

User requests retraining because the 99% result may reflect memorization. Do not
interpret high accuracy alone as proof of memorization, intentionally lower the
score, choose favorable seeds, or fabricate fresh independent data. Preserve old
fits and the app. The earlier dataset/test outputs already influenced selection.

Re-import the original October 12 ZIP through the unchanged cleaning policy;
require identical eligible rows and recompute the label-blind template/sender
components. Audit the earlier split's exact/group overlap, component dominance
and nearest-training character-cosine similarity. Cosine is a diagnostic heuristic.

Freeze five disjoint group folds. Target rounded exact 80/20 row and class counts;
keep components intact. Assign the five largest groups to separate folds; constrain
group counts to 80–120% of the equal-group target and minimize their deviation
from that target, then source/class composition deviation. Seed 42 breaks ties.
Accept a validated feasible incumbent from the fixed 45-second solver budget;
report status/optimality and actual counts. If no feasible allocation exists, stop
and report the constraint problem; do not fall back to row leakage or score search.

Separately leave out each entire source and purge every connected group touching
that source from fitting. These stress tests have differing train/test fractions
and must not be described as 80/20. Positive-only sources cannot estimate FPR.

Fixed candidates: original raw-URL NB alpha=.1, identifier-reduced NB alpha=.1,
identifier-reduced NB alpha=1. Reduced features remove URLs, emails, numbers and
amounts without learned text rewriting; TF-IDF (1,2), conservative shared stopwords,
min_df=2, max_df=.95, 20,000-feature cap. Fixed threshold >=.5. Every vocabulary,
IDF, feature cap and class prior is fitted on the relevant training rows only.
Do not tune hyperparameters/thresholds from these new evaluation results.

Add five-fold source-only NB and label-permutation negative controls. Permute the
separate diagnostic labels once with seed 20261019; never change actual labels.
The randomized-label metrics are a sanity check, not actual phishing performance
or a significance test. Report an all-ham baseline to expose accuracy inflation.

Save all fold fits/memberships and training metrics; seal before held-out scoring.
Report pooled complete OOF row metrics, fold variation, train/test gaps,
equal-component metrics and all source-purged stress results. Report outcomes
regardless of rank or magnitude. Keep first-fold reference artifacts, selected
before scoring; no model is selected/installed for deployment from these results.
Require exclusive evaluation, immutable source/input/model hashes and saved-metric
recomputation. Preserve data, weights, vocabularies, neighbor IDs and row outputs
inside ignored private run directories; publish aggregate evidence only.
