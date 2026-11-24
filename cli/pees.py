#!/usr/bin/env python3
"""pees - explain programming errors from the terminal.

    python cli/pees.py analyze main.py
    python cli/pees.py analyze Main.java --hint 2 --fix
    python cli/pees.py analyze main.c --expected expected.txt --stdin input.txt

Needs the backend running (python app.py). Uses only the standard library.
Exit codes: 0 = no error found, 1 = error or wrong output found, 2 = usage/connection problem.
"""
import argparse
import json
import os
import sys
import textwrap
import urllib.error
import urllib.request

LANGUAGES = {".py": "Python", ".java": "Java", ".c": "C", ".cpp": "C++", ".cc": "C++", ".cxx": "C++"}
DEFAULT_SERVER = os.environ.get("PEES_SERVER", "http://127.0.0.1:5001")


def request(server, path, body=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        server.rstrip("/") + path, data=data,
        headers={"Content-Type": "application/json"}, method="POST" if body is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        try:
            message = json.loads(error.read().decode("utf-8")).get("error", error.reason)
        except Exception:
            message = error.reason
        raise SystemExit(f"Backend error: {message}")
    except urllib.error.URLError:
        raise SystemExit(f"Cannot reach the backend at {server}. Start it with: python app.py")


def read_text(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    except OSError as error:
        raise SystemExit(f"Cannot read {path}: {error.strerror}")


def wrap(text, indent="  "):
    return textwrap.fill(text, width=78, initial_indent=indent, subsequent_indent=indent)


def show(label, text):
    if text:
        print(f"\n{label}\n{wrap(text)}")


def analyze(args):
    language = args.language or LANGUAGES.get(os.path.splitext(args.file)[1].lower())
    if not language:
        raise SystemExit("Cannot detect the language from the file extension. Use --language.")
    body = {"language": language, "code": read_text(args.file), "skill_level": args.level}
    if args.expected:
        body["expected_output"] = read_text(args.expected)
    if args.stdin:
        body["stdin"] = read_text(args.stdin)

    data = request(args.server, "/api/explain", body)
    if args.json:
        print(json.dumps(data, indent=2))
        return 0 if data["analysis"]["status"] == "correct" else 1

    analysis, explanation = data["analysis"], data["explanation"]
    status = analysis["status"]
    print("Programming Error Explanation System\n")
    print(f"File: {args.file}\nLanguage: {analysis.get('language', language)}")

    if status in ("unsupported", "unavailable"):
        print(f"\n{analysis['message']}")
        return 2
    if status == "correct":
        print("\nNo error found. Your program ran correctly.")
        if analysis.get("actual_output"):
            print("\nOutput:\n" + textwrap.indent(analysis["actual_output"], "  "))
        for warning in explanation.get("warnings", []):
            print(f"  warning (line {warning['line']}): {warning['message']}")
        return 0
    if status == "logical_error":
        print("\nThe program ran, but the output is not what was expected.")
        print("\nYour output:\n" + textwrap.indent(analysis["actual_output"] or "(nothing)", "  "))
        print("\nExpected:\n" + textwrap.indent(analysis["expected_output"], "  "))
        show("Where it first differs:", explanation.get("specific"))
        show("Suggested approach:", explanation.get("approach"))
    else:
        error = analysis["error"]
        print(f"\nError: {error['error_name']} ({error['category']})")
        if error.get("line_number"):
            print(f"Line: {error['line_number']}")
        if error.get("code"):
            print(f"Code: {error['code']}")
        print("\nOriginal message:\n" + textwrap.indent(error.get("raw_message") or error["message"], "  "))
        show("In your code:", explanation.get("specific"))
        show("What happened:", explanation.get("cause"))
        show("Why it happened:", explanation.get("why_it_happened"))
        show("Suggested approach:", explanation.get("approach"))
        show("Think about it:", explanation.get("learning_question"))

    for level in range(1, (args.hint or 0) + 1):
        hint = request(args.server, "/api/hints", {"attempt_id": data["attempt_id"], "level": level})
        show(f"Hint {level}:", hint["hint"])

    if args.fix:
        solution = request(args.server, "/api/solution", {"attempt_id": data["attempt_id"]})["solution"]
        show("Suggested correction:", solution.get("description") or solution["solution"])
        if solution.get("corrected_code"):
            print(f"\n  - line {solution['changed_line']}: {solution['before']}")
            print(f"  + line {solution['changed_line']}: {solution['after']}")
            print(wrap(solution.get("note") or "Verified by running the corrected code again."))
            if args.write:
                with open(args.file, "w", encoding="utf-8") as handle:
                    handle.write(solution["corrected_code"])
                print(f"\n  Corrected code written to {args.file}")
        else:
            show("", solution["solution"])
    elif status == "error":
        print("\nTip: add --hint 1 for a nudge, or --fix for a possible correction.")
    return 1


def main():
    parser = argparse.ArgumentParser(prog="pees", description="Explain programming errors.")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("analyze", help="analyze a source file")
    p.add_argument("file")
    p.add_argument("--language", help="Python, Java, C or C++ (default: from file extension)")
    p.add_argument("--expected", help="file containing the expected output")
    p.add_argument("--stdin", help="file whose contents are given to the program as input")
    p.add_argument("--hint", type=int, choices=(1, 2, 3), help="show hints up to this level")
    p.add_argument("--fix", action="store_true", help="show a possible, verified correction")
    p.add_argument("--write", action="store_true", help="with --fix, overwrite the file with the corrected code")
    p.add_argument("--level", choices=("beginner", "intermediate"), default="beginner")
    p.add_argument("--server", default=DEFAULT_SERVER)
    p.add_argument("--json", action="store_true", help="print the raw JSON response")
    args = parser.parse_args()
    sys.exit(analyze(args))


if __name__ == "__main__":
    main()
