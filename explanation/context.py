"""Pulls concrete facts (names, indexes, lengths, types) out of the real error
message and source code, so explanations talk about the student's own code."""
import ast
import difflib
import re

KEYWORDS = {
    "if", "else", "for", "while", "return", "int", "char", "float", "double", "void",
    "class", "public", "private", "static", "def", "import", "from", "print", "true",
    "false", "none", "null", "new", "include", "using", "namespace", "std", "string",
    "long", "short", "break", "continue", "in", "and", "or", "not", "is", "try",
    "except", "catch", "finally", "switch", "case", "struct", "const", "main", "args",
}


def _python_index_info(code, line_number):
    """Return (list_name, index, length) for a constant subscript on the line."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None
    lengths = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, (ast.List, ast.Tuple)):
            if node.lineno <= (line_number or 10 ** 9):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        lengths[target.id] = (node.lineno, len(node.value.elts))
    for node in ast.walk(tree):
        if (isinstance(node, ast.Subscript) and getattr(node, "lineno", None) == line_number
                and isinstance(node.value, ast.Name) and node.value.id in lengths):
            index = node.slice
            value = None
            if isinstance(index, ast.Constant) and isinstance(index.value, int):
                value = index.value
            elif (isinstance(index, ast.UnaryOp) and isinstance(index.op, ast.USub)
                  and isinstance(index.operand, ast.Constant)):
                value = -index.operand.value
            if value is not None:
                length = lengths[node.value.id][1]
                if value >= length or value < -length:
                    return node.value.id, value, length
    return None


def _identifier(error):
    raw = error.raw_message or error.message or ""
    message = error.message or ""
    patterns = [
        r"name '(\w+)' is not defined",
        r"variable '(\w+)'",
        r"'([\w:]+)' (?:undeclared|was not declared|does not name a type|has not been declared)",
        r"symbol:\s+(?:variable|method|class)\s+(\w+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, raw) or re.search(pattern, message)
        if match:
            return match.group(1).split("::")[-1]
    return None


def _suggest(ident, code):
    words = set(re.findall(r"\b[A-Za-z_]\w*\b", code))
    words = {w for w in words if w.lower() not in KEYWORDS and w != ident}
    matches = difflib.get_close_matches(ident, sorted(words), n=1, cutoff=0.75)
    return matches[0] if matches else None


def build_context(error, code, language=None):
    language = language or error.language
    message = error.message or ""
    ctx = {
        "language": language,
        "container": "list" if language == "Python" else "array",
        "a_container": "a list" if language == "Python" else "an array",
        "line": error.line_number,
        "code_line": error.code or "",
        "message": message,
        "ident": "",
        "suggestion": None,
        "specific": None,
        "index_info": None,
    }

    ident = _identifier(error)
    if ident:
        ctx["ident"] = ident
        suggestion = _suggest(ident, code)
        ctx["suggestion"] = suggestion
        ctx["specific"] = f"`{ident}` is not defined at this point."
        if suggestion:
            ctx["specific"] += f" Did you mean `{suggestion}`?"

    name = error.error_name
    if name == "IndexError" and language == "Python":
        info = _python_index_info(code, error.line_number)
        if info:
            ctx["index_info"] = info
            list_name, index, length = info
            plural = "element" if length == 1 else "elements"
            ctx["specific"] = (
                f"Your list `{list_name}` contains {length} {plural}, so the valid indexes are "
                f"0 to {length - 1}. You tried to use index {index}, which does not exist."
            )
    elif name in ("ArrayIndexOutOfBoundsException", "IndexOutOfBoundsException",
                  "StringIndexOutOfBoundsException"):
        match = re.search(r"[Ii]ndex:? (-?\d+),? (?:out of bounds for )?(?:length|size):? (\d+)", message)
        if match:
            index, length = int(match[1]), int(match[2])
            ctx["specific"] = (f"The collection has {length} items, so valid indexes are 0 to "
                               f"{length - 1}. Your code used index {index}.")
    elif name == "ArrayOutOfBounds":
        match = re.search(r"index (-?\d+) out of bounds for type '[^\[']*\[(\d+)\]", message)
        if match:
            index, length = int(match[1]), int(match[2])
            ctx["specific"] = (f"The array has {length} elements, so valid indexes are 0 to "
                               f"{length - 1}. Your code used index {index}.")
    elif name == "KeyError":
        ctx["specific"] = f"The key {message} is not in the dictionary."
    elif name == "ValueError":
        match = re.search(r"invalid literal for int\(\) with base 10: (.+)", message)
        if match:
            ctx["specific"] = f"You tried to convert {match[1]} into a whole number, but it is not made only of digits."
    elif name == "NumberFormatException":
        match = re.search(r'For input string: "(.*)"', message)
        if match:
            ctx["specific"] = f'You tried to convert "{match[1]}" into a number, but it is not a valid number.'
    elif name == "TypeError":
        match = re.search(r"unsupported operand type\(s\) for ([^:]+): '(\w+)' and '(\w+)'", message)
        if match:
            ctx["specific"] = f"The operator `{match[1]}` was used between a {match[2]} and a {match[3]}, which cannot be combined."
        elif "can only concatenate str" in message or "must be str" in message:
            ctx["specific"] = "You tried to join text with a number using `+`. Convert the number with str() first."
    elif name == "TypeMismatch" and language == "Java":
        lossy = re.search(r"possible lossy conversion from (\w+) to (\w+)", message)
        plain = re.search(r"(\S+) cannot be converted to (\S+)", message)
        if lossy:
            ctx["specific"] = f"A {lossy[1]} may lose information when stored in a {lossy[2]}, so Java requires an explicit cast."
        elif plain:
            ctx["specific"] = f"A value of type {plain[1]} was used where {plain[2]} is required."
    elif name == "TypeMismatch":
        match = re.search(r"from '([^']+)' to '([^']+)'", message)
        if match:
            ctx["specific"] = f"A value of type {match[1]} was used where {match[2]} is required."
    return ctx
