"""
Glitch Investigator AI — main Streamlit app.

Paste Python code (defaults to the buggy guessing game in app.py) and the
system retrieves relevant bug patterns, asks Claude to detect bugs, tags each
with a fine-tuned classifier, verifies suggested fixes, and shows a report.

Pipeline (see diagrams / ai_interactions.md):
    input -> guardrails -> retriever -> detector -> classifier -> verifier -> report

Run with:  python -m streamlit run investigator.py
"""

import streamlit as st

# These imports point at the stub modules created during scaffolding.
# from src.guardrails import validate_input
# from src.retriever import retrieve
# from src.detector import detect_bugs
# from src.classifier import classify
# from src.verifier import verify_fix


def main():
    """Render the Streamlit UI and run the detect->classify->verify pipeline."""
    st.set_page_config(page_title="Glitch Investigator AI", page_icon="🕵️")
    st.title("🕵️ Glitch Investigator AI")
    st.caption("Paste Python code and let the AI find, classify, and explain the bugs.")
    st.info("Scaffold only — pipeline not yet wired up.")
    # TODO: wire up guardrails -> retriever -> detector -> classifier -> verifier


if __name__ == "__main__":
    main()
