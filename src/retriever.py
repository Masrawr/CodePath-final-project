"""
Retriever — the RAG component (Module 3-4).

Splits the bug-pattern "cards" in kb/ into documents, embeds them, and returns
the ones most relevant to a given code snippet so the detector reasons with
concrete prior knowledge instead of guessing from scratch.

Two backends:
  * "tfidf"  (default) — pure-Python TF-IDF cosine similarity. No heavy deps,
               runs anywhere, easy to explain. Good enough for a small KB.
  * "st"     — sentence-transformers embeddings (semantic). Used automatically
               if the library is installed and backend="auto".

Public API:
    build_index(kb_dir="kb", backend="auto")
    retrieve(code, k=3) -> list[str]   # the k most relevant card texts
"""

import math
import os
import re

KB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "kb")

# Module-level cache so the index is built once per process.
_index = None


# --- Parsing the knowledge base ---------------------------------------------

def load_cards(kb_dir: str = KB_DIR) -> list[dict]:
    """Read every .md file in kb_dir and split it into `## ` cards.

    Returns a list of {"title", "text"} dicts. The intro text before the first
    `## ` heading in a file is ignored.
    """
    cards = []
    if not os.path.isdir(kb_dir):
        return cards
    for fname in sorted(os.listdir(kb_dir)):
        if not fname.endswith(".md"):
            continue
        with open(os.path.join(kb_dir, fname), encoding="utf-8") as f:
            content = f.read()
        # Split on level-2 headings; skip the file preamble (chunk 0).
        chunks = re.split(r"^## ", content, flags=re.MULTILINE)
        for chunk in chunks[1:]:
            lines = chunk.strip().splitlines()
            if not lines:
                continue
            title = lines[0].strip()
            body = "\n".join(lines[1:]).strip()
            cards.append({"title": title, "text": f"{title}\n{body}".strip()})
    return cards


# --- Tokenization (shared by the TF-IDF backend) ----------------------------

def _tokenize(text: str) -> list[str]:
    """Lowercase, split on non-word chars, and break identifiers apart.

    `st.session_state` -> ['st', 'session', 'state'];
    `parseGuess` -> ['parse', 'guess']. This helps code tokens line up with the
    plain-English words used in the cards.
    """
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)  # split camelCase
    raw = re.split(r"[^A-Za-z0-9]+", text)
    return [t.lower() for t in raw if t]


# --- TF-IDF backend ---------------------------------------------------------

class _TfidfIndex:
    """Tiny TF-IDF vector-space index over the KB cards."""

    def __init__(self, cards: list[dict]):
        import numpy as np
        self.np = np
        self.cards = cards
        docs = [_tokenize(c["text"]) for c in cards]

        # Document frequency -> idf.
        df = {}
        for toks in docs:
            for term in set(toks):
                df[term] = df.get(term, 0) + 1
        n = max(len(docs), 1)
        self.idf = {t: math.log((1 + n) / (1 + d)) + 1.0 for t, d in df.items()}
        self.vocab = {t: i for i, t in enumerate(sorted(self.idf))}

        self.matrix = np.vstack([self._vec(toks) for toks in docs]) if docs \
            else np.zeros((0, 0))

    def _vec(self, tokens: list[str]):
        np = self.np
        v = np.zeros(len(self.vocab), dtype="float32")
        if not tokens:
            return v
        counts = {}
        for t in tokens:
            counts[t] = counts.get(t, 0) + 1
        for t, c in counts.items():
            j = self.vocab.get(t)
            if j is not None:
                v[j] = (c / len(tokens)) * self.idf[t]
        norm = np.linalg.norm(v)
        return v / norm if norm else v

    def query(self, code: str, k: int) -> list[int]:
        np = self.np
        if self.matrix.shape[0] == 0:
            return []
        q = self._vec(_tokenize(code))
        scores = self.matrix @ q  # cosine similarity (all vectors unit-norm)
        return list(np.argsort(scores)[::-1][:k])


# --- sentence-transformers backend (optional) -------------------------------

class _STIndex:
    """Semantic index using sentence-transformers, if available."""

    def __init__(self, cards: list[dict], model_name="all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        import numpy as np
        self.np = np
        self.cards = cards
        self.model = SentenceTransformer(model_name)
        emb = self.model.encode([c["text"] for c in cards],
                                normalize_embeddings=True)
        self.matrix = np.asarray(emb, dtype="float32")

    def query(self, code: str, k: int) -> list[int]:
        np = self.np
        q = self.model.encode([code], normalize_embeddings=True)[0]
        scores = self.matrix @ np.asarray(q, dtype="float32")
        return list(np.argsort(scores)[::-1][:k])


# --- Public API -------------------------------------------------------------

def build_index(kb_dir: str = KB_DIR, backend: str = "auto"):
    """Load the cards, build the chosen index, and cache it.

    backend: "auto" (use sentence-transformers if installed, else tfidf),
             "st", or "tfidf".
    """
    global _index
    cards = load_cards(kb_dir)

    use_st = backend == "st"
    if backend == "auto":
        try:
            import sentence_transformers  # noqa: F401
            use_st = True
        except Exception:
            use_st = False

    _index = _STIndex(cards) if use_st else _TfidfIndex(cards)
    return _index


def retrieve(code: str, k: int = 3, kb_dir: str = KB_DIR) -> list[str]:
    """Return the k most relevant bug-pattern cards for the given code."""
    global _index
    if _index is None:
        build_index(kb_dir)
    idxs = _index.query(code, k)
    return [_index.cards[i]["text"] for i in idxs]


if __name__ == "__main__":
    demo = (
        "if 'secret' not in st.session_state:\n"
        "    st.session_state.secret = random.randint(1, 100)\n"
        "secret = random.randint(1, 100)"
    )
    print(f"Backend: {type(build_index().__class__).__name__ or ''}")
    for i, card in enumerate(retrieve(demo, k=3), 1):
        print(f"\n--- match {i} ---\n{card.splitlines()[0]}")
