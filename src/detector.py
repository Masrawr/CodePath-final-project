"""
Detector — the reasoning component (Module 3-4).

Sends the user's code plus retrieved bug-pattern context to Claude and returns
a STRUCTURED bug report (validated JSON), not free-form prose.
"""


def detect_bugs(code: str, context: list[str]) -> list[dict]:
    """
    Ask Claude to find bugs in `code`, guided by retrieved `context`.

    Returns a list of findings, each like:
        {"line": int, "category": str, "explanation": str, "suggested_fix": str}
    """
    ...  # to be implemented
