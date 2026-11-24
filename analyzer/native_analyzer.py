"""Shared implementation for the C (gcc) and C++ (g++) analyzers."""
import os
import re
import sys

from analyzer.base_analyzer import BaseAnalyzer
from classifier.compiler_patterns import match_compiler_message
from execution.sandbox import IS_WINDOWS, find_tool, run_limited, workspace
from models.error import ErrorInfo

DIAGNOSTIC = re.compile(
    r"^(?P<file>[^\s:]+):(?P<line>\d+):(?:(?P<col>\d+):)?\s*"
    r"(?P<sev>fatal error|error|warning|note):\s*(?P<msg>.*)$"
)
SKIP_LINE = re.compile(r"^(\S+: (In|At top level)|In file included from|compilation terminated)")
SANITIZER_FLAGS = ["-fsanitize=address,undefined", "-fno-omit-frame-pointer"]
SANITIZER_ENV = {
    "ASAN_OPTIONS": "detect_leaks=0:hard_rss_limit_mb=256:color=never",
    "UBSAN_OPTIONS": "print_stacktrace=0:color=never",
}
COMPILE_TIMEOUT = 20
RUN_TIMEOUT = 5

ASAN_NAMES = {
    "heap-buffer-overflow": "HeapBufferOverflow",
    "stack-buffer-overflow": "StackBufferOverflow",
    "global-buffer-overflow": "GlobalBufferOverflow",
    "heap-use-after-free": "HeapUseAfterFree",
    "stack-use-after-scope": "StackUseAfterScope",
    "stack-use-after-return": "StackUseAfterScope",
    "stack-overflow": "StackOverflow",
    "SEGV": "SegmentationFault",
    "FPE": "DivisionByZero",
    "bad-free": "InvalidFree",
    "ABRT": "ProgramError",
}
SIGNALS = {
    -11: ("SegmentationFault", "The program crashed with a segmentation fault (SIGSEGV)."),
    -6: ("ProgramError", "The program was aborted (SIGABRT)."),
    -8: ("DivisionByZero", "The program crashed with an arithmetic error (SIGFPE), often division by zero."),
    -7: ("SegmentationFault", "The program crashed with a bus error (SIGBUS)."),
    -9: ("MemoryError", "The program was killed, usually for using too much memory."),
    -24: ("TimeLimitExceeded", "The program used too much CPU time."),
    -25: ("ProgramError", "The program wrote more output than allowed."),
    0xC0000005: ("SegmentationFault", "The program crashed with an access violation."),
    0xC0000094: ("DivisionByZero", "The program crashed: integer division by zero."),
    0xC00000FD: ("StackOverflow", "The program crashed with a stack overflow."),
}
UBSAN_RULES = [
    (r"division by zero", "DivisionByZero"),
    (r"index -?\d+ out of bounds", "ArrayOutOfBounds"),
    (r"signed integer overflow", "SignedIntegerOverflow"),
    (r"null pointer", "NullPointerDereference"),
]


