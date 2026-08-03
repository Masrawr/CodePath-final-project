"""
Reliability & guardrail experiments (Module 5).

Structured tests that measure how trustworthy the system is:
  - detection accuracy (precision / recall on known-buggy vs clean snippets)
  - LLM-vs-classifier agreement (do the two models agree on category?)
  - consistency (same input run N times -> how stable are the findings?)
  - guardrail tests (junk input, prompt injection, empty file are refused)
"""


def test_guardrail_rejects_non_python():
    """Non-Python text should be rejected by the guardrail."""
    ...  # to be implemented


def test_guardrail_rejects_prompt_injection():
    """'Ignore previous instructions...' style input should be refused."""
    ...  # to be implemented


def test_detection_recall_on_known_bugs():
    """Injected bugs should be detected at/above a target recall threshold."""
    ...  # to be implemented
