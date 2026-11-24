import os
import unittest

from tests.helpers import ANALYZER, err, needs

JAVA = "public class Main {\n    public static void main(String[] args) {\n%s\n    }\n}\n"


class SandboxTests(unittest.TestCase):
    def test_infinite_loop_is_stopped(self):
        result, error = err("Python", "while True:\n    pass")
        self.assertEqual(error.error_name, "TimeLimitExceeded")

    def test_student_code_cannot_kill_the_backend(self):
        # With the old exec() approach this would terminate the whole process.
        result, error = err("Python", "import os\nos._exit(3)\nprint('x')")
        self.assertIsNone(error)  # a non-zero exit is not a Python exception

    def test_secrets_are_not_inherited(self):
        os.environ["PEES_TEST_SECRET"] = "hunter2"
        result, _ = err("Python", "import os\nprint(os.environ.get('PEES_TEST_SECRET', 'hidden'))")
        self.assertEqual(result["actual_output"], "hidden")

    def test_output_is_capped(self):
        result, _ = err("Python", "print('x' * 10_000_000)")
        self.assertLess(len(result["actual_output"]), 70_000)


class PythonTests(unittest.TestCase):
    def test_syntax_error_line(self):
        result, error = err("Python", "x = 1\nprint('a'")
        self.assertEqual(error.category, "Syntax Error")
        self.assertEqual(error.line_number, 2)
        self.assertIn("SyntaxError", error.raw_message)

    def test_indentation_error(self):
        _, error = err("Python", "if True:\nprint(1)")
        self.assertEqual(error.error_name, "IndentationError")

    def test_runtime_errors(self):
        for code, name, line in [
            ("items = [1]\nprint(items[3])", "IndexError", 2),
            ("print(undefined_name)", "NameError", 1),
            ("print(1 + 'a')", "TypeError", 1),
            ("x = 1\ny = 0\nprint(x / y)", "ZeroDivisionError", 3),
            ("int('abc')", "ValueError", 1),
            ("d = {}\nprint(d['k'])", "KeyError", 2),
        ]:
            with self.subTest(name=name):
                _, error = err("Python", code)
                self.assertEqual((error.error_name, error.line_number), (name, line))

    def test_error_inside_function_reports_student_line(self):
        _, error = err("Python", "def f(a):\n    return a[10]\nf([1])")
        self.assertEqual(error.line_number, 2)

    def test_logical_error_and_correct(self):
        self.assertEqual(ANALYZER.analyze("Python", "print(2*3)", "7")["status"], "logical_error")
        self.assertEqual(ANALYZER.analyze("Python", "print(2*3)", "6")["status"], "correct")

    def test_stdin(self):
        result, error = err("Python", "print(int(input()) * 2)", stdin="21")
        self.assertEqual(result["actual_output"], "42")
        _, error = err("Python", "input()")
        self.assertEqual(error.error_name, "EOFError")


@needs("Java")
class JavaTests(unittest.TestCase):
    def test_compile_error_missing_semicolon(self):
        result, error = err("Java", JAVA % "        int x = 5\n        System.out.println(x);")
        self.assertEqual(error.error_name, "MissingSemicolon")
        self.assertEqual(error.line_number, 3)
        self.assertEqual(error.category, "Syntax Error")
        self.assertIn("';' expected", error.raw_message)

    def test_undeclared_and_type_errors(self):
        _, error = err("Java", JAVA % "        System.out.println(missing);")
        self.assertEqual(error.error_name, "UndeclaredIdentifier")
        _, error = err("Java", JAVA % '        int n = "five";')
        self.assertEqual(error.error_name, "TypeMismatch")

    def test_runtime_exceptions(self):
        _, error = err("Java", JAVA % "        int[] a = {1, 2, 3};\n        System.out.println(a[5]);")
        self.assertEqual(error.error_name, "ArrayIndexOutOfBoundsException")
        self.assertEqual(error.line_number, 4)
        _, error = err("Java", JAVA % "        String s = null;\n        s.length();")
        self.assertEqual(error.error_name, "NullPointerException")
        _, error = err("Java", JAVA % '        Integer.parseInt("abc");')
        self.assertEqual(error.error_name, "NumberFormatException")
        _, error = err("Java", JAVA % "        System.out.println(5 / (1 - 1));")
        self.assertEqual(error.error_name, "ArithmeticException")

    def test_correct_program(self):
        result, error = err("Java", JAVA % '        System.out.println("Hello");', "Hello")
        self.assertIsNone(error)
        self.assertEqual(result["status"], "correct")

    def test_non_main_public_class_name(self):
        code = 'public class Greeter {\n public static void main(String[] a) {\n  System.out.println("hi");\n }\n}\n'
        result, error = err("Java", code)
        self.assertEqual(result["actual_output"], "hi")


