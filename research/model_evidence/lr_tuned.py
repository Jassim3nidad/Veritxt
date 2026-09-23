import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold
from sklearn.metrics import precision_recall_fscore_support, accuracy_score, classification_report

df = pd.read_csv('../data/smishguard_dataset.csv')
df = df.dropna(subset=['message_text', 'label'])
X = df['message_text']
y = df['label']

SEEDS = [42, 7, 123, 2024, 99]
N_BOOTSTRAP = 1000

# --- Step 1: find the best hyperparameters using one split, validation-only ---
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 2), max_features=5000, token_pattern=r'\b\w+\b')
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

param_grid = {
    'C': [0.1, 0.5, 1, 2, 5, 10],
    'penalty': ['l1', 'l2'],
    'solver': ['liblinear'],
    'class_weight': ['balanced', None],
}

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
grid = GridSearchCV(
    LogisticRegression(max_iter=2000, random_state=42),
    param_grid, scoring='f1_macro', cv=cv, n_jobs=-1
)
grid.fit(X_train_vec, y_train)

print("=== Best hyperparameters found ===")
print(grid.best_params_)
print(f"Best CV macro-F1: {grid.best_score_:.4f}")
print()

best_params = grid.best_params_

# --- Step 2: re-run the 5-seed + bootstrap protocol using the tuned hyperparameters ---
seed_results = []
for seed in SEEDS:
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=seed, stratify=y)

    vec = TfidfVectorizer(lowercase=True, ngram_range=(1, 2), max_features=5000, token_pattern=r'\b\w+\b')
    X_train_vec = vec.fit_transform(X_train)
    X_test_vec = vec.transform(X_test)

    model = LogisticRegression(random_state=seed, max_iter=2000, **best_params)
    model.fit(X_train_vec, y_train)
    preds = model.predict(X_test_vec)

    acc = accuracy_score(y_test, preds)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test, preds, labels=['ham', 'smishing'], zero_division=0
    )
    seed_results.append({
        'seed': seed, 'accuracy': acc,
        'smishing_precision': precision[1], 'smishing_recall': recall[1], 'smishing_f1': f1[1],
        'ham_f1': f1[0]
    })

    if seed == SEEDS[0]:
        print(f"=== Detailed report, seed {seed} (tuned model) ===")
        print(classification_report(y_test, preds, zero_division=0))
        y_test_arr, preds_arr = np.array(y_test), np.array(preds)
        n = len(y_test_arr)
        rng = np.random.default_rng(seed)
        boot_f1s = []
        for _ in range(N_BOOTSTRAP):
            idx = rng.integers(0, n, n)
            _, _, f1_b, _ = precision_recall_fscore_support(
                y_test_arr[idx], preds_arr[idx], labels=['ham', 'smishing'], zero_division=0
            )
            boot_f1s.append(f1_b[1])
        ci_low, ci_high = np.percentile(boot_f1s, [2.5, 97.5])

results_df = pd.DataFrame(seed_results)
print("=== Tuned Logistic Regression across 5 seeds ===")
print(results_df.to_string(index=False))
print()
print(f"Mean accuracy: {results_df['accuracy'].mean():.4f} (std: {results_df['accuracy'].std():.4f})")
print(f"Mean smishing F1: {results_df['smishing_f1'].mean():.4f} (std: {results_df['smishing_f1'].std():.4f})")
print(f"Bootstrapped 95% CI for smishing F1: [{ci_low:.4f}, {ci_high:.4f}]")

results_df.to_csv('./lr_tuned_5seed_results.csv', index=False)

import json
with open('./lr_best_params.json', 'w') as f:
    json.dump(best_params, f, indent=2)
