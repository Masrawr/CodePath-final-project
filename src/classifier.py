"""
Classifier — the ADVANCED FEATURE: a fine-tuned / specialized model.

A small DistilBERT/CodeBERT classifier fine-tuned on data/bugs.csv to tag a
code snippet with a bug category. It gives a second, specialized signal that we
compare against Claude's category (see the evaluator).

Bug taxonomy:
    state_bug, logic_inverted, missing_validation, off_by_one, dead_control, clean
"""

MODEL_DIR = "model"


def load_model(model_dir: str = MODEL_DIR):
    """Load the fine-tuned classifier and tokenizer from disk."""
    ...  # to be implemented


def classify(snippet: str) -> tuple[str, float]:
    """Return (predicted_category, confidence) for a code snippet."""
    ...  # to be implemented
