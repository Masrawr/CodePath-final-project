"""
Guardrails — screen input before it reaches the AI, and screen output before
it reaches the user.

This is one of the "checker" components in the architecture diagram: it is
where testing/validation protects the system from bad or malicious input.
"""


def validate_input(code: str) -> tuple[bool, str | None]:
    """
    Check that `code` is something we should analyze.

    Returns (ok, error_message). Should reject: empty input, non-Python text,
    and obvious prompt-injection attempts ("ignore previous instructions", etc.).
    """
    ...  # to be implemented


def is_probably_python(code: str) -> bool:
    """Cheap heuristic / AST parse to decide whether the input is Python."""
    ...  # to be implemented
