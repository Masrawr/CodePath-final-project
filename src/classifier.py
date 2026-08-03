"""
Classifier — the ADVANCED FEATURE: a specialized model.

A scikit-learn TF-IDF + LogisticRegression classifier, trained on data/bugs.csv
to tag a code snippet with a bug category. It runs locally in the Streamlit app
(no GPU, no external service) and gives a second, specialized signal that we
compare against Gemini's category in the evaluator.

Train it with:  python3 src/train_classifier.py   (writes model/classifier.joblib)

Bug taxonomy:
    state_bug, logic_inverted, missing_validation, off_by_one, dead_control, clean
"""

import os
import re

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "model")
MODEL_PATH = os.path.join(MODEL_DIR, "classifier.joblib")

# Lazy singleton so the model file is loaded once, only when first needed.
_pipeline = None


class ModelNotTrainedError(RuntimeError):
    """Raised when classify() is called before the model has been trained."""


def code_tokenizer(text: str) -> list[str]:
    """Tokenize code for TF-IDF: split identifiers and lowercase.

    `st.session_state` -> ['st', 'session', 'state']; `parseGuess` ->
    ['parse', 'guess']. Defined at module scope so the fitted vectorizer that
    references it can be pickled and reloaded.
    """
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)  # split camelCase
    raw = re.split(r"[^A-Za-z0-9]+", text)
    return [t.lower() for t in raw if t]


def load_model(model_path: str = MODEL_PATH):
    """Load the trained pipeline (cached). Raises ModelNotTrainedError if absent."""
    global _pipeline
    if _pipeline is not None:
        return _pipeline
    if not os.path.exists(model_path):
        raise ModelNotTrainedError(
            f"No trained model at '{model_path}'. "
            "Train it with: python3 src/train_classifier.py"
        )
    import joblib
    _pipeline = joblib.load(model_path)
    return _pipeline


def classify(snippet: str, model_path: str = MODEL_PATH) -> tuple[str, float]:
    """
    Return (predicted_category, confidence) for a code snippet.

    confidence is the predicted-class probability in [0, 1].
    Raises ModelNotTrainedError if the model has not been trained yet.
    """
    pipeline = load_model(model_path)
    probs = pipeline.predict_proba([snippet])[0]
    classes = pipeline.classes_
    best = probs.argmax()
    return str(classes[best]), float(probs[best])


if __name__ == "__main__":
    # The saved model references src.classifier.code_tokenizer, so make the
    # project root importable when running this file directly (the app and
    # tests already import via `src.classifier`, so they don't need this).
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    demo = (
        "def check_guess(guess, secret):\n"
        "    if guess > secret:\n"
        "        return 'Too Low'\n"
        "    return 'Too High'"
    )
    try:
        label, conf = classify(demo)
        print(f"{label}  (confidence {conf:.2f})")
    except ModelNotTrainedError as e:
        print(e)
