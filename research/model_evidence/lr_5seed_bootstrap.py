import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_recall_fscore_support, accuracy_score

df = pd.read_csv('../data/smishguard_dataset.csv')
df = df.dropna(subset=['message_text', 'label'])
X = df['message_text']
y = df['label']

SEEDS = [42, 7, 123, 2024, 99]
N_BOOTSTRAP = 1000

seed_results = []

for seed in SEEDS:
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=seed, stratify=y
    )

    vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 2), max_features=5000, token_pattern=r'\b\w+\b')
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    model = LogisticRegression(random_state=seed, max_iter=1000, class_weight='balanced')
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

    # Bootstrap CI on this seed's test predictions
    if seed == SEEDS[0]:
        y_test_arr = np.array(y_test)
        preds_arr = np.array(preds)
        n = len(y_test_arr)
        boot_f1s = []
        rng = np.random.default_rng(seed)
        for _ in range(N_BOOTSTRAP):
            idx = rng.integers(0, n, n)
            _, _, f1_b, _ = precision_recall_fscore_support(
                y_test_arr[idx], preds_arr[idx], labels=['ham', 'smishing'], zero_division=0
            )
            boot_f1s.append(f1_b[1])  # smishing F1
        boot_f1s = np.array(boot_f1s)
        ci_low, ci_high = np.percentile(boot_f1s, [2.5, 97.5])

results_df = pd.DataFrame(seed_results)
print("=== Logistic Regression across 5 seeds ===")
print(results_df.to_string(index=False))
print()
print(f"Mean accuracy: {results_df['accuracy'].mean():.4f} (std: {results_df['accuracy'].std():.4f})")
print(f"Mean smishing F1: {results_df['smishing_f1'].mean():.4f} (std: {results_df['smishing_f1'].std():.4f})")
print()
print(f"Bootstrapped 95% CI for smishing F1 (seed {SEEDS[0]}, {N_BOOTSTRAP} resamples): "
      f"[{ci_low:.4f}, {ci_high:.4f}]")

results_df.to_csv('./lr_5seed_results.csv', index=False)
