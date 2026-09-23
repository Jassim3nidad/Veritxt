import pandas as pd
import json
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score, precision_recall_fscore_support

# 1. Load dataset
df = pd.read_csv('../data/smishguard_dataset.csv')
df = df.dropna(subset=['message_text', 'label'])
print(f"Total rows: {len(df)}")
print(df['label'].value_counts())
print(f"Class ratio - ham: {(df['label']=='ham').mean():.1%}, smishing: {(df['label']=='smishing').mean():.1%}")
print()

X = df['message_text']
y = df['label']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 2. TF-IDF vectorization
vectorizer = TfidfVectorizer(
    lowercase=True,
    ngram_range=(1, 2),
    max_features=5000,
    token_pattern=r'\b\w+\b'
)
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# 3. Models - class_weight='balanced' compensates for the 83/17 ham/smishing split
#    so minority-class (smishing) performance isn't swamped by raw accuracy
models = {
    'Linear SVM': LinearSVC(random_state=42, max_iter=5000, class_weight='balanced'),
    'Logistic Regression': LogisticRegression(random_state=42, max_iter=1000, class_weight='balanced'),
    'Random Forest': RandomForestClassifier(random_state=42, n_estimators=200, class_weight='balanced'),
    'Multinomial Naive Bayes': MultinomialNB(),  # MNB has no class_weight param
    'K-Nearest Neighbors': KNeighborsClassifier(n_neighbors=5),  # KNN has no class_weight param
}

results = []
trained_models = {}

for name, model in models.items():
    model.fit(X_train_vec, y_train)
    preds = model.predict(X_test_vec)

    acc = accuracy_score(y_test, preds)
    # per-class metrics matter more than weighted average given the imbalance
    precision, recall, f1, support = precision_recall_fscore_support(
        y_test, preds, labels=['ham', 'smishing'], zero_division=0
    )

    cv_scores = cross_val_score(model, X_train_vec, y_train, cv=5, scoring='f1_macro')

    results.append({
        'Algorithm': name,
        'Accuracy': round(acc, 4),
        'Smishing Precision': round(precision[1], 4),
        'Smishing Recall': round(recall[1], 4),
        'Smishing F1': round(f1[1], 4),
        'Ham F1': round(f1[0], 4),
        'Macro F1 (CV mean)': round(cv_scores.mean(), 4),
        'Macro F1 (CV std)': round(cv_scores.std(), 4),
    })
    trained_models[name] = model

    print(f"=== {name} ===")
    print(classification_report(y_test, preds, zero_division=0))
    print()

results_df = pd.DataFrame(results).sort_values('Smishing F1', ascending=False)
print("=== COMPARATIVE ANALYSIS (sorted by Smishing F1 - the class that matters) ===")
print(results_df.to_string(index=False))
results_df.to_csv('./comparative_analysis_v2.csv', index=False)

best_name = results_df.iloc[0]['Algorithm']
print(f"\nBest performer on Smishing F1: {best_name}")

joblib.dump(vectorizer, './vectorizer_v2.joblib')

# Export SVM regardless (for Kotlin portability, per earlier decision)
svm_model = trained_models['Linear SVM']
vocab = {k: int(v) for k, v in vectorizer.vocabulary_.items()}
idf = vectorizer.idf_.tolist()
coef = svm_model.coef_[0].tolist()
intercept = svm_model.intercept_.tolist()
classes = svm_model.classes_.tolist()

export = {
    "vocabulary": vocab, "idf": idf, "coef": coef, "intercept": intercept,
    "classes": classes, "ngram_range": [1, 2], "lowercase": True,
    "class_weight": "balanced", "trained_on_rows": len(df)
}
with open('./model_export_v2.json', 'w') as f:
    json.dump(export, f)

print(f"Exported Linear SVM (balanced) parameters — vocabulary size: {len(vocab)}")
