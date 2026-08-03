"""
Verifier — the agentic self-check (Module 5).

Closes the plan->detect->fix->verify loop: applies a suggested fix to a
sandboxed copy of the code, re-runs the tests, and reports whether the bug is
actually gone. This is where the system tests its own AI output.
"""


def verify_fix(original_code: str, finding: dict) -> dict:
    """
    Apply `finding["suggested_fix"]` to a copy of the code, re-run pytest, and
    return {"fixed": bool, "details": str}.
    """
    ...  # to be implemented