class NativeAnalyzer(BaseAnalyzer):
    compiler_names = []
    language = ""
    source_name = ""
    standard_flag = ""
    family = "C"

    def __init__(self):
        self._compiler = None
        self._found = False
        self._sanitizers = None

    # ---- tool discovery -------------------------------------------------
    def _find(self):
        if not self._found:
            self._found = True
            self._compiler = find_tool(self.compiler_names)
        return self._compiler

    def is_available(self):
        return self._find() is not None

    def availability_note(self):
        name = self.compiler_names[0]
        return (f"{name.upper()} was not found. On Windows install MinGW-w64 "
                f"(for example through MSYS2: pacman -S mingw-w64-ucrt-x86_64-gcc) and add its "
                f"bin folder to PATH; on Ubuntu run: sudo apt install build-essential. "
                f"Restart the backend afterwards.")

    def _sanitizers_work(self):
        """Probe once whether ASan/UBSan can build and run on this machine."""
        if self._sanitizers is None:
            self._sanitizers = False
            if not IS_WINDOWS and not sys.platform == "darwin" and self._find():
                try:
                    with workspace() as folder:
                        (folder / self.source_name).write_text(
                            self.probe_source, encoding="utf-8")
                        build = run_limited(
                            [self._compiler, *SANITIZER_FLAGS, self.source_name, "-o", "probe"],
                            folder, timeout=COMPILE_TIMEOUT, restrict_processes=False,
                            max_file_mb=64)
                        if build.returncode == 0:
                            run = run_limited([str(folder / "probe")], folder, timeout=5,
                                              env_extra=SANITIZER_ENV)
                            self._sanitizers = run.returncode == 0
                except Exception:
                    self._sanitizers = False
        return self._sanitizers

    # ---- compile ---------------------------------------------------------
    @staticmethod
    def _parse_diagnostics(text):
        diagnostics, current = [], None
        for line in text.splitlines():
            if SKIP_LINE.match(line):
                continue
            match = DIAGNOSTIC.match(line)
            if match and match["sev"] != "note":
                current = {
                    "line": int(match["line"]),
                    "column": int(match["col"]) if match["col"] else None,
                    "severity": "error" if "error" in match["sev"] else "warning",
                    "message": match["msg"], "raw": [line],
                }
                diagnostics.append(current)
            elif current is not None:
                current["raw"].append(line)
        return diagnostics

    def _compile_error(self, code, diagnostic):
        message = diagnostic["message"]
        return ErrorInfo(
            self.language, "Compilation Error",
            match_compiler_message(self.family, message), message,
            diagnostic["line"], self.source_line(code, diagnostic["line"]),
            raw_message="\n".join(diagnostic["raw"]).rstrip(),
            column=diagnostic["column"], phase="compile")

    def _link_error(self, code, text):
        match = re.search(r"undefined reference to [`'\u2018]([^'\u2019]+)['\u2019]", text)
        if not match:
            return None
        line_match = re.search(rf"{re.escape(self.source_name)}:(\d+)", text)
        line = int(line_match.group(1)) if line_match else None
        symbol = match.group(1)
        return ErrorInfo(
            self.language, "Compilation Error", "UndefinedReference",
            f"undefined reference to '{symbol}'", line, self.source_line(code, line),
            raw_message=text.strip()[:600], phase="compile")

    # ---- main entry ------------------------------------------------------
    def execute(self, code, stdin_text=""):
        if not self.is_available():
            return self.unavailable()
        sanitized = self._sanitizers_work()
        executable = "program.exe" if IS_WINDOWS else "program"

        with workspace() as folder:
            (folder / self.source_name).write_text(code, encoding="utf-8")
            command = [self._compiler, "-g", "-Wall", "-Wextra", self.standard_flag,
                       "-fno-diagnostics-show-caret"]
            if sanitized:
                command += SANITIZER_FLAGS
            command += [self.source_name, "-o", executable, "-lm"]
            build = run_limited(command, folder, timeout=COMPILE_TIMEOUT,
                                restrict_processes=False, max_file_mb=64)
            if build.timed_out:
                return {"output": "", "warnings": [], "unavailable": None,
                        "error": ErrorInfo(self.language, "Time Limit Error",
                                           "TimeLimitExceeded", "Compilation took too long.",
                                           phase="compile")}

            diagnostics = self._parse_diagnostics(build.stderr + build.stdout)
            errors = [d for d in diagnostics if d["severity"] == "error"]
            warnings = [{"line": d["line"], "message": d["message"],
                         "raw": "\n".join(d["raw"]).rstrip(),
                         "name": match_compiler_message(self.family, d["message"])}
                        for d in diagnostics if d["severity"] == "warning"]

            if build.returncode != 0:
                error = (self._compile_error(code, errors[0]) if errors
                         else self._link_error(code, build.stderr))
                if error is None:
                    text = (build.stderr or build.stdout).strip()
                    error = ErrorInfo(self.language, "Compilation Error", "CompilationError",
                                      text[:300] or "Compilation failed.", raw_message=text,
                                      phase="compile")
                return {"output": "", "warnings": warnings, "unavailable": None,
                        "error": error}

            run = run_limited(
                [str(folder / executable)], folder, timeout=RUN_TIMEOUT,
                stdin_text=stdin_text,
                memory_mb=None if sanitized else 256,
                env_extra=SANITIZER_ENV if sanitized else None)

        output = run.stdout.strip()
        if run.timed_out:
            error = ErrorInfo(self.language, "Time Limit Error", "TimeLimitExceeded",
                              f"The program ran for more than {RUN_TIMEOUT} seconds and was stopped.",
                              phase="runtime")
        else:
            error = self._parse_runtime(run, code)
        return {"output": output, "warnings": warnings, "unavailable": None,
                "error": error}

    # ---- runtime ---------------------------------------------------------
    def _student_line(self, text):
        pattern = rf"#\d+ 0x[0-9a-f]+ in .*? \S*{re.escape(self.source_name)}:(\d+)"
        match = re.search(pattern, text)
        return int(match.group(1)) if match else None

    def _parse_runtime(self, run, code):
        err = run.stderr

        ub = re.search(
            rf"{re.escape(self.source_name)}:(\d+):(\d+): runtime error: (.*)", err)
        if ub:
            line, column, message = int(ub.group(1)), int(ub.group(2)), ub.group(3)
            name = next((n for p, n in UBSAN_RULES if re.search(p, message)),
                        "UndefinedBehavior")
            return ErrorInfo(self.language, "Runtime Error", name, message, line,
                             self.source_line(code, line), raw_message=ub.group(0),
                             column=column, phase="runtime")

        asan = re.search(r"==\d+==ERROR: AddressSanitizer: (.*)", err)
        if asan:
            headline = asan.group(1).strip()
            kind = re.match(r"[\w-]+", headline).group(0) if re.match(r"[\w-]+", headline) else ""
            if "double-free" in headline:
                name = "DoubleFree"
            elif "rss limit" in headline or "out of memory" in headline.lower():
                name = "MemoryError"
            elif kind == "SEGV" and "zero page" in err:
                name = "NullPointerDereference"
            else:
                name = ASAN_NAMES.get(kind, "ProgramError")
            line = self._student_line(err)
            summary = re.search(r"SUMMARY: AddressSanitizer: .*", err)
            access = re.search(r"^(READ|WRITE) of size \d+.*$", err, re.M)
            raw = "\n".join(x for x in (asan.group(0), access.group(0) if access else None,
                                        summary.group(0) if summary else None) if x)
            message = headline + (f" ({access.group(1).lower()} access)" if access else "")
            return ErrorInfo(self.language, "Memory Error" if "Buffer" in name or "Free" in name
                             else "Runtime Error", name, message, line,
                             self.source_line(code, line), raw_message=raw,
                             phase="runtime")

        terminate = re.search(
            r"terminate called after throwing an instance of '([^']+)'\s*(?:what\(\):\s*(.*))?",
            err)
        if terminate:
            kind = terminate.group(1)
            what = terminate.group(2) or ""
            return ErrorInfo(self.language, "Runtime Error", "UncaughtException",
                             f"{kind}: {what}".strip(": "), raw_message=terminate.group(0).strip(),
                             phase="runtime")

        code_value = run.returncode
        if code_value is not None and code_value != 0:
            key = code_value if code_value < 0 else code_value
            if key in SIGNALS:
                name, text = SIGNALS[key]
                return ErrorInfo(self.language, "Runtime Error", name, text,
                                 raw_message=f"{text} (exit status {code_value})",
                                 phase="runtime")
        return None


class CAnalyzer(NativeAnalyzer):
    language = "C"
    extension = ".c"
    compiler_names = ["gcc"]
    source_name = "main.c"
    standard_flag = "-std=gnu11"
    family = "C"
    probe_source = "int main(void){return 0;}\n"


class CppAnalyzer(NativeAnalyzer):
    language = "C++"
    extension = ".cpp"
    compiler_names = ["g++"]
    source_name = "main.cpp"
    standard_flag = "-std=c++17"
    family = "C++"
    probe_source = "int main(){return 0;}\n"
