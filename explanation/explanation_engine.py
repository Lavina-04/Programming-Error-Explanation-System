import re

from explanation.ai_service import AIService
from explanation.context import build_context
from explanation.knowledge_base import lookup
from explanation.prompt_builder import PromptBuilder


def render(text, ctx):
    """Fill {placeholders}; unknown or empty values fall back to a neutral word."""
    if not text:
        return text

    def fill(match):
        value = ctx.get(match.group(1))
        return str(value) if value else "that name"
    return re.sub(r"\{(\w+)\}", fill, text)


def first_difference(actual, expected):
    actual_lines, expected_lines = actual.split("\n"), expected.split("\n")
    for index in range(max(len(actual_lines), len(expected_lines))):
        a = actual_lines[index] if index < len(actual_lines) else "(nothing)"
        e = expected_lines[index] if index < len(expected_lines) else "(nothing)"
        if a != e:
            return index + 1, a, e
    return None


class ExplanationEngine:
    def __init__(self):
        self.prompt_builder = PromptBuilder()
        self.ai_service = AIService()

    def explain(self, result, language, code, skill_level="beginner"):
        context = self.prompt_builder.build(result, language, code)
        ai_explanation = self.ai_service.explain(context)
        if ai_explanation:
            return {"source": "ai", "summary": ai_explanation, "verified_facts": context}
        explanation = self.rule_based_explanation(result, language, code, skill_level)
        warnings = result.get("warnings") or []
        if warnings:
            explanation["warnings"] = [
                {"line": w.get("line"), "message": w.get("message")} for w in warnings[:10]
            ]
        return explanation

    def rule_based_explanation(self, result, language=None, code="", skill_level="beginner"):
        status = result.get("status")
        base = {"source": "rules", "skill_level": skill_level}

        if status in ("unsupported", "unavailable"):
            return {**base, "summary": result["message"],
                    "cause": result["message"],
                    "concept": "Language support",
                    "learning_question": "Which programming language did you select?",
                    "next_step": "Choose Python, Java, C or C++ (and check that its compiler is installed)."}

        if status == "correct":
            warned = bool(result.get("warnings"))
            return {**base, "summary": "Your program ran without a detected syntax or runtime error.",
                    "cause": "No execution error was detected.",
                    "concept": "Program execution",
                    "learning_question": "Does the output also match what the problem asks for?",
                    "next_step": ("The compiler also reported warnings. Read them; they often point to real bugs."
                                  if warned else "Compare your output with the problem requirements."),
                    "learning_outcome": "Check results, not just that the program runs."}

        if status == "logical_error":
            actual = result.get("actual_output", "")
            expected = result.get("expected_output", "")
            diff = first_difference(actual, expected)
            specific = None
            if diff:
                line, got, want = diff
                specific = f"Output line {line} is `{got}` but `{want}` was expected."
            return {**base, "summary": "Your program ran, but its output is not the expected one.",
                    "specific": specific,
                    "cause": "The logic or calculation does not match the problem requirements.",
                    "concept": "Algorithmic logic",
                    "detail": "The program has no syntax or runtime error, so the mistake is in the steps it follows.",
                    "why_it_happened": "The program has no syntax or runtime error, so the mistake is in the steps it follows.",
                    "approach": "Trace the program by hand with a small example and find the first step where your value differs.",
                    "learning_question": "At which calculation step does your result first differ?",
                    "next_step": "Trace your program using a small example.",
                    "learning_outcome": "Learn to debug logic by comparing actual and expected results."}

        error = result.get("error")
        if not error:
            return {**base, "summary": "An error occurred.",
                    "cause": "The system could not identify its exact cause.",
                    "concept": "Debugging",
                    "learning_question": "Which line should you inspect first?",
                    "next_step": "Review the error message and source code."}

        ctx = build_context(error, code, language or error.language)
        _, entry = lookup(error.error_name)
        detail = render(entry["detail"], ctx)
        note = (entry.get("notes") or {}).get(ctx["language"])
        if note and skill_level == "beginner":
            detail = f"{detail} {note}"
        elif note:
            detail = note

        cause = render(entry["cause"], ctx)
        where = f" on line {error.line_number}" if error.line_number else ""
        return {
            **base,
            "summary": f"{error.error_name}{where}: {cause}" if error.line_number is None
                       else f"{error.error_name} detected on line {error.line_number}.",
            "error_name": error.error_name,
            "error_category": error.category,
            "language": ctx["language"],
            "line_number": error.line_number,
            "code_line": error.code,
            "original_message": error.raw_message or error.message,
            "specific": ctx["specific"],
            "cause": cause,
            "concept": entry["concept"],
            "detail": detail,
            "why_it_happened": detail,
            "approach": render(entry["approach"], ctx),
            "learning_question": render(entry["question"], ctx),
            "next_step": (f"Inspect this line: {error.code}" if error.code
                          else "Use the error message to decide which part of your program to inspect."),
            "learning_outcome": entry["outcome"],
        }
