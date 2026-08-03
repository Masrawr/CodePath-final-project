"""
Glitch Investigator AI — main Streamlit app.

Paste Python code (defaults to a buggy snippet from the guessing game) and the
system runs the full pipeline:

    input -> guardrails -> retriever -> classifier -> detector -> verifier -> report

Run with:  python -m streamlit run investigator.py
"""

import os

import streamlit as st

from src.guardrails import validate_input
from src.retriever import retrieve
from src.detector import detect_bugs, ApiKeyMissingError
from src.classifier import classify, ModelNotTrainedError
from src.verifier import verify_fix

# A compact demo snippet carrying two of the original game's real bugs:
# inverted higher/lower logic AND a Streamlit state reset.
DEMO_CODE = """\
if "secret" not in st.session_state:
    st.session_state.secret = random.randint(1, 100)
secret = random.randint(1, 100)

def check_guess(guess, secret):
    if guess == secret:
        return "Win"
    if guess > secret:
        return "Too Low"
    return "Too High"
"""

CATEGORY_EMOJI = {
    "state_bug": "🔄",
    "logic_inverted": "🔀",
    "missing_validation": "🚧",
    "off_by_one": "➕",
    "dead_control": "🔌",
    "clean": "✅",
}


def render_finding(idx, finding, code, run_verify):
    """Render one detector finding, optionally with a verification result."""
    cat = finding["category"]
    emoji = CATEGORY_EMOJI.get(cat, "🐞")
    with st.container(border=True):
        st.markdown(f"**{emoji} Bug {idx} — `{cat}` (line {finding['line']})**")
        st.write(finding["explanation"])
        st.markdown(f"**Suggested fix:** {finding['suggested_fix']}")

        if run_verify:
            with st.spinner("Verifying the fix (re-detection)…"):
                try:
                    result = verify_fix(code, finding)
                except ApiKeyMissingError as e:
                    st.warning(str(e))
                    return
            if result["fixed"]:
                st.success(f"✅ Verified: {result['details']}")
            else:
                st.error(f"❌ Not verified: {result['details']}")
            with st.expander("Show corrected code"):
                st.code(result["fixed_code"], language="python")


def render_classifier(code):
    """Show the fine-tuned classifier's snippet-level second opinion."""
    st.subheader("🎯 Specialized classifier (second opinion)")
    try:
        label, conf = classify(code)
    except ModelNotTrainedError as e:
        st.info(f"Classifier unavailable — {e}")
        return None
    emoji = CATEGORY_EMOJI.get(label, "🐞")
    st.metric("Predicted category", f"{emoji} {label}", f"{conf:.0%} confidence")
    return label


def main():
    st.set_page_config(page_title="Glitch Investigator AI", page_icon="🕵️")
    st.title("🕵️ Glitch Investigator AI")
    st.caption("Paste Python code and let the AI find, classify, and explain the bugs.")

    # --- Sidebar controls ---
    st.sidebar.header("Settings")
    has_key = bool(os.environ.get("GEMINI_API_KEY"))
    st.sidebar.write("Gemini API key: " + ("✅ set" if has_key else "❌ not set"))
    if not has_key:
        st.sidebar.caption("Set GEMINI_API_KEY to enable bug detection.")
    k = st.sidebar.slider("Retrieved patterns (k)", 1, 5, 3)
    show_context = st.sidebar.checkbox("Show retrieved patterns", value=True)
    use_classifier = st.sidebar.checkbox("Run specialized classifier", value=True)
    run_verify = st.sidebar.checkbox("Verify fixes (extra API calls)", value=False)

    # --- Input ---
    code = st.text_area("Python code to investigate:", value=DEMO_CODE, height=280)
    investigate = st.button("🔍 Investigate", type="primary")

    if not investigate:
        return

    # --- Guardrails ---
    ok, err = validate_input(code)
    if not ok:
        st.error(f"⛔ {err}")
        return

    # --- Retrieval (RAG) ---
    patterns = retrieve(code, k=k)
    if show_context:
        with st.expander(f"🔎 Retrieved {len(patterns)} bug pattern(s)"):
            for p in patterns:
                st.markdown(f"- {p.splitlines()[0]}")

    # --- Classifier (second opinion) ---
    clf_label = render_classifier(code) if use_classifier else None

    # --- Detector (Gemini) ---
    st.subheader("🐞 Detected bugs")
    if not has_key:
        st.warning("Set GEMINI_API_KEY to run bug detection.")
        return
    try:
        with st.spinner("Asking Gemini to analyze the code…"):
            findings = detect_bugs(code, patterns)
    except ApiKeyMissingError as e:
        st.warning(str(e))
        return

    if not findings:
        st.success("No bugs detected. 🎉")
        return

    for i, finding in enumerate(findings, 1):
        render_finding(i, finding, code, run_verify)

    # --- Cross-check the two models ---
    if clf_label is not None:
        detector_cats = {f["category"] for f in findings}
        if clf_label in detector_cats:
            st.info(f"🤝 Classifier and detector agree that a `{clf_label}` bug is present.")
        elif clf_label == "clean":
            st.warning("⚠️ Classifier thinks the snippet is clean, but the detector found bugs.")
        else:
            st.warning(
                f"⚠️ Models disagree: classifier says `{clf_label}`, "
                f"detector reported {sorted(detector_cats)}."
            )


if __name__ == "__main__":
    main()
