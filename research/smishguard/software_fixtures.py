"""Train tiny synthetic software fixtures. Never reports detection accuracy."""
import json
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from .linear_export import export_linear
from .preprocessing import normalize
from .train import margin


def generate():
    target = Path(__file__).resolve().parents[2] / "android/app/src/androidTest/assets/software"
    target.mkdir(parents=True, exist_ok=True)
    train = ["hello kumusta", "meeting bukas", "salamat bayad", "hello po", "verify account", "urgent bayad", "account zzurlzz", "verify ngayon"]
    labels = np.array([0, 0, 0, 0, 1, 1, 1, 1])
    vectorizer = TfidfVectorizer(lowercase=False, token_pattern=r"(?u)\b\w+\b").fit(train)
    x = vectorizer.transform(train)
    # Separate synthetic calibration inputs; all outputs remain software fixtures.
    calibration_x = vectorizer.transform(["hello meeting", "salamat po", "urgent verify", "account ngayon"])
    probes = ["HELLO kumusta", "verify account https://example.org/private?token=123", "unknown 🧪 ñ", "bayad " * 1000]
    for name, classifier in [("lr", LogisticRegression(random_state=42)), ("nb", MultinomialNB()), ("svm", LinearSVC(dual="auto", random_state=42))]:
        classifier.fit(x, labels)
        calibrator = LogisticRegression(random_state=42).fit(margin(classifier, calibration_x).reshape(-1, 1), [0, 0, 1, 1])
        model = export_linear(vectorizer, classifier, calibrator, .5, synthetic=True)
        scores = calibrator.predict_proba(margin(classifier, vectorizer.transform([normalize(t) for t in probes])).reshape(-1, 1))[:, 1]
        cases = [dict(text=t, score=float(s), suspicious=bool(s >= .5)) for t, s in zip(probes, scores)]
        for suffix, data in [("model", model), ("cases", cases)]:
            (target / f"{name}-{suffix}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    print("Created LR/NB/SVM Android instrumentation fixtures only; no research metrics.")


if __name__ == "__main__":
    generate()
