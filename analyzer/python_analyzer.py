import re
import sys

from analyzer.base_analyzer import BaseAnalyzer
from execution.sandbox import run_limited, workspace
from models.error import ErrorInfo

FRAME = re.compile(r'File "(?:.*[\\/])?student\.py", line (\d+)')
EXCEPTION_LINE = re.compile(r"^([A-Za-z_][\w.]*)(?::\s*(.*))?$")
TIME_LIMIT_SECONDS = 5


class PythonAnalyzer(BaseAnalyzer):
    language = "Python"
    extension = ".py"

    def execute(self, code, stdin_text=""):
        # Syntax is checked in-process with compile(), which never runs the code.
        try:
            compile(code, "student.py", "exec")
        except SyntaxError as error:
            line = error.lineno
            name = type(error).__name__
            return {
                "output": "", "warnings": [], "unavailable": None,
                "error": ErrorInfo(
                    language="Python", category="Syntax Error", error_name=name,
                    message=str(error.msg), line_number=line,
                    code=self.source_line(code, line),
                    raw_message=f"{name}: {error.msg} (line {line})",
                    column=error.offset, phase="compile"
                )
            }
        except (ValueError, RecursionError, MemoryError) as error:
            return {
                "output": "", "warnings": [], "unavailable": None,
                "error": ErrorInfo(
                    "Python", "Syntax Error", "SyntaxError", str(error),
                    raw_message=str(error), phase="compile"
                )
            }

        # Execution happens in a separate, limited process - never via exec().
        with workspace() as folder:
            (folder / "student.py").write_text(code, encoding="utf-8")
            run = run_limited(
                [sys.executable, "-I", "-B", "student.py"], folder,
                timeout=TIME_LIMIT_SECONDS, stdin_text=stdin_text, memory_mb=512
            )

        output = run.stdout.strip()
        if run.timed_out:
            return {"output": output, "warnings": [], "unavailable": None,
                    "error": ErrorInfo(
                        "Python", "Time Limit Error", "TimeLimitExceeded",
                        f"The program ran for more than {TIME_LIMIT_SECONDS} seconds and was stopped.",
                        phase="runtime")}

        error = self._parse_traceback(run.stderr, code)
        return {"output": output, "error": error, "warnings": [],
                "unavailable": None}

    def _parse_traceback(self, stderr, code):
        lines = stderr.strip().splitlines()
        if not any(line.startswith("Traceback (most recent call last)") for line in lines):
            return None
        frames = [int(m.group(1)) for line in lines for m in [FRAME.search(line)] if m]
        last = next(
            (line for line in reversed(lines)
             if line.strip() and not line.startswith((" ", "\t"))), ""
        )
        match = EXCEPTION_LINE.match(last)
        if not match:
            return None
        name = match.group(1).split(".")[-1]
        message = match.group(2) or name
        line = frames[-1] if frames else None
        return ErrorInfo(
            language="Python", category="Runtime Error", error_name=name,
            message=message, line_number=line, code=self.source_line(code, line),
            raw_message=last, phase="runtime"
        )
