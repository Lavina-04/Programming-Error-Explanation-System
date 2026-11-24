"""Turns raw compiler diagnostics into normalised error names.

Each entry is (regex, normalised_name). The first match wins, so more specific
patterns come first. The original message is always kept by the analyzer.
"""
import re

JAVA_PATTERNS = [
    (r"';' expected", "MissingSemicolon"),
    (r"reached end of file while parsing", "MissingClosingBrace"),
    (r"'[)\]}]' expected|'\(' expected|'\[' expected", "MissingBracket"),
    (r"unclosed string literal", "UnclosedString"),
    (r"cannot find symbol", "UndeclaredIdentifier"),
    (r"incompatible types", "TypeMismatch"),
    (r"bad operand types|incomparable types", "BadOperandTypes"),
    (r"missing return statement", "MissingReturn"),
    (r"might not have been initialized", "UninitializedVariable"),
    (r"is already defined", "DuplicateDeclaration"),
    (r"unreported exception", "UnreportedException"),
    (r"non-static .* cannot be referenced from a static context", "StaticContext"),
    (r"cannot be applied to given types|no suitable (method|constructor)", "WrongArguments"),
    (r"cannot assign a value to final variable", "FinalReassignment"),
    (r"should be declared in a file named", "ClassFileNameMismatch"),
    (r"illegal start of expression|not a statement|<identifier> expected|"
     r"class, interface, enum, or record expected|illegal start of type|"
     r"'else' without 'if'|orphaned", "SyntaxError"),
]

C_FAMILY_PATTERNS = [
    (r"expected '[;,]'( or '[;,]')? before|expected ';'", "MissingSemicolon"),
    (r"expected declaration or statement at end of input|expected '\}' at end of input",
     "MissingClosingBrace"),
    (r"expected '[)\]]' before|expected '[)\]]'|expected '\(' before", "MissingBracket"),
    (r"missing terminating", "UnclosedString"),
    (r"fatal error: .*: No such file or directory", "MissingHeader"),
    (r"undefined reference to", "UndefinedReference"),
    (r"implicit declaration of function", "ImplicitDeclaration"),
    (r"undeclared \(first use|was not declared in this scope|does not name a type|"
     r"has not been declared|not declared in this scope", "UndeclaredIdentifier"),
    (r"too (few|many) arguments|no matching function for call|cannot be applied", "WrongArguments"),
    (r"redefinition of|redeclaration of|conflicting types for", "DuplicateDeclaration"),
    (r"assignment of read-only|cannot assign to .*const|assignment of member .* in read-only",
     "FinalReassignment"),
    (r"no match for 'operator|invalid operands to binary|invalid operands of types",
     "BadOperandTypes"),
    (r"incompatible types|invalid conversion from|cannot convert|incompatible pointer|"
     r"assignment to expression with array type|makes (integer|pointer) from",
     "TypeMismatch"),
    (r"control reaches end of non-void function|no return statement", "MissingReturn"),
    (r"is used uninitialized|may be used uninitialized", "UninitializedVariable"),
    (r"format '%.*' expects|format '%.*' .* but argument", "FormatMismatch"),
    (r"expected expression|expected primary-expression|stray '|expected unqualified-id|"
     r"expected declaration specifiers|expected identifier", "SyntaxError"),
]


def match_compiler_message(language, message):
    patterns = JAVA_PATTERNS if language == "Java" else C_FAMILY_PATTERNS
    for pattern, name in patterns:
        if re.search(pattern, message):
            return name
    return "CompilationError"
