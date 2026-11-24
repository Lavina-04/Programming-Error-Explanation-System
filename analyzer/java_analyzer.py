import os
import re
import subprocess

from analyzer.base_analyzer import BaseAnalyzer
from classifier.compiler_patterns import match_compiler_message
from execution.sandbox import find_tool, run_limited, workspace
from models.error import ErrorInfo

PUBLIC_CLASS = re.compile(
    r"\bpublic\s+(?:final\s+|abstract\s+)*(?:class|interface|enum|record)\s+([A-Za-z_]\w*)"
)
DIAGNOSTIC = re.compile(
    r"^(?P<file>[\w$.-]+\.java):(?P<line>\d+): (?P<sev>error|warning): (?P<msg>.*)$"
)
EXCEPTION = re.compile(r'Exception in thread "[^"]*" ([\w.$]+)(?:: (.*))?')
STACK_FRAME = re.compile(r"\bat [\w.$<>]+\((\w+)\.java:(\d+)\)")
COMPILE_TIMEOUT = 20
RUN_TIMEOUT = 8


class JavaAnalyzer(BaseAnalyzer):
    language = "Java"
    extension = ".java"

    def __init__(self):
        self._compiler = None
        self._java = None
        self._probed = False

    # ---- tool discovery -------------------------------------------------
    def _probe(self):
        if self._probed:
            return
        self._probed = True
        home = os.environ.get("JAVA_HOME")
        extra = [os.path.join(home, "bin")] if home else []
        self._java = find_tool(["java"], extra)
        javac = find_tool(["javac"], extra)
        if javac:
            self._compiler = [javac, "-J-Duser.language=en"]
        elif self._java:
            # A JDK without a javac launcher on PATH still ships the compiler module.
            try:
                modules = subprocess.run(
                    [self._java, "--list-modules"], capture_output=True,
                    text=True, timeout=10
                ).stdout
                if "jdk.compiler" in modules:
                    self._compiler = [self._java, "-Duser.language=en", "-m",
                                      "jdk.compiler/com.sun.tools.javac.Main"]
            except Exception:
                pass

    def is_available(self):
        self._probe()
        return bool(self._compiler and self._java)

    def availability_note(self):
        return ("Java JDK not found. Install JDK 17 or newer and make sure `javac` "
                "and `java` are on your PATH (or set JAVA_HOME), then restart the backend.")

    # ---- helpers ---------------------------------------------------------
    @staticmethod
    def _entry_class(code):
        public = PUBLIC_CLASS.search(code)
        if public:
            return public.group(1)
        classes = list(re.finditer(r"\bclass\s+([A-Za-z_]\w*)", code))
        main = re.search(r"static\s+void\s+main\s*\(", code)
        if main:
            before = [c for c in classes if c.start() < main.start()]
            if before:
                return before[-1].group(1)
        return classes[0].group(1) if classes else "Main"

    @staticmethod
    def _parse_compile(text):
        diagnostics, current = [], None
        for line in text.splitlines():
            match = DIAGNOSTIC.match(line)
            if match:
                current = {"line": int(match["line"]), "severity": match["sev"],
                           "message": match["msg"], "raw": [line], "column": None}
                diagnostics.append(current)
            elif current is not None and not re.match(r"^\d+ (errors?|warnings?)$", line.strip()):
                current["raw"].append(line)
                if line.strip() == "^" or line.strip().startswith("^"):
                    current["column"] = len(line) - len(line.lstrip()) + 1
        return diagnostics

    # ---- main entry ------------------------------------------------------
    def execute(self, code, stdin_text=""):
        if not self.is_available():
            return self.unavailable()

        class_name = self._entry_class(code)
        with workspace() as folder:
            source = folder / f"{class_name}.java"
            source.write_text(code, encoding="utf-8")

            compile_run = run_limited(
                self._compiler + ["-g", "-encoding", "UTF-8", source.name], folder,
                timeout=COMPILE_TIMEOUT, restrict_processes=False,
                isolate_network=True, max_file_mb=64
            )
            diagnostics = self._parse_compile(compile_run.stderr + compile_run.stdout)
            errors = [d for d in diagnostics if d["severity"] == "error"]
            warnings = [
                {"line": d["line"], "message": d["message"], "raw": "\n".join(d["raw"])}
                for d in diagnostics if d["severity"] == "warning"
            ]

            if compile_run.returncode != 0 or errors:
                if errors:
                    first = errors[0]
                    return {"output": "", "warnings": warnings, "unavailable": None,
                            "error": ErrorInfo(
                                "Java", "Compilation Error",
                                match_compiler_message("Java", first["message"]),
                                first["message"], first["line"],
                                self.source_line(code, first["line"]),
                                raw_message="\n".join(first["raw"]).rstrip(),
                                column=first["column"], phase="compile")}
                text = (compile_run.stderr or compile_run.stdout).strip()
                return {"output": "", "warnings": warnings, "unavailable": None,
                        "error": ErrorInfo("Java", "Compilation Error", "CompilationError",
                                           text[:300] or "javac failed.", raw_message=text,
                                           phase="compile")}

            run = run_limited(
                [self._java, "-Xmx128m", "-Xss1m", "-XX:+UseSerialGC",
                 "-XX:TieredStopAtLevel=1", "-cp", str(folder), class_name],
                folder, timeout=RUN_TIMEOUT, stdin_text=stdin_text,
                restrict_processes=False
            )

        output = run.stdout.strip()
        if run.timed_out:
            return {"output": output, "warnings": warnings, "unavailable": None,
                    "error": ErrorInfo("Java", "Time Limit Error", "TimeLimitExceeded",
                                       f"The program ran for more than {RUN_TIMEOUT} seconds and was stopped.",
                                       phase="runtime")}
        return {"output": output, "warnings": warnings, "unavailable": None,
                "error": self._parse_runtime(run, code, class_name)}

    def _parse_runtime(self, run, code, class_name):
        stderr = run.stderr
        match = EXCEPTION.search(stderr)
        if match:
            name = match.group(1).split(".")[-1].split("$")[-1]
            message = match.group(2) or name
            line = None
            for frame in STACK_FRAME.finditer(stderr):
                if frame.group(1) == class_name:
                    line = int(frame.group(2))
                    break
            raw = stderr.strip().splitlines()
            raw_text = "\n".join(raw[:6])
            return ErrorInfo("Java", "Runtime Error", name, message, line,
                             self.source_line(code, line), raw_message=raw_text,
                             phase="runtime")
        if "Main method not found" in stderr or "main method" in stderr.lower():
            return ErrorInfo("Java", "Compilation Error", "MissingMainMethod",
                             stderr.strip().splitlines()[0], raw_message=stderr.strip(),
                             phase="runtime")
        if run.returncode not in (0, None) and stderr.strip():
            first = stderr.strip().splitlines()[0]
            return ErrorInfo("Java", "Runtime Error", "ProgramError", first,
                             raw_message=stderr.strip()[:500], phase="runtime")
        return None
