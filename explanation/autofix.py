"""Generates candidate corrections for a few well-understood mistakes and keeps
only those that the real compiler/interpreter confirms. Nothing is suggested
as 'verified' unless the original error actually disappears."""
import re

from explanation.context import build_context


class AutoFixer:
    def __init__(self, analyzer):
        self.analyzer = analyzer

    @staticmethod
    def _replace(lines, number, text):
        copy = list(lines)
        copy[number - 1] = text
        return "\n".join(copy)

    def _candidates(self, language, code, error, ctx):
        lines = code.split("\n")
        n, name, message = error.line_number, error.error_name, error.message or ""
        if not n or n > len(lines):
            if name == "MissingClosingBrace":
                yield ("Add the missing closing brace at the end of the file",
                       code.rstrip("\n") + "\n}\n", len(lines))
            return

        if name == "MissingSemicolon" and language in ("Java", "C", "C++"):
            for i in (n, n - 1):
                if i >= 1 and lines[i - 1].strip():
                    text = lines[i - 1].rstrip()
                    if not text.endswith((";", "{", "}")):
                        yield (f"Add a semicolon at the end of line {i}",
                               self._replace(lines, i, text + ";"), i)
        elif name == "MissingClosingBrace":
            yield ("Add the missing closing brace at the end of the file",
                   code.rstrip("\n") + "\n}\n", len(lines))
        elif language == "Python" and name == "SyntaxError":
            if "expected ':'" in message:
                yield (f"Add a colon at the end of line {n}",
                       self._replace(lines, n, lines[n - 1].rstrip() + ":"), n)
            if "Missing parentheses in call to 'print'" in message:
                match = re.match(r"^(\s*)print\s+(.+?)\s*$", lines[n - 1])
                if match:
                    yield ("Put the printed value in parentheses",
                           self._replace(lines, n, f"{match[1]}print({match[2]})"), n)
        elif language == "Python" and name == "IndentationError":
            previous = next((l for l in reversed(lines[:n - 1]) if l.strip()), "")
            base = len(previous) - len(previous.lstrip())
            if "expected an indented block" in message:
                indent = base + 4
            elif "unexpected indent" in message:
                indent = base
            else:
                return
            yield (f"Set the indentation of line {n} to {indent} spaces",
                   self._replace(lines, n, " " * indent + lines[n - 1].lstrip()), n)
        elif name in ("NameError", "UndeclaredIdentifier") and ctx.get("suggestion"):
            wrong, right = ctx["ident"], ctx["suggestion"]
            fixed = re.sub(rf"\b{re.escape(wrong)}\b", right, lines[n - 1])
            if fixed != lines[n - 1]:
                yield (f"Use `{right}` instead of `{wrong}` on line {n}",
                       self._replace(lines, n, fixed), n)
        elif name == "IndexError" and ctx.get("index_info"):
            list_name, index, length = ctx["index_info"]
            fixed = re.sub(rf"\b{re.escape(list_name)}\s*\[\s*{re.escape(str(index))}\s*\]",
                           f"{list_name}[{length - 1}]", lines[n - 1])
            if fixed != lines[n - 1]:
                yield (f"Use the last valid index ({length - 1}) on line {n}",
                       self._replace(lines, n, fixed), n)

    @staticmethod
    def _progress(check, error):
        found = check.get("error")
        if found is None:
            return check.get("status") in ("correct", "logical_error")
        if found.phase != error.phase:
            return True
        return (found.line_number is not None and error.line_number is not None
                and found.line_number > error.line_number)

    def suggest(self, language, code, result, stdin_text=""):
        error = result.get("error")
        if error is None or result.get("status") != "error":
            return None
        ctx = build_context(error, code, language)
        for description, new_code, line in self._candidates(language, code, error, ctx):
            check = self.analyzer.analyze(language, new_code, None, stdin_text)
            if check.get("status") in ("unavailable", "unsupported"):
                return None
            if self._progress(check, error):
                before = code.split("\n")[line - 1] if line <= len(code.split("\n")) else ""
                after = new_code.split("\n")[line - 1] if line <= len(new_code.split("\n")) else ""
                remaining = check.get("error")
                return {
                    "description": description,
                    "corrected_code": new_code,
                    "changed_line": line,
                    "before": before.strip(),
                    "after": after.strip(),
                    "verified": True,
                    "remaining_issue": (
                        f"{remaining.error_name} on line {remaining.line_number}"
                        if remaining else None),
                }
        return None
