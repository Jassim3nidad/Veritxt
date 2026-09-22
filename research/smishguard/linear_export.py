"""One portable export implementation shared by research and software fixtures."""
import numpy as np
from .preprocessing import VERSION


def export_linear(vectorizer, model, calibrator, threshold, *, synthetic):
    if list(model.classes_) != [0, 1] or list(calibrator.classes_) != [0, 1]:
        raise ValueError("Binary class order must be [0, 1]")
    if vectorizer.analyzer != "word" or vectorizer.ngram_range != (1, 1) or vectorizer.norm != "l2" or vectorizer.sublinear_tf or vectorizer.binary:
        raise ValueError("Android requires raw-count word-unigram TF-IDF/L2")
    if hasattr(model, "feature_log_prob_"):
        weights = model.feature_log_prob_[1] - model.feature_log_prob_[0]
        bias = model.class_log_prior_[1] - model.class_log_prior_[0]
    else:
        weights, bias = model.coef_[0], model.intercept_[0]
    vocabulary = vectorizer.get_feature_names_out().tolist()
    if len(weights) != len(vocabulary) or not all(w.isascii() and w.isalpha() and w.islower() for w in vocabulary):
        raise ValueError("Vocabulary incompatible with Android preprocessing")
    if not np.isfinite(np.r_[weights, bias, vectorizer.idf_, calibrator.coef_.ravel(), calibrator.intercept_, threshold]).all() or not 0 <= threshold <= 1:
        raise ValueError("Invalid numeric model parameters")
    return dict(schema_version=1, preprocessing_version=VERSION,
        feature_type="word-unigram-tfidf-l2", vocabulary=vocabulary,
        idf=vectorizer.idf_.tolist(), weights=weights.tolist(), bias=float(bias),
        classes=["not_suspicious", "suspicious"], threshold=float(threshold),
        calibration=dict(method="sigmoid", a=float(calibrator.coef_[0, 0]), b=float(calibrator.intercept_[0])),
        calibration_evaluated=False, synthetic=bool(synthetic))
