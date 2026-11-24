"""Curated beginner practice questions. Expected answers stay on the server.

Every question lists the languages it can be solved in; starter code is built
per language from a short `setup` snippet.
"""

SKELETONS = {
    "Python": "{setup}# Write your code here\n",
    "Java": "public class Main {{\n    public static void main(String[] args) {{\n{setup}        // Write your code here\n    }}\n}}\n",
    "C": "#include <stdio.h>\n\nint main() {{\n{setup}    // Write your code here\n    return 0;\n}}\n",
    "C++": "#include <iostream>\n#include <string>\nusing namespace std;\n\nint main() {{\n{setup}    // Write your code here\n    return 0;\n}}\n",
}
ALL = ["Python", "Java", "C", "C++"]


def _indent(text, spaces):
    if not text:
        return ""
    pad = " " * spaces
    return "".join(f"{pad}{line}\n" for line in text.split("\n"))


def _starters(setup, languages):
    result = {}
    for language in languages:
        text = setup.get(language, setup.get("*", ""))
        if language == "Python":
            body = (text + "\n") if text else ""
        elif language == "Java":
            body = _indent(text, 8)
        else:
            body = _indent(text, 4)
        result[language] = SKELETONS[language].format(setup=body)
    return result


def _problem(key, title, concept, description, expected, hint, setup=None,
             languages=ALL, difficulty="beginner"):
    starters = _starters(setup or {}, languages)
    return {
        "key": key, "title": title, "concept": concept, "description": description,
        "difficulty": difficulty, "languages": list(languages), "starters": starters,
        "starter_code": starters["Python"] if "Python" in starters else next(iter(starters.values())),
        "expected_output": expected, "hint": hint,
    }


class ProblemGenerator:
    problems = {p["key"]: p for p in [
        _problem("indexing", "Access the final list element", "List Indexing",
                 "Given the values 4, 8, 12, 16 in a list (array), print the final element.",
                 "16", "The last valid index is one less than the number of items.",
                 {"Python": "values = [4, 8, 12, 16]", "*": "int values[] = {4, 8, 12, 16};",
                  "Java": "int[] values = {4, 8, 12, 16};"}),
        _problem("variables", "Variable Definition", "Variables",
                 "Create a variable named score with value 25 and print it.",
                 "25", "Assign a value before using a variable."),
        _problem("division", "Safe Division", "Arithmetic",
                 "Set numerator = 20 and denominator = 4. Print the quotient (Python prints 5.0).",
                 "5.0", "Use the division operator.",
                 {"Python": "numerator = 20\ndenominator = 4"}, languages=["Python"]),
        _problem("logic", "Calculate Total", "Logical Thinking",
                 "Set price = 12 and quantity = 3. Print their product.",
                 "36", "Multiply the price by the quantity.",
                 {"Python": "price = 12\nquantity = 3", "*": "int price = 12;\nint quantity = 3;"}),
        _problem("loops", "Count to five", "Loops",
                 "Print the numbers 1 to 5, one per line.",
                 "1\n2\n3\n4\n5", "A for loop can repeat a print statement. Check where it starts and stops."),
        _problem("conditions", "Even or odd", "Conditions",
                 "Set number = 10. Print Even if it is even, otherwise print Odd.",
                 "Even", "A number is even when the remainder after dividing by 2 is 0.",
                 {"Python": "number = 10", "*": "int number = 10;"}),
        _problem("strings", "Word length", "Strings",
                 'Given the word "programming", print how many characters it has.',
                 "11", "Most languages offer a length function or method for text.",
                 {"Python": 'word = "programming"', "Java": 'String word = "programming";',
                  "C": 'char word[] = "programming";', "C++": 'string word = "programming";'}),
        _problem("sum", "Sum of numbers", "Accumulating values",
                 "Given the numbers 3, 5, 7, 9, print their sum.",
                 "24", "Start a total at 0 and add each number to it.",
                 {"Python": "numbers = [3, 5, 7, 9]", "*": "int numbers[] = {3, 5, 7, 9};",
                  "Java": "int[] numbers = {3, 5, 7, 9};"}),
    ]}

    aliases = {
        "list_indexing": "indexing", "list": "indexing",
        "variable": "variables", "variable_definition": "variables",
        "arithmetic": "division", "safe_division": "division",
        "logical_thinking": "logic", "calculation": "logic",
        "loop": "loops", "condition": "conditions", "if": "conditions",
        "string": "strings", "accumulating_values": "sum",
    }

    def get_problem(self, concept):
        if not isinstance(concept, str):
            return None
        key = concept.strip().lower().replace(" ", "_")
        key = self.aliases.get(key, key)
        problem = self.problems.get(key)
        return dict(problem) if problem else None

    def generate(self, concept):
        return self.get_problem(concept)

    def list_concepts(self):
        return [
            {"key": item["key"], "concept": item["concept"], "title": item["title"],
             "difficulty": item["difficulty"], "languages": item["languages"]}
            for item in self.problems.values()
        ]
