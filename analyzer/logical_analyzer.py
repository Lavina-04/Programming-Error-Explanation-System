class LogicalAnalyzer:
    @staticmethod
    def normalize(value):
        text = str(value if value is not None else "")
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Ignore trailing spaces on each line and blank lines at the ends.
        return "\n".join(line.rstrip() for line in text.split("\n")).strip()

    def compare_outputs(self, actual_output, expected_output):
        actual = self.normalize(actual_output)
        expected = self.normalize(expected_output)
        return {
            "status": "correct" if actual == expected else "logical_error",
            "actual_output": actual,
            "expected_output": expected
        }
