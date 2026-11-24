class ErrorInfo:
    """Common error format shared by every language.

    `error_name` and `category` are normalised across languages, while
    `raw_message` always keeps the original compiler / interpreter text.
    """

    def __init__(
        self,
        language,
        category,
        error_name,
        message,
        line_number=None,
        code=None,
        raw_message=None,
        column=None,
        phase=None
    ):
        self.language = language
        self.category = category
        self.error_name = error_name
        self.message = message
        self.line_number = line_number
        self.code = code
        self.raw_message = raw_message if raw_message is not None else message
        self.column = column
        self.phase = phase  # "compile" or "runtime"

    def to_dict(self):
        return {
            "language": self.language,
            "category": self.category,
            "error_name": self.error_name,
            "message": self.message,
            "line_number": self.line_number,
            "code": self.code,
            "raw_message": self.raw_message,
            "column": self.column,
            "phase": self.phase
        }

    def display(self):
        for key, value in self.to_dict().items():
            print(f"{key}: {value}")
