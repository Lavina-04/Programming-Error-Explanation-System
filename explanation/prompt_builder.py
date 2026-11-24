class PromptBuilder:
    """Collects only verified facts, so a future AI explanation can be checked
    against the real compiler/interpreter result."""

    def build(self, result, language, code):
        error = result.get("error")
        if error:
            return {
                "language": language,
                "code": code,
                "status": result.get("status"),
                "error_name": error.error_name,
                "error_message": error.message,
                "original_message": error.raw_message,
                "line_number": error.line_number,
                "error_line": error.code,
                "category": error.category
            }
        return {
            "language": language,
            "code": code,
            "status": result.get("status"),
            "actual_output": result.get("output", ""),
            "expected_output": result.get("expected_output")
        }
