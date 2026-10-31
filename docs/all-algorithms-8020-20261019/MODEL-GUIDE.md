# Models included in the 80/20 comparison

All entries share the same 2,734 training and 684 test messages. Model settings
come from earlier experiments and are fixed before this extension's fits.

| Report ID | Algorithm and representation |
|---|---|
| AE-A | Logistic Regression, word TF-IDF (1,2), C=.1, balanced weights, min_df=2, 20,000-feature cap |
| AE-B | Linear SVM, word TF-IDF (1,2), C=.1, balanced weights, min_df=2, 20,000-feature cap |
| AE-C | Combined word (1,2) + character (3,5) TF-IDF with Linear SVM, C=.1, balanced weights, min_df=1, no feature cap |
| AE-D | Combined word (1,2) + character (3,5) TF-IDF with Logistic Regression, C=.1, balanced weights, min_df=2, 30,000-feature cap per block |
| AE-E | Multinomial NB, word TF-IDF (1,2), alpha=.03, min_df=2, 20,000-feature cap |
| latest-A-baseline | NB alpha=1 with the latest URL/currency-preserving word-bigram tokenizer |
| latest-B-proposed | Same representation, NB alpha=.1 |
| latest-NB-alpha-* | Same representation, NB alpha=.01, .5 or 2 |
| latest-SVM-reference | Same representation, Linear SVM C=1 |
| legacy-lr / legacy-svm / legacy-nb | Earlier ASCII/masked unigram representation; LR C=10, SVM C=10, NB alpha=.1 |
| random-forest | 200 balanced trees, word TF-IDF (1,2), 5,000 features |
| knn | Five nearest neighbors, same 5,000-feature representation |
| mbert | Multilingual cased BERT, native tokenizer and two fresh fixed epochs |

A–E each appear twice: `raw` uses native scores or SVM margins; `sigmoid` uses
a training-only OOF sigmoid. Each legacy standalone entry uses its sigmoid.
The latest NB/SVM controls, Random Forest and KNN use native scores.

The **combined feature models** join word and character TF-IDF features before
fitting one LR or SVM classifier. The **combined model ensembles** combine the
predictions of several classifiers: all eleven pairs/triples/four-way soft votes
over legacy LR/SVM/NB/mBERT, plus LR+SVM+NB → LR and mBERT+SVM+NB → LR stacking.
The LR/NB voting and stacking inputs are native probabilities; SVM inputs are
training-OOF sigmoid probabilities. All base stacking rows are out of fold.

This gives 22 standalone score variants, eleven voting ensembles and two stacks:
**35 report entries**. The raw and sigmoid rows share one fitted classifier, and
ensembles share freshly trained components. They are not 35 independent base fits.

XLM-R was previously proposed but not trained. INT8 mBERT is an inference
quantization of a transformer, rather than another training algorithm.
