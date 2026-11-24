import os
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from analyzer.analyzer import Analyzer
from database.db import init_db
from explanation.explanation_engine import ExplanationEngine
from explanation.hint_generator import HintGenerator
from explanation.solution_generator import SolutionGenerator
from execution.sandbox import sandbox_capabilities
from learning.attempt_manager import AttemptManager
from learning.exercises import BY_KEY as EXERCISES_BY_KEY, EXERCISES, public_view
from learning.learning_analyzer import LearningAnalyzer
from learning.problem_generator import ProblemGenerator


FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"
app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024  # 1 MB request limit
app.config["JSON_SORT_KEYS"] = False

allowed_origins = [
    origin.strip()
    for origin in os.environ.get(
        "FRONTEND_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]
try:
    from flask_cors import CORS
    CORS(app, resources={r"/api/*": {"origins": allowed_origins}})
except ImportError:  # minimal fallback so the backend still starts without Flask-Cors
    @app.after_request
    def _cors(response):
        origin = request.headers.get("Origin")
        if request.path.startswith("/api/") and origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        return response

analyzer = Analyzer()
language_manager = analyzer.language_manager
explanation_engine = ExplanationEngine()
hint_generator = HintGenerator()
solution_generator = SolutionGenerator(analyzer)
attempt_manager = AttemptManager()
learning_analyzer = LearningAnalyzer()
problem_generator = ProblemGenerator()

init_db()


def serialize_result(result):
    serialized = dict(result)
    error = serialized.get("error")
    if error is not None:
        if hasattr(error, "to_dict"):
            serialized["error"] = error.to_dict()
        elif isinstance(error, dict):
            serialized["error"] = error
        else:
            serialized["error"] = {
                "language": getattr(error, "language", None),
                "error_name": getattr(error, "error_name", None),
                "message": getattr(error, "message", str(error)),
                "line_number": getattr(error, "line_number", None),
                "code": getattr(error, "code", None),
                "category": getattr(error, "category", None)
            }
    return serialized


def analyze_payload(payload):
    return analyzer.analyze(
        payload["language"], payload["code"], payload["expected_output"], payload["stdin"]
    )


def explain_and_save(payload):
    result = analyze_payload(payload)
    explanation = explanation_engine.explain(
        result, payload["language"], payload["code"], payload["skill_level"]
    )
    attempt_id = attempt_manager.save_attempt(
        payload["language"], payload["code"], result, explanation,
        payload["expected_output"], source="code", stdin_input=payload["stdin"]
    )
    return {
        "attempt_id": attempt_id,
        "analysis": serialize_result(result),
        "explanation": explanation
    }


def json_body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, (jsonify({"error": "A JSON object is required."}), 400)
    return data, None


def validate_code_payload(data, require_language=False):
    language = data.get("language", "Python")
    code = data.get("code")
    expected_output = data.get("expected_output")
    stdin_text = data.get("stdin", "")
    skill_level = data.get("skill_level", "beginner")

    if not isinstance(stdin_text, str) or len(stdin_text) > 5000:
        return None, (jsonify({"error": "stdin must be a string of at most 5,000 characters."}), 400)
    if skill_level not in ("beginner", "intermediate"):
        return None, (jsonify({"error": "skill_level must be 'beginner' or 'intermediate'."}), 400)
    if not isinstance(language, str) or not language.strip():
        return None, (jsonify({"error": "language must be a non-empty string."}), 400)
    if not isinstance(code, str) or not code.strip():
        return None, (jsonify({"error": "code must be a non-empty string."}), 400)
    if len(code) > 20000:
        return None, (jsonify({"error": "Code exceeds the 20,000 character limit."}), 413)
    if expected_output is not None and not isinstance(expected_output, str):
        expected_output = str(expected_output)
    if expected_output is not None and len(expected_output) > 20000:
        return None, (jsonify({"error": "expected_output is too long."}), 400)

    return {
        "language": language_manager.canonical_name(language.strip()),
        "code": code,
        "expected_output": expected_output,
        "stdin": stdin_text,
        "skill_level": skill_level
    }, None


def parse_pagination():
    try:
        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))
    except ValueError:
        return None, (jsonify({"error": "limit and offset must be integers."}), 400)
    if limit < 1 or limit > 100 or offset < 0:
        return None, (jsonify({"error": "limit must be 1-100 and offset must be non-negative."}), 400)
    return (limit, offset), None


