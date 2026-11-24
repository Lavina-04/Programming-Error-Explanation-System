# Normalised categories shared by every language.
SYNTAX = "Syntax Error"
COMPILATION = "Compilation Error"
TYPE = "Type Error"
RUNTIME = "Runtime Error"
MEMORY = "Memory Error"
TIMEOUT = "Time Limit Error"

CATEGORY_BY_NAME = {}


def _register(category, names):
    for name in names:
        CATEGORY_BY_NAME[name] = category


_register(SYNTAX, [
    "SyntaxError", "IndentationError", "TabError", "MissingSemicolon",
    "MissingBracket", "MissingClosingBrace", "UnclosedString",
])
_register(COMPILATION, [
    "UndeclaredIdentifier", "DuplicateDeclaration", "WrongArguments",
    "MissingReturn", "UninitializedVariable", "StaticContext", "FinalReassignment",
    "UndefinedReference", "MissingHeader", "ImplicitDeclaration",
    "UnreportedException", "ClassFileNameMismatch", "CompilationError",
    "MissingMainMethod", "FormatMismatch",
])
_register(TYPE, [
    "TypeMismatch", "BadOperandTypes", "TypeError", "ValueError",
    "NumberFormatException", "ClassCastException", "InputMismatchException",
])
_register(RUNTIME, [
    "IndexError", "KeyError", "NameError", "UnboundLocalError", "ZeroDivisionError",
    "AttributeError", "FileNotFoundError", "ImportError", "ModuleNotFoundError",
    "RecursionError", "OverflowError", "EOFError", "StopIteration",
    "ArrayIndexOutOfBoundsException", "StringIndexOutOfBoundsException",
    "IndexOutOfBoundsException", "NullPointerException", "ArithmeticException",
    "NegativeArraySizeException", "StackOverflowError", "NoSuchElementException",
    "SegmentationFault", "NullPointerDereference", "ArrayOutOfBounds",
    "DivisionByZero", "SignedIntegerOverflow", "UncaughtException",
    "StackOverflow", "ProgramError", "FloatingPointException",
])
_register(MEMORY, [
    "MemoryError", "OutOfMemoryError", "HeapBufferOverflow", "StackBufferOverflow",
    "GlobalBufferOverflow", "HeapUseAfterFree", "StackUseAfterScope", "DoubleFree",
    "InvalidFree",
])
_register(TIMEOUT, ["TimeLimitExceeded"])


class ErrorClassifier:
    def classify(self, error):
        category = CATEGORY_BY_NAME.get(error.error_name)
        if category:
            return category
        # Unknown names (for example a student-defined exception) keep the
        # phase category the analyzer assigned instead of becoming "Unknown".
        if getattr(error, "category", None) in (SYNTAX, COMPILATION, RUNTIME):
            return error.category
        return "Unknown Error"
