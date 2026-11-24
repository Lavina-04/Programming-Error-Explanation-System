from explanation.context import build_context
from explanation.explanation_engine import render
from explanation.knowledge_base import lookup

LOGICAL_HINTS = [
    "Try calculating the expected result by hand for a small example.",
    "Check the operators and the order of calculations.",
    "Print each intermediate value and compare it with your hand calculation.",
]
GENERIC_HINTS = [
    "Read the explanation carefully.",
    "Trace the code line by line.",
    "Test your code using a small example.",
]


class HintGenerator:
    """Hints get more direct with the level, but never reveal the full code."""

    def generate(self, result, level, code=None):
        if level not in (1, 2, 3):
            return "Invalid hint level."
        error = result.get("error")
        if result.get("status") == "logical_error":
            return LOGICAL_HINTS[level - 1]
        if error:
            ctx = build_context(error, code or "", error.language)
            _, entry = lookup(error.error_name)
            return render(entry["hints"][level - 1], ctx)
        return GENERIC_HINTS[level - 1]