@app.errorhandler(413)
def request_too_large(_error):
    return jsonify({"error": "Request body is too large. Maximum size is 1 MB."}), 413


@app.errorhandler(404)
def not_found(_error):
    return jsonify({"error": "Endpoint not found."}), 404


@app.errorhandler(500)
def internal_error(_error):
    app.logger.exception("Unhandled backend error")
    return jsonify({"error": "Internal server error."}), 500


# 1. Backend health
@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "message": "Programming Error Explanation System backend running",
        "supported_languages": [d["name"] for d in language_manager.describe()],
        "sandbox": sandbox_capabilities()
    })


# 2. Supported languages
@app.get("/api/languages")
def languages():
    details = language_manager.describe()
    return jsonify({"languages": [d["name"] for d in details], "details": details})


# 3. Analyze code without saving an attempt
@app.post("/api/analyze")
def analyze():
    data, problem = json_body()
    if problem:
        return problem
    payload, problem = validate_code_payload(data)
    if problem:
        return problem
    return jsonify(serialize_result(analyze_payload(payload)))


# 4. Analyze, explain and save an attempt
@app.post("/api/explain")
def explain():
    data, problem = json_body()
    if problem:
        return problem
    payload, problem = validate_code_payload(data)
    if problem:
        return problem

    return jsonify(explain_and_save(payload)), 201


# 5. Create an attempt record
@app.post("/api/attempts")
def create_attempt():
    data, problem = json_body()
    if problem:
        return problem
    payload, problem = validate_code_payload(data)
    if problem:
        return problem

    return jsonify(explain_and_save(payload)), 201


# 6. List attempts with pagination
@app.get("/api/attempts")
def get_attempts():
    pagination, problem = parse_pagination()
    if problem:
        return problem
    limit, offset = pagination
    attempts = attempt_manager.list_attempts(limit, offset)
    return jsonify({
        "attempts": attempts,
        "limit": limit,
        "offset": offset,
        "returned": len(attempts)
    })


# 7. Get one attempt
@app.get("/api/attempts/<int:attempt_id>")
def get_attempt(attempt_id):
    attempt = attempt_manager.get_attempt(attempt_id)
    if not attempt:
        return jsonify({"error": "Attempt not found."}), 404
    return jsonify({"attempt": attempt})


# 8. Retry an attempt
@app.post("/api/attempts/<int:attempt_id>/retry")
def retry_attempt(attempt_id):
    attempt = attempt_manager.get_attempt(attempt_id)
    if not attempt:
        return jsonify({"error": "Attempt not found."}), 404

    data, problem = json_body()
    if problem:
        return problem
    code = data.get("code")
    if not isinstance(code, str) or not code.strip():
        return jsonify({"error": "Revised code is required."}), 400
    if len(code) > 20000:
        return jsonify({"error": "Code exceeds the 20,000 character limit."}), 413

    # Practice answers must always use the trusted answer stored in the question bank.
    if attempt.get("source") == "practice":
        expected_output = attempt.get("expected_output")
    else:
        expected_output = data.get("expected_output", attempt.get("expected_output"))
    if expected_output is not None and not isinstance(expected_output, str):
        expected_output = str(expected_output)

    stdin_text = data.get("stdin", attempt.get("stdin_input") or "")
    if not isinstance(stdin_text, str) or len(stdin_text) > 5000:
        return jsonify({"error": "stdin must be a string of at most 5,000 characters."}), 400
    result = analyzer.analyze(
        attempt["language"], code, expected_output, stdin_text
    )
    retry = attempt_manager.save_retry(
        attempt_id, code, result, expected_output
    )
    return jsonify({
        "attempt_id": attempt_id,
        "retry": retry,
        "analysis": serialize_result(result),
        "explanation": explanation_engine.explain(result, attempt["language"], code)
    })


