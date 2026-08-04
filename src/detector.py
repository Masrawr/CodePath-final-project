"""
Detector — the reasoning component (Module 3-4).

Sends the user's code plus retrieved bug-pattern context to Google's Gemini and
returns a STRUCTURED bug report (validated JSON), not free-form prose.

Configuration (environment variables):
    GEMINI_API_KEY   required to make a live call
    GEMINI_MODEL     optional, defaults to "gemini-flash-lite-latest"

The heavy SDK import and the API-key check happen lazily, so the rest of the app
(and offline tests of `_parse_findings`) work without the key or the library.
"""

import json
import os
import re

MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-lite-latest")

CATEGORIES = [
    "state_bug",
    "logic_inverted",
    "missing_validation",
    "off_by_one",
    "dead_control",
    "clean",
]

_SYSTEM = (
    "You are a careful Python code reviewer. You find real bugs only — do not "
    "invent problems. Use the provided bug-pattern reference to ground your "
    "reasoning. Respond with ONLY a JSON array (no prose, no markdown fences)."
)

_PROMPT = """\
Analyze the Python code below for bugs.

Relevant bug patterns (retrieved from a knowledge base):
{context}

Code to analyze:
```python
{code}
```

Return a JSON array. Each element is an object with exactly these keys:
  "line": integer (1-based line number in the code above; best estimate)
  "category": one of {categories}
  "explanation": a short plain-English description of the bug
  "suggested_fix": a concrete one-line description of how to fix it

If the code has no bugs, return an empty array []."""


class ApiKeyMissingError(RuntimeError):
    """Raised when detect_bugs() is called without GEMINI_API_KEY set."""


def _build_prompt(code: str, context: list[str]) -> str:
    ctx = "\n\n".join(f"- {c}" for c in context) if context else "(none)"
    return _PROMPT.format(context=ctx, code=code, categories=CATEGORIES)


def _parse_findings(text: str) -> list[dict]:
    """Parse the model's response text into a validated list of findings.

    Tolerates markdown code fences and stray prose around the JSON. Drops any
    element that is missing keys or uses an unknown category. Pure function —
    unit-testable without any API call.
    """
    if not text:
        return []

    # Strip ```json ... ``` fences if the model added them anyway.
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)

    # Fall back to the outermost [ ... ] if there is surrounding prose.
    if not text.lstrip().startswith("["):
        bracket = re.search(r"\[.*\]", text, re.DOTALL)
        if bracket:
            text = bracket.group(0)

    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        return []
    if not isinstance(data, list):
        return []

    findings = []
    for item in data:
        if not isinstance(item, dict):
            continue
        category = item.get("category")
        if category not in CATEGORIES:
            continue
        try:
            line = int(item.get("line", 0))
        except (ValueError, TypeError):
            line = 0
        findings.append({
            "line": line,
            "category": category,
            "explanation": str(item.get("explanation", "")).strip(),
            "suggested_fix": str(item.get("suggested_fix", "")).strip(),
        })
    return findings


def detect_bugs(code: str, context: list[str], model: str = MODEL) -> list[dict]:
    """
    Ask Gemini to find bugs in `code`, guided by retrieved `context`.

    Returns a list of findings, each like:
        {"line": int, "category": str, "explanation": str, "suggested_fix": str}

    Raises ApiKeyMissingError if GEMINI_API_KEY is not set.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ApiKeyMissingError(
            "GEMINI_API_KEY is not set. Export it before running the detector: "
            "export GEMINI_API_KEY='your-key-here'"
        )

    # Lazy import so the SDK is only required when a live call is made.
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=_build_prompt(code, context),
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM,
            response_mime_type="application/json",
            temperature=0,
        ),
    )
    return _parse_findings(response.text)


if __name__ == "__main__":
    from src.retriever import retrieve

    demo = (
        "def check_guess(guess, secret):\n"
        "    if guess > secret:\n"
        "        return 'Too Low'\n"
        "    return 'Too High'"
    )
    try:
        findings = detect_bugs(demo, retrieve(demo, k=3))
        print(json.dumps(findings, indent=2))
    except ApiKeyMissingError as e:
        print(e)
