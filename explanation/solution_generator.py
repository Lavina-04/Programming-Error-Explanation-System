from explanation.autofix import AutoFixer
from explanation.context import build_context
from explanation.explanation_engine import render
from explanation.knowledge_base import lookup


class SolutionGenerator:
    """Optional correction guidance. Corrected code is only returned when the
    real compiler/interpreter confirms that the original error is gone."""

    def __init__(self, analyzer=None):
        self.autofixer = AutoFixer(analyzer) if analyzer else None

    def generate(self, result, code=None, language=None, stdin_text=""):
        error = result.get("error")

        if result.get("status") == "logical_error":
            return {
                "type": "guidance",
                "solution": ("Review your algorithm and compare intermediate calculations with "
                             "the expected result. The complete correction depends on the original problem."),
                "alternatives": [],
                "corrected_code": None,
            }
        if not error:
            return {"type": "guidance", "solution": "No runtime or syntax correction was identified.",
                    "alternatives": [], "corrected_code": None}

        ctx = build_context(error, code or "", language or error.language)
        _, entry = lookup(error.error_name)
        fixes = [render(f, ctx) for f in entry["fixes"]]
        solution = fixes[0]
        if ctx.get("specific") and error.error_name in ("IndexError", "ArrayIndexOutOfBoundsException",
                                                         "ArrayOutOfBounds"):
            solution = fixes[0]
        response = {
            "type": "guidance",
            "solution": solution,
            "approach": render(entry["approach"], ctx),
            "alternatives": fixes[1:],
            "corrected_code": None,
        }

        if self.autofixer and code:
            fix = self.autofixer.suggest(language or error.language, code, result, stdin_text)
            if fix:
                response["type"] = "verified_fix"
                response.update(fix)
                response["note"] = ("This is one possible correction. It was checked by running the "
                                    "code again, but make sure you understand why it works.")
        return response