# 9. Retry history
@app.get("/api/attempts/<int:attempt_id>/retries")
def get_retry_history(attempt_id):
    if not attempt_manager.get_attempt(attempt_id):
        return jsonify({"error": "Attempt not found."}), 404
    history = attempt_manager.get_retry_history(attempt_id)
    return jsonify({
        "attempt_id": attempt_id,
        "retry_count": len(history),
        "retries": history
    })


# 10. Hints
@app.post("/api/hints")
def hints():
    data, problem = json_body()
    if problem:
        return problem
    attempt_id = data.get("attempt_id")
    level = data.get("level", 1)

    if not isinstance(attempt_id, int) or isinstance(attempt_id, bool) or attempt_id < 1:
        return jsonify({"error": "A valid attempt_id is required."}), 400
    if not isinstance(level, int) or isinstance(level, bool) or level not in (1, 2, 3):
        return jsonify({"error": "Hint level must be 1, 2, or 3."}), 400

    attempt = attempt_manager.get_attempt(attempt_id)
    if not attempt:
        return jsonify({"error": "Attempt not found."}), 404

    result = analyzer.analyze(
        attempt["language"], attempt["code"], attempt["expected_output"],
        attempt.get("stdin_input") or ""
    )
    hint = hint_generator.generate(result, level, attempt["code"])
    attempt_manager.save_hint(attempt_id, level, hint)
    return jsonify({
        "attempt_id": attempt_id,
        "level": level,
        "hint": hint
    })


@app.get("/api/attempts/<int:attempt_id>/hints")
def get_attempt_hints(attempt_id):
    if not attempt_manager.get_attempt(attempt_id):
        return jsonify({"error": "Attempt not found."}), 404
    return jsonify({
        "attempt_id": attempt_id,
        "hints": attempt_manager.get_hints(attempt_id)
    })


# 11. Optional solution guidance
@app.post("/api/solution")
def solution():
    data, problem = json_body()
    if problem:
        return problem
    attempt_id = data.get("attempt_id")
    if not isinstance(attempt_id, int) or isinstance(attempt_id, bool) or attempt_id < 1:
        return jsonify({"error": "A valid attempt_id is required."}), 400

    attempt = attempt_manager.get_attempt(attempt_id)
    if not attempt:
        return jsonify({"error": "Attempt not found."}), 404

    stdin_text = attempt.get("stdin_input") or ""
    result = analyzer.analyze(
        attempt["language"], attempt["code"], attempt["expected_output"], stdin_text
    )
    return jsonify({
        "attempt_id": attempt_id,
        "solution": solution_generator.generate(
            result, attempt["code"], attempt["language"], stdin_text)
    })


# 12. Practice question catalogue
@app.get("/api/practice/concepts")
def practice_concepts():
    return jsonify({"concepts": problem_generator.list_concepts()})


# 13. Generate a practice question
@app.post("/api/practice/generate")
def generate_practice():
    data, problem = json_body()
    if problem:
        return problem
    concept = data.get("concept", "indexing")
    question = problem_generator.generate(concept)
    if question is None:
        return jsonify({
            "error": "Practice question not found.",
            "available_concepts": problem_generator.list_concepts()
        }), 404
    # The expected answer is retained server-side; do not expose it before submission.
    public_question = {
        key: value for key, value in question.items()
        if key != "expected_output"
    }
    return jsonify(public_question)


