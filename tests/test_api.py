import tempfile
import unittest
from pathlib import Path

import database.db as db

# The API tests must never touch the real learning database.
db.DB_PATH = Path(tempfile.mkdtemp()) / "api_test.db"

import app as backend  # noqa: E402
from tests.helpers import available  # noqa: E402


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db.init_db()
        cls.client = backend.app.test_client()

    def post(self, path, body):
        return self.client.post(path, json=body)

    def test_health_languages_and_frontend(self):
        health = self.client.get("/api/health").get_json()
        self.assertEqual(health["supported_languages"], ["Python", "Java", "C", "C++"])
        self.assertIn("network_disabled", health["sandbox"])
        details = self.client.get("/api/languages").get_json()
        self.assertEqual([d["name"] for d in details["details"]], ["Python", "Java", "C", "C++"])
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/styles.css").status_code, 200)
        self.assertEqual(self.client.get("/api/nothing").status_code, 404)

    def test_full_learning_flow(self):
        code = "numbers = [10, 20, 30]\nprint(numbers[5])"
        r = self.post("/api/explain", {"language": "Python", "code": code})
        self.assertEqual(r.status_code, 201)
        data = r.get_json()
        attempt = data["attempt_id"]
        self.assertEqual(data["analysis"]["error"]["error_name"], "IndexError")
        self.assertIn("raw_message", data["analysis"]["error"])
        self.assertIn("3 elements", data["explanation"]["specific"])

        hints = [self.post("/api/hints", {"attempt_id": attempt, "level": n}).get_json()["hint"] for n in (1, 2, 3)]
        self.assertEqual(len(set(hints)), 3)

        solution = self.post("/api/solution", {"attempt_id": attempt}).get_json()["solution"]
        self.assertEqual(solution["type"], "verified_fix")

        retry = self.post(f"/api/attempts/{attempt}/retry", {"code": solution["corrected_code"]}).get_json()
        self.assertEqual(retry["analysis"]["status"], "correct")
        self.assertEqual(len(self.client.get(f"/api/attempts/{attempt}/retries").get_json()["retries"]), 1)

        progress = self.client.get("/api/progress").get_json()
        self.assertGreaterEqual(progress["total_attempts"], 1)
        for key in ("category_frequency", "language_frequency", "activity", "retry_history"):
            self.assertIn(key, progress)

    def test_language_aliases_and_validation(self):
        self.assertEqual(self.post("/api/analyze", {"language": "py", "code": "print(1)"}).get_json()["status"], "correct")
        self.assertEqual(self.post("/api/analyze", {"language": "Ruby", "code": "x"}).get_json()["status"], "unsupported")
        self.assertEqual(self.post("/api/analyze", {"language": "Python", "code": ""}).status_code, 400)
        self.assertEqual(self.post("/api/analyze", {"language": "Python", "code": "x" * 20001}).status_code, 413)
        self.assertEqual(self.post("/api/analyze", {"code": "1", "skill_level": "wizard"}).status_code, 400)
        self.assertEqual(self.post("/api/hints", {"attempt_id": 999, "level": 1}).status_code, 404)

    def test_stdin_is_remembered_for_hints(self):
        r = self.post("/api/explain", {"language": "Python", "code": "n = int(input())\nprint(10 / n)", "stdin": "0"}).get_json()
        self.assertEqual(r["analysis"]["error"]["error_name"], "ZeroDivisionError")
        hint = self.post("/api/hints", {"attempt_id": r["attempt_id"], "level": 1}).get_json()["hint"]
        self.assertIn("division", hint.lower())

    def test_practice_python_and_other_languages(self):
        question = self.post("/api/practice/generate", {"concept": "List Indexing"}).get_json()
        self.assertNotIn("expected_output", question)
        self.assertIn("Java", question["starters"])
        ok = self.post("/api/practice/submit", {"concept": "List Indexing", "code": "values = [4, 8, 12, 16]\nprint(values[-1])"}).get_json()
        self.assertTrue(ok["evaluation"]["passed"])
        wrong = self.post("/api/practice/submit", {"concept": "List Indexing", "code": "print(1)"}).get_json()
        self.assertFalse(wrong["evaluation"]["passed"])
        self.assertEqual(self.post("/api/practice/submit", {"concept": "Safe Division", "code": "print(5.0)", "language": "Java"}).status_code, 400)

    @unittest.skipUnless(available("C++"), "C++ not installed")
    def test_practice_in_cpp(self):
        code = '#include <iostream>\nusing namespace std;\nint main() {\n    for (int i = 1; i <= 5; i++) cout << i << "\\n";\n    return 0;\n}\n'
        r = self.post("/api/practice/submit", {"concept": "loops", "code": code, "language": "cpp"}).get_json()
        self.assertTrue(r["evaluation"]["passed"], r)

    def test_identification_exercises(self):
        listing = self.client.get("/api/practice/exercises?language=Python").get_json()["exercises"]
        self.assertTrue(listing and all("answer" not in e for e in listing))
        good = self.post("/api/practice/identify", {"exercise_key": "py_zero", "answer": "ZeroDivisionError", "line": 3}).get_json()
        self.assertTrue(good["passed"])
        bad = self.post("/api/practice/identify", {"exercise_key": "py_zero", "answer": "TypeError"}).get_json()
        self.assertFalse(bad["passed"])
        wrong_line = self.post("/api/practice/identify", {"exercise_key": "py_zero", "answer": "ZeroDivisionError", "line": 1}).get_json()
        self.assertTrue(wrong_line["error_correct"] and not wrong_line["line_correct"])
        self.assertEqual(self.post("/api/practice/identify", {"exercise_key": "py_zero", "answer": "Nope"}).status_code, 400)
        progress = self.client.get("/api/progress").get_json()
        self.assertGreaterEqual(progress["practice"]["total_submissions"], 3)


if __name__ == "__main__":
    unittest.main()
