# Programming Error Explanation System

A beginner-friendly system that helps students **understand** programming errors in **Python, Java, C and C++** instead of just handing them corrected code.

For every submission it finds the error, normalises it into one common format (keeping the original compiler message), points at the line, explains the concept behind the mistake, offers three levels of hints, and only then offers an optional correction. Corrected code is never shown unless the real compiler/interpreter confirmed that the original error disappeared.

```text
backend (Flask) ← web frontend · terminal CLI · VS Code extension
analyzers → classifier → explanation engine → hints / verified fixes → SQLite learning database
```

## 1. Setup (Windows, PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5001** - the backend serves the web app itself, so there is nothing else to start.

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### Compilers

| Language | Needs | Check |
|---|---|---|
| Python | the Python that runs the backend | built in |
| Java | JDK 17+ (`javac` and `java`) | `javac -version` |
| C | GCC | `gcc --version` |
| C++ | G++ | `g++ --version` |

GCC/G++ on Windows: install MinGW-w64, for example through MSYS2:

```bash
pacman -S mingw-w64-ucrt-x86_64-gcc
```

Add its `bin` folder to PATH. Ubuntu:

```bash
sudo apt install build-essential
```

Restart `python app.py` afterwards.

`GET /api/languages` (and the Home page) show which compilers were found and what to install if one is missing.

**Note:** Python has been tested in the local development environment. Java, C and C++ compiler execution must be verified after installing their respective compilers.

## 2. What it does

- **Analyzers** (`analyzer/`): Python runs in a limited subprocess (no more in-process `exec()`); Java uses `javac` + `java`; C/C++ use `gcc`/`g++`. On Linux/macOS-with-sanitizers, C/C++ programs are built with AddressSanitizer + UBSan so crashes come with a line number and a precise cause (out-of-bounds index, null dereference, use-after-free...). Where sanitizers are unavailable (typically MinGW on Windows) the backend falls back to a plain build and reports crashes from the exit status, without a line number.
- **Common error format** (`models/error.py`, `classifier/`): `language, category, error_name, message, line_number, code, raw_message, column, phase`. Examples: Java `';' expected` and GCC `expected ';' before` both become `MissingSemicolon` / **Syntax Error**; the untouched compiler text stays in `raw_message`.
- **Explanation engine** (`explanation/`): 40 concept groups covering approximately 70 error names, filled in with facts from the student's own code (list length and bad index, "did you mean `count`?", first differing output line...). Beginner / intermediate wording. Rule-based; `ai_service.py` is still the placeholder hook for an LLM, and anything an LLM produces should be checked against the compiler result.
- **Hints before answers:** three progressive levels per error; the web app unlocks "show a possible fix" only after a hint.
- **Verified fixes** (`explanation/autofix.py`): missing semicolon/brace/colon, Python 2 `print`, indentation, misspelled names, index out of range. Each candidate is re-run and only accepted if the original error is gone.
- **Practice:** 8 topics solvable in Python/Java/C/C++, plus 12 "spot the error" exercises. Expected answers stay on the server.
- **Progress:** attempts, accuracy, error categories, languages, concepts, 14-day activity, retry history.

## 3. API

All bodies are JSON. Existing endpoints are unchanged; new fields are optional.

| Method | Endpoint | Notes |
|---|---|---|
| GET | `/api/health` | languages + sandbox capabilities |
| GET | `/api/languages` | `languages` plus `details` (available, install note) |
| POST | `/api/analyze` | `{language, code, expected_output?, stdin?}` - no saving |
| POST | `/api/explain` | adds `skill_level: "beginner" \| "intermediate"`; saves an attempt |
| POST / GET | `/api/attempts`, `/api/attempts/<id>` | create / read |
| POST | `/api/attempts/<id>/retry` | now also returns an `explanation` |
| GET | `/api/attempts/<id>/retries`, `/hints` | history |
| POST | `/api/hints` | `{attempt_id, level 1-3}` |
| POST | `/api/solution` | guidance, plus `corrected_code` when a fix was verified |
| GET | `/api/practice/concepts` | topics with supported languages |
| POST | `/api/practice/generate` | question + starter code per language (no expected output) |
| POST | `/api/practice/submit` | `{concept, code, language?}` |
| GET | `/api/practice/exercises?language=` | spot-the-error exercises |
| POST | `/api/practice/identify` | `{exercise_key, answer, line?}` |
| GET | `/api/progress` | analytics, now with categories, languages, activity, retry history |

