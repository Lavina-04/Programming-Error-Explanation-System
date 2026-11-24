from analyzer.language_manager import LanguageManager
from analyzer.logical_analyzer import LogicalAnalyzer
from classifier.error_classifier import ErrorClassifier


class Analyzer:
    def __init__(self):
        self.language_manager = LanguageManager()
        self.logical_analyzer = LogicalAnalyzer()
        self.error_classifier = ErrorClassifier()

    def analyze(self, language, code, expected_output=None, stdin_text=""):
        language_analyzer = self.language_manager.get_analyzer(language)
        if language_analyzer is None:
            return {
                "status": "unsupported",
                "message": f"Language '{language}' is not supported yet. "
                           f"Supported languages: Python, Java, C, C++.",
                "output": "",
                "actual_output": ""
            }

        execution = language_analyzer.execute(code, stdin_text or "")
        if execution.get("unavailable"):
            return {
                "status": "unavailable",
                "language": language_analyzer.language,
                "message": execution["unavailable"],
                "output": "",
                "actual_output": ""
            }

        actual_output = execution.get("output", "")
        error = execution.get("error")
        warnings = execution.get("warnings", [])

        if error is not None:
            error.category = self.error_classifier.classify(error)
            return {
                "status": "error",
                "language": language_analyzer.language,
                "error": error,
                "warnings": warnings,
                "output": actual_output,
                "actual_output": actual_output
            }

        if expected_output is not None:
            comparison = self.logical_analyzer.compare_outputs(
                actual_output, expected_output
            )
            return {**comparison, "language": language_analyzer.language,
                    "warnings": warnings, "output": actual_output}

        return {
            "status": "correct",
            "language": language_analyzer.language,
            "warnings": warnings,
            "output": actual_output,
            "actual_output": actual_output
        }
