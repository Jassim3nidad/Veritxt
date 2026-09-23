import pandas as pd
import json
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# 1. Load the full dataset
df = pd.read_csv('../data/smishguard_dataset.csv')
df = df.dropna(subset=['message_text', 'label'])
print(f"Training on full dataset: {len(df)} rows")
print(df['label'].value_counts())

X = df['message_text']
y = df['label']

# 2. TF-IDF vectorizer - same simple tokenizer as before, easy to replicate in Kotlin
vectorizer = TfidfVectorizer(
    lowercase=True,
    ngram_range=(1, 2),
    max_features=5000,
    token_pattern=r'\b\w+\b'
)
X_vec = vectorizer.fit_transform(X)

# 3. Train Logistic Regression with the tuned hyperparameters found earlier
model = LogisticRegression(
    C=2,
    penalty='l2',
    solver='liblinear',
    class_weight='balanced',
    max_iter=2000,
    random_state=42
)
model.fit(X_vec, y)

# 4. Save Python-side artifacts (for the research dashboard / future retraining)
joblib.dump(vectorizer, './final_vectorizer.joblib')
joblib.dump(model, './final_lr_model.joblib')

# 5. Export raw parameters for Kotlin
vocab = {k: int(v) for k, v in vectorizer.vocabulary_.items()}
idf = vectorizer.idf_.tolist()
coef = model.coef_[0].tolist()       # single row since binary classification
intercept = float(model.intercept_[0])
classes = model.classes_.tolist()    # e.g. ['ham', 'smishing'] - alphabetical order

export = {
    "model_type": "logistic_regression",
    "vocabulary": vocab,
    "idf": idf,
    "coef": coef,
    "intercept": intercept,
    "classes": classes,
    "ngram_range": [1, 2],
    "lowercase": True,
    "trained_on_rows": len(df),
    "note": "classes[1] is the positive class for sigmoid(coef . tfidf + intercept)"
}

with open('./model_export_final.json', 'w') as f:
    json.dump(export, f)

print(f"\nVocabulary size: {len(vocab)}")
print(f"Classes (order matters for Kotlin): {classes}")
print(f"Intercept: {intercept}")

# Reference SMS text intentionally omitted from this public copy.
# Use the existing safe Android parity fixtures; never update expected scores to hide drift.