Languages accept aliases: `py`, `cpp`, `c++`, `java`, `c`. `stdin` (max 5,000 chars) feeds `input()` / `scanf` / `Scanner`.

## 4. Terminal tool

```powershell
python cli\pees.py analyze main.py
python cli\pees.py analyze Main.java --hint 2 --fix
python cli\pees.py analyze main.c --expected expected.txt --stdin input.txt
python cli\pees.py analyze main.py --fix --write
```

Language comes from the extension (`.py .java .c .cpp`). `--server` or `PEES_SERVER` selects another backend.

Exit code 0 = no error, 1 = error or wrong output. On Windows `cli\pees.cmd` lets you type `pees analyze main.py` if the `cli` folder is on PATH.

## 5. VS Code extension (first version)

Open `vscode-extension/` in VS Code and press **F5** to start an Extension Development Host. Open a `.py/.java/.c/.cpp` file and run **Explain Errors in Current File** (Ctrl+Alt+E). It underlines the failing line, opens an explanation panel with progressive hints, and can apply a verified fix.

Settings: `pees.serverUrl`, `pees.skillLevel`, `pees.analyzeOnSave`.

**Status:** Its logic was exercised against the real backend with a mocked VS Code API, but it has not been run inside real VS Code yet - expect small fixes on first use.

## 6. Security - read this

Student code is now run in a **separate process** (not inside Flask) with: a fresh temporary directory per run, cleaned environment variables (your secrets are not inherited), 5-8 second wall-clock limits, 64 KB output cap, at most 4 concurrent runs, and on Linux/macOS CPU, memory, file-size and process-count limits; on Linux the network is disabled when user namespaces are available (`/api/health` → `sandbox` tells you what is active on this machine).

This is good for a local demonstration, **not** a hardened public service: code can still read files the backend's OS user can read, and **on Windows the memory/process limits and network isolation are not applied**. Before exposing it to untrusted users, run the backend in a locked-down container or VM, as an unprivileged user, with no secrets mounted.

## 7. Tests

Run:

```powershell
python -m unittest discover -s tests -t .
```

The test suite contains 48 tests covering all four languages (compile errors, runtime errors, correct programs), the sandbox (infinite loops, output flood, secret leakage, backend survival), explanations, hints, verified fixes, every practice exercise (each is executed to prove its stated answer and line), and the full API flow.

Tests for a language are skipped if its compiler is missing. Tests use a temporary database, never `database/learning.db`.

**Note:** The actual number of passing tests and skipped compiler-dependent tests should be confirmed by running the suite in the target environment.

## 8. Changes to your original code

- `analyzer/python_analyzer.py`: `exec()` replaced by sandboxed subprocess execution.
- `analyzer/logical_analyzer.py`: fixed newline normalisation (it matched the literal text `\r\n`, so Windows line endings made correct answers fail) and now ignores trailing spaces.
- `learning/problem_generator.py`: starter code contained literal `\n` text; now real newlines. Added 4 topics and per-language starter code.
- `classifier/error_classifier.py`: unknown exception names keep their phase category instead of "Unknown Error".
- `database/db.py`: adds a `stdin_input` column automatically; existing data is kept.
- `app.py`: new endpoints/fields listed above; works without `flask-cors` installed (falls back to a small CORS handler).

## 9. Known limitations / next steps

- Explanations are rule-based; unusual errors get the generic "debugging" explanation plus the raw compiler message.
- Java: one source file per submission. C/C++: single file, no `scanf` prompts handling beyond `stdin`.
- Auto-fixes cover a handful of well-understood mistakes; everything else is hints and guidance only.
- Not yet done: user accounts (progress is global to the database), LLM-assisted explanations, other editors.

---

The Programming Error Explanation System aims to help students understand programming mistakes instead of simply receiving corrected code. By combining error classification, contextual explanations, progressive hints and verified corrections, it makes debugging a learning process and encourages students to develop independent problem-solving skills.