from abc import ABC, abstractmethod


class BaseAnalyzer(ABC):
    """Every language analyzer returns the same execution dictionary:

    {"output": str, "error": ErrorInfo | None, "warnings": [dict],
     "unavailable": str | None}
    """

    language = ""
    extension = ""

    @abstractmethod
    def execute(self, code, stdin_text=""):
        pass

    def analyze(self, code):
        return self.execute(code)["error"]

    def is_available(self):
        return True

    def availability_note(self):
        return ""

    @staticmethod
    def source_line(code, line_number):
        lines = code.splitlines()
        if line_number and 1 <= line_number <= len(lines):
            return lines[line_number - 1].strip()
        return None

    def unavailable(self):
        return {"output": "", "error": None, "warnings": [],
                "unavailable": self.availability_note()}
