"""
Train the specialized bug classifier (the advanced feature).

Fits a TF-IDF + LogisticRegression pipeline on data/bugs.csv and saves it to
model/classifier.joblib. Prints accuracy, a per-class report, and a confusion
matrix — copy these into model_card.md.

Run:  python3 src/train_classifier.py
"""

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.classifier import code_tokenizer, MODEL_DIR, MODEL_PATH

DATA_CSV = os.path.join(os.path.dirname(MODEL_DIR), "data", "bugs.csv")


def load_data(csv_path=DATA_CSV):
    snippets, labels = [], []
    with open(csv_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            snippets.append(row["snippet"])
            labels.append(row["label"])
    return snippets, labels


def main():
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report, confusion_matrix
    import joblib

    X, y = load_data()
    print(f"Loaded {len(X)} labeled snippets.")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42)

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(tokenizer=code_tokenizer, token_pattern=None)),
        ("clf", LogisticRegression(max_iter=1000, C=10.0)),
    ])
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    labels = sorted(set(y))
    print("\n=== Test-set report ===")
    print(classification_report(y_test, y_pred, labels=labels))
    print("Confusion matrix (rows=true, cols=pred):")
    print("labels:", labels)
    for name, row in zip(labels, confusion_matrix(y_test, y_pred, labels=labels)):
        print(f"  {name:18s} {[int(x) for x in row]}")

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)
    print(f"\nSaved model to {MODEL_PATH}")


if __name__ == "__main__":
    main()
