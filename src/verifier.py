"""
Verifier — the agentic self-check (Module 5).

Closes the plan->detect->fix->verify loop using RE-DETECTION: it asks Gemini to
apply the suggested fix, syntax-checks the result, then re-runs the detector on
the corrected code. If the same bug category no longer appears, the fix is
considered successful.

Note (limitation, worth stating in the model card): this grounds verification in
the detector rather than executing tests, so it is the model checking its own
work. It catches fixes that clearly remove the reported bug, but cannot prove
runtime correctness. Both AI calls are injectable so the loop is testable offline.
"""

import ast
import os
import re

MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-lite-latest")

_REWRITE_SYSTEM = (
    "You are a precise code editor. Apply ONLY the requested fix to the code. "
    "Change nothing else. Respond with ONLY the corrected Python code — no "
    "explanation, no markdown fences."
)

_REWRITE_PROMPT = """\
Apply this fix to the code.

Bug: {explanation}
Fix to apply: {suggested_fix}

Code:
```python
{code}
```

Return the full corrected Python code."""


def _strip_code_fences(text: str) -> str:
    """Remove a surrounding ```python ... ``` fence if the model added one."""
    m = re.search(r"```(?:python)?\s*(.*?)```", text, re.DOTALL)
    return (m.group(1) if m else text).strip()


def _same_category_present(findings: list[dict], category: str) -> bool:
    """True if any remaining finding has the given bug category."""
    return any(f.get("category") == category for f in findings)


def _rewrite_with_fix(code: str, finding: dict, model: str = MODEL) -> str:
    """Ask Gemini to apply `finding['suggested_fix']` and return corrected code."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        from src.detector import ApiKeyMissingError
        raise ApiKeyMissingError(
            "GEMINI_API_KEY is not set. Export it before running the verifier."
        )

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    prompt = _REWRITE_PROMPT.format(
        explanation=finding.get("explanation", ""),
        suggested_fix=finding.get("suggested_fix", ""),
        code=code,
    )
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=_REWRITE_SYSTEM, temperature=0,
        ),
    )
    return _strip_code_fences(response.text)


def verify_fix(original_code: str, finding: dict,
               apply_fn=None, detect_fn=None) -> dict:
    """
    Apply `finding["suggested_fix"]` and check whether the bug is gone.

    apply_fn(code, finding) -> corrected_code
    detect_fn(code) -> list[finding]
    Both default to the live Gemini-backed implementations; pass fakes to test
    the loop offline.

    Returns {"fixed": bool, "details": str, "fixed_code": str}.
    """
    if apply_fn is None:
        apply_fn = _rewrite_with_fix
    if detect_fn is None:
        # Imported here to avoid a hard dependency when callers inject fakes.
        from src.detector import detect_bugs
        from src.retriever import retrieve
        detect_fn = lambda code: detect_bugs(code, retrieve(code, k=3))  # noqa: E731

    corrected = apply_fn(original_code, finding)

    # Guard: never accept a "fix" that breaks the code's syntax.
    try:
        ast.parse(corrected)
    except SyntaxError as e:
        return {
            "fixed": False,
            "details": f"The suggested fix produced invalid Python ({e.msg}).",
            "fixed_code": corrected,
        }

    remaining = detect_fn(corrected)
    category = finding.get("category", "")
    if _same_category_present(remaining, category):
        return {
            "fixed": False,
            "details": f"A '{category}' bug is still detected after the fix.",
            "fixed_code": corrected,
        }
    return {
        "fixed": True,
        "details": f"The '{category}' bug is no longer detected after the fix.",
        "fixed_code": corrected,
    }


if __name__ == "__main__":
    from src.detector import ApiKeyMissingError
    from src.retriever import retrieve
    from src.detector import detect_bugs

    demo = (
        "def check_guess(guess, secret):\n"
        "    if guess > secret:\n"
        "        return 'Too Low'\n"
        "    return 'Too High'"
    )
    try:
        finding = detect_bugs(demo, retrieve(demo, k=3))[0]
        print(verify_fix(demo, finding))
    except (ApiKeyMissingError, IndexError) as e:
        print(f"(needs GEMINI_API_KEY for a live run) {e}")
