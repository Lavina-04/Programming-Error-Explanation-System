import tempfile
import unittest
from pathlib import Path

import database.db as db
from analyzer.analyzer import Analyzer
from learning.attempt_manager import AttemptManager
from learning.learning_analyzer import LearningAnalyzer
from learning.problem_generator import ProblemGenerator


class BackendCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_db_path = db.DB_PATH
        db.DB_PATH = Path(tempfile.mkdtemp()) / "test_learning.db"
        db.init_db()
        cls.analyzer = Analyzer()
        cls.manager = AttemptManager()

    @classmethod
    def tearDownClass(cls):
        db.DB_PATH = cls.original_db_path

    def test_runtime_error(self):
        result = self.analyzer.analyze("Python", "items = [1]\nprint(items[3])")
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"].error_name, "IndexError")
        self.assertEqual(result["error"].line_number, 2)

    def test_correct_output(self):
        result = self.analyzer.analyze("Python", "print(6 * 7)", "42")
        self.assertEqual(result["status"], "correct")
        self.assertEqual(result["actual_output"], "42")

    def test_logical_error(self):
        result = self.analyzer.analyze("Python", "print(6 * 6)", "42")
        self.assertEqual(result["status"], "logical_error")
        self.assertEqual(result["actual_output"], "36")

    def test_practice_catalogue_unknown_concept(self):
        generator = ProblemGenerator()
        self.assertIsNone(generator.generate("not-a-real-concept"))
        self.assertEqual(generator.generate("List Indexing")["key"], "indexing")

    def test_practice_attempt_and_retry_analytics(self):
        correct = self.analyzer.analyze("Python", "print(16)", "16")
        explanation = {"concept": "List Indexing", "summary": "test"}
        attempt_id = self.manager.save_attempt(
            "Python", "print(16)", correct, explanation, "16",
            source="practice", question_key="indexing"
        )
        self.assertTrue(self.manager.get_attempt(attempt_id)["solved"])

        wrong = self.analyzer.analyze("Python", "print(8)", "16")
        retry = self.manager.save_retry(attempt_id, "print(8)", wrong, "16")
        self.assertFalse(retry["solved"])

        progress = LearningAnalyzer().get_progress()
        self.assertEqual(progress["practice"]["total_submissions"], 1)
        self.assertEqual(progress["practice"]["solved_submissions"], 1)
        self.assertEqual(progress["retries"]["total_retries"], 1)


if __name__ == "__main__":
    unittest.main()
