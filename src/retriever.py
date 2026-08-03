"""
Retriever — the RAG component (Module 3-4).

Embeds the bug-pattern "cards" in kb/ and returns the ones most relevant to a
given code snippet, so the detector reasons with concrete prior knowledge
instead of guessing from scratch.
"""


def build_index(kb_dir: str = "kb") -> None:
    """Load bug-pattern cards, embed them, and store the vector index."""
    ...  # to be implemented


def retrieve(code: str, k: int = 3) -> list[str]:
    """Return the k most relevant bug-pattern cards for the given code."""
    ...  # to be implemented