# 14. Submit and evaluate a practice answer
@app.post("/api/practice/submit")
def submit_practice():
    data, problem = json_body()
    if problem:
        return problem
    concept = data.get("concept")
    code = data.get("code")
    language = language_manager.canonical_name(data.get("language", "Python"))
    stdin_text = ""

    if not isinstance(concept, str) or not concept.strip():
        return jsonify({"error": "Practice concept is required."}), 400
    if not isinstance(code, str) or not code.strip():
        return jsonify({"error": "Student code is required."}), 400
    if len(code) > 20000:
        return jsonify({"error": "Code exceeds the 20,000 character limit."}), 413

    question = problem_generator.get_problem(concept)
    if question is None:
        return jsonify({
            "error": "Practice question not found.",
            "available_concepts": problem_generator.list_concepts()
        }), 404

    if language not in question["languages"]:
        return jsonify({
            "error": f"This question is not available in {language}.",
            "available_languages": question["languages"]
        }), 400

    expected_output = question["expected_output"]
    result = analyzer.analyze(language, code, expected_output)
    explanation = explanation_engine.explain(result, language, code)
    explanation["concept"] = question["concept"]

    attempt_id = attempt_manager.save_attempt(
        language, code, result, explanation, expected_output,
        source="practice", question_key=question["key"]
    )

    return jsonify({
        "attempt_id": attempt_id,
        "question": question["title"],
        "concept": question["concept"],
        "evaluation": {
            "status": result.get("status"),
            "passed": result.get("status") == "correct",
            "actual_output": result.get("actual_output", ""),
            "expected_output": expected_output
        },
        "analysis": serialize_result(result),
        "explanation": explanation
    })


# 14b. Error-identification exercises
@app.get("/api/practice/exercises")
def list_exercises():
    language = request.args.get("language")
    items = [public_view(e) for e in EXERCISES
             if not language or e["language"].lower() == language.lower()]
    return jsonify({"exercises": items})


@app.post("/api/practice/identify")
def submit_identification():
    data, problem = json_body()
    if problem:
        return problem
    exercise = EXERCISES_BY_KEY.get(data.get("exercise_key"))
    answer = data.get("answer")
    line = data.get("line")
    if exercise is None:
        return jsonify({"error": "Exercise not found."}), 404
    if answer not in exercise["options"]:
        return jsonify({"error": "answer must be one of the listed options."}), 400
    if line is not None and (not isinstance(line, int) or isinstance(line, bool)):
        return jsonify({"error": "line must be an integer."}), 400

    error_correct = answer == exercise["answer"]
    line_correct = line is None or line == exercise["line"]
    passed = error_correct and line_correct

    result = {"status": "correct" if passed else "incorrect", "actual_output": answer}
    if not passed:
        result["error"] = {"error_name": exercise["answer"], "category": None}
    explanation = {"concept": exercise["concept"], "summary": exercise["explanation"]}
    attempt_id = attempt_manager.save_attempt(
        exercise["language"], exercise["code"], result, explanation,
        exercise["answer"], source="identify", question_key=exercise["key"]
    )
    return jsonify({
        "attempt_id": attempt_id,
        "passed": passed,
        "error_correct": error_correct,
        "line_correct": line_correct,
        "correct_answer": exercise["answer"],
        "correct_line": exercise["line"],
        "explanation": exercise["explanation"],
        "hint": exercise["hint"]
    })


@app.get("/api/practice/exercises/<key>/hint")
def exercise_hint(key):
    exercise = EXERCISES_BY_KEY.get(key)
    if exercise is None:
        return jsonify({"error": "Exercise not found."}), 404
    return jsonify({"hint": exercise["hint"]})


# 15. Learning analytics
@app.get("/api/progress")
def progress():
    return jsonify(learning_analyzer.get_progress())


# Frontend (served from the same origin, so no CORS setup is needed locally)
@app.get("/")
def frontend_index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/<path:filename>")
def frontend_files(filename):
    if filename.startswith("api/"):
        return jsonify({"error": "Endpoint not found."}), 404
    return send_from_directory(FRONTEND_DIR, filename)


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("PORT", "5001")),
        debug=os.environ.get("FLASK_DEBUG", "0") == "1"
    )
