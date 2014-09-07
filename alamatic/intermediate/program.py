
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
    ):
        self.entry_task = entry_task
