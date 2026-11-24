import unittest

from analyzer.analyzer import Analyzer

ANALYZER = Analyzer()


def available(language):
    return ANALYZER.language_manager.get_analyzer(language).is_available()


def needs(language):
    return unittest.skipUnless(available(language), f"{language} toolchain not installed")


def err(language, code, expected=None, stdin=""):
    result = ANALYZER.analyze(language, code, expected, stdin)
    return result, result.get("error")
