from analyzer.java_analyzer import JavaAnalyzer
from analyzer.native_analyzer import CAnalyzer, CppAnalyzer
from analyzer.python_analyzer import PythonAnalyzer

ALIASES = {
    "python": "python", "py": "python", "python3": "python",
    "java": "java",
    "c": "c",
    "c++": "c++", "cpp": "c++", "cxx": "c++", "cplusplus": "c++",
}
BY_EXTENSION = {".py": "Python", ".java": "Java", ".c": "C",
                ".cpp": "C++", ".cc": "C++", ".cxx": "C++"}


class LanguageManager:
    def __init__(self):
        self.analyzers = {
            "python": PythonAnalyzer(),
            "java": JavaAnalyzer(),
            "c": CAnalyzer(),
            "c++": CppAnalyzer(),
        }

    def get_analyzer(self, language):
        if not isinstance(language, str):
            return None
        key = ALIASES.get(language.strip().lower())
        return self.analyzers.get(key) if key else None

    def canonical_name(self, language):
        analyzer = self.get_analyzer(language)
        return analyzer.language if analyzer else language

    def describe(self):
        return [
            {
                "name": analyzer.language,
                "extension": analyzer.extension,
                "available": analyzer.is_available(),
                "note": "" if analyzer.is_available() else analyzer.availability_note(),
            }
            for analyzer in self.analyzers.values()
        ]
