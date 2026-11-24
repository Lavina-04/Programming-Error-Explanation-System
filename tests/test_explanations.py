import unittest

from explanation.explanation_engine import ExplanationEngine
from explanation.hint_generator import HintGenerator
from explanation.solution_generator import SolutionGenerator
from learning.exercises import EXERCISES
from tests.helpers import ANALYZER, available, err, needs

engine, hints, solutions = ExplanationEngine(), HintGenerator(), SolutionGenerator(ANALYZER)


class ExplanationTests(unittest.TestCase):
    def test_index_error_matches_the_project_example(self):
        code = "numbers = [10, 20, 30]\nprint(numbers[5])"
        result, _ = err("Python", code)
        e = engine.explain(result, "Python", code)
        self.assertIn("3 elements", e["specific"])
        self.assertIn("index 5", e["specific"])
        self.assertIn("0 to 2", e["specific"])
        self.assertEqual(e["concept"], "Zero-based indexing")
        for key in ("error_category", "line_number", "original_message", "why_it_happened",
                    "approach", "learning_outcome"):
            self.assertTrue(e[key], key)

    def test_name_error_suggests_close_match(self):
        code = "count = 3\nprint(cuont)"
        result, _ = err("Python", code)
        self.assertIn("count", engine.explain(result, "Python", code)["specific"])

    def test_skill_level_changes_the_text(self):
        code = "x = [1]\nprint(x[4])"
        result, _ = err("Python", code)
        beginner = engine.explain(result, "Python", code, "beginner")["detail"]
        advanced = engine.explain(result, "Python", code, "intermediate")["detail"]
        self.assertNotEqual(beginner, "")
        self.assertEqual(engine.explain(result, "Python", code, "intermediate")["skill_level"], "intermediate")
        self.assertIsInstance(advanced, str)

    def test_logical_error_points_at_first_difference(self):
        result = ANALYZER.analyze("Python", "print(1)\nprint(5)", "1\n6")
        e = engine.explain(result, "Python", "print(1)\nprint(5)")
        self.assertIn("line 2", e["specific"])

    def test_hints_progress_and_do_not_leak_code(self):
        code = "x = [1]\nprint(x[4])"
        result, _ = err("Python", code)
        texts = [hints.generate(result, level, code) for level in (1, 2, 3)]
        self.assertEqual(len(set(texts)), 3)
        self.assertEqual(hints.generate(result, 9, code), "Invalid hint level.")

    def test_unknown_error_name_still_gets_an_explanation(self):
        code = "class Boom(Exception):\n    pass\nraise Boom('bad')"
        result, error = err("Python", code)
        self.assertEqual(error.error_name, "Boom")
        self.assertEqual(error.category, "Runtime Error")
        self.assertTrue(engine.explain(result, "Python", code)["cause"])

    def test_every_alias_maps_to_complete_content(self):
        from explanation.knowledge_base import ALIASES, GROUPS
        for name in ALIASES:
            group = GROUPS[ALIASES[name]]
            self.assertEqual(len(group["hints"]), 3, name)
            for key in ("concept", "cause", "detail", "question", "approach", "fixes", "outcome"):
                self.assertTrue(group[key], f"{name}:{key}")


class VerifiedFixTests(unittest.TestCase):
    def fix(self, language, code):
        result, _ = err(language, code)
        return solutions.generate(result, code, language)

    def test_python_fixes(self):
        for code in ["numbers = [1, 2, 3]\nprint(numbers[5])",
                     "total = 4\nprint(totl)",
                     "if True:\nprint('a')",
                     "print 'hello'",
                     "x = 3\nif x > 1\n    print(x)"]:
            with self.subTest(code=code):
                solution = self.fix("Python", code)
                self.assertEqual(solution["type"], "verified_fix")
                after, _ = err("Python", solution["corrected_code"])
                self.assertNotEqual(after.get("status"), "unsupported")

    @needs("Java")
    def test_java_semicolon_fix_compiles(self):
        code = "public class Main {\n    public static void main(String[] a) {\n        int x = 5\n        System.out.println(x);\n    }\n}\n"
        solution = self.fix("Java", code)
        self.assertEqual(solution["type"], "verified_fix")
        result, error = err("Java", solution["corrected_code"])
        self.assertEqual(result["actual_output"], "5")

    @needs("C")
    def test_c_semicolon_fix_compiles(self):
        code = '#include <stdio.h>\nint main() {\n    int x = 5\n    printf("%d", x);\n    return 0;\n}\n'
        solution = self.fix("C", code)
        self.assertEqual(solution["type"], "verified_fix")
        self.assertEqual(err("C", solution["corrected_code"])[0]["actual_output"], "5")

    def test_no_fix_is_claimed_when_none_is_verified(self):
        solution = self.fix("Python", "print(1 / 0)")
        self.assertEqual(solution["type"], "guidance")
        self.assertIsNone(solution["corrected_code"])


class ExerciseTests(unittest.TestCase):
    def test_every_exercise_really_produces_its_answer(self):
        for exercise in EXERCISES:
            if not available(exercise["language"]):
                continue
            with self.subTest(key=exercise["key"]):
                _, error = err(exercise["language"], exercise["code"])
                self.assertIsNotNone(error)
                self.assertEqual(error.error_name, exercise["answer"])
                self.assertEqual(error.line_number, exercise["line"])
                self.assertIn(exercise["answer"], exercise["options"])


if __name__ == "__main__":
    unittest.main()
