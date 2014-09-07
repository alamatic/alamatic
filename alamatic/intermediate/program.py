
__all__ = [
    "Program",
]


class Program(object):
    """
    Represents a complete program.
    """

    def __init__(
        self,
        entry_task,
        preprocessor_result,
    ):
        self.entry_task = entry_task
        self.preprocessor_result = preprocessor_result
        self.context = preprocessor_result.context