class NativeMixin:
    language = ""
    main_wrap = "%s"

    def wrap(self, body):
        return self.main_wrap % body


@needs("C")
class CTests(unittest.TestCase):
    HEAD = "#include <stdio.h>\n\nint main() {\n%s\n    return 0;\n}\n"

    def test_compile_errors(self):
        _, error = err("C", self.HEAD % "    int x = 5\n    printf(\"%d\", x);")
        self.assertEqual(error.error_name, "MissingSemicolon")
        self.assertEqual(error.phase, "compile")
        _, error = err("C", self.HEAD % '    printf("%d", y);')
        self.assertEqual((error.error_name, error.line_number), ("UndeclaredIdentifier", 4))
        self.assertIn("undeclared", error.raw_message)

    def test_correct_program_and_warnings(self):
        result, error = err("C", self.HEAD % '    printf("hello\\n");', "hello")
        self.assertEqual(result["status"], "correct")
        result, _ = err("C", self.HEAD % '    int unused = 1;\n    printf("ok");')
        self.assertTrue(result["warnings"])

    def test_runtime_failures_have_lines(self):
        _, error = err("C", self.HEAD % "    int *p = NULL;\n    *p = 1;")
        self.assertIn(error.error_name, ("NullPointerDereference", "SegmentationFault"))
        _, error = err("C", self.HEAD % '    int a[3] = {1,2,3};\n    int i = 5;\n    printf("%d", a[i]);')
        self.assertIn(error.error_name, ("ArrayOutOfBounds", "StackBufferOverflow", "SegmentationFault"))

    def test_link_error(self):
        _, error = err("C", "int helper(void);\nint main() { return helper(); }\n")
        self.assertEqual(error.error_name, "UndefinedReference")


@needs("C++")
class CppTests(unittest.TestCase):
    HEAD = "#include <iostream>\n#include <vector>\nusing namespace std;\n\nint main() {\n%s\n    return 0;\n}\n"

    def test_compile_errors(self):
        _, error = err("C++", self.HEAD % "    cout << missing;")
        self.assertEqual((error.error_name, error.line_number), ("UndeclaredIdentifier", 6))
        _, error = err("C++", self.HEAD % '    int x = "hi";')
        self.assertEqual(error.error_name, "TypeMismatch")
        _, error = err("C++", self.HEAD % "    int x = 1\n    cout << x;")
        self.assertEqual(error.error_name, "MissingSemicolon")

    def test_runtime_errors(self):
        _, error = err("C++", self.HEAD % "    int a = 0;\n    cout << 5 / a;")
        self.assertIn(error.error_name, ("DivisionByZero",))
        _, error = err("C++", self.HEAD % "    vector<int> v{1,2,3};\n    cout << v.at(9);")
        self.assertEqual(error.error_name, "UncaughtException")
        self.assertIn("out_of_range", error.message)

    def test_correct_program(self):
        result, _ = err("C++", self.HEAD % '    cout << "Hi";', "Hi")
        self.assertEqual(result["status"], "correct")


class UnavailableAndUnknown(unittest.TestCase):
    def test_unknown_language(self):
        self.assertEqual(ANALYZER.analyze("Ruby", "puts 1")["status"], "unsupported")

    def test_aliases(self):
        for alias in ("cpp", "C++", "py", "JAVA", "c"):
            self.assertIsNotNone(ANALYZER.language_manager.get_analyzer(alias))


if __name__ == "__main__":
    unittest.main()
