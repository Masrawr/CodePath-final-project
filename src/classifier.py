"""
Classifier — the ADVANCED FEATURE: a fine-tuned / specialized model.

A small DistilBERT classifier (trained by notebooks/finetune.ipynb on
data/bugs.csv) that tags a code snippet with a bug category. It gives a second,
specialized signal that we compare against Claude's category in the evaluator.

Expected files in MODEL_DIR (produced by the notebook):
    config.json, model.safetensors, tokenizer files, and labels.json

Bug taxonomy:
    state_bug, logic_inverted, missing_validation, off_by_one, dead_control, clean
"""

import json
import os

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "model")

# Lazy singletons so the (large) model loads once, only when first needed.
_model = None
_tokenizer = None
_labels = None


class ModelNotTrainedError(RuntimeError):
    """Raised when classify() is called before a fine-tuned model exists."""


def _is_trained(model_dir: str) -> bool:
    """True if MODEL_DIR looks like it contains a saved fine-tuned model."""
    has_weights = any(
        os.path.exists(os.path.join(model_dir, f))
        for f in ("model.safetensors", "pytorch_model.bin")
    )
    has_labels = os.path.exists(os.path.join(model_dir, "labels.json"))
    return has_weights and has_labels


def load_model(model_dir: str = MODEL_DIR):
    """Load the fine-tuned classifier, tokenizer, and label list (cached)."""
    global _model, _tokenizer, _labels
    if _model is not None:
        return _model, _tokenizer, _labels

    if not _is_trained(model_dir):
        raise ModelNotTrainedError(
            f"No fine-tuned model found in '{model_dir}'. "
            "Run notebooks/finetune.ipynb and unzip the result into model/."
        )

    # Imported here so the rest of the app doesn't require torch/transformers
    # until the classifier is actually used.
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    _tokenizer = AutoTokenizer.from_pretrained(model_dir)
    _model = AutoModelForSequenceClassification.from_pretrained(model_dir)
    _model.eval()
    with open(os.path.join(model_dir, "labels.json"), encoding="utf-8") as f:
        _labels = json.load(f)
    return _model, _tokenizer, _labels


def classify(snippet: str, model_dir: str = MODEL_DIR) -> tuple[str, float]:
    """
    Return (predicted_category, confidence) for a code snippet.

    confidence is the softmax probability of the winning class in [0, 1].
    Raises ModelNotTrainedError if no fine-tuned model is available yet.
    """
    # load_model() raises ModelNotTrainedError before any heavy import, so the
    # "no model yet" path works even when torch isn't installed.
    model, tokenizer, labels = load_model(model_dir)
    import torch
    inputs = tokenizer(
        snippet, return_tensors="pt", truncation=True,
        padding="max_length", max_length=128,
    )
    with torch.no_grad():
        logits = model(**inputs).logits
    probs = torch.softmax(logits, dim=-1)[0]
    idx = int(torch.argmax(probs))
    return labels[idx], float(probs[idx])


if __name__ == "__main__":
    # Tiny smoke test (requires a trained model in model/).
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
