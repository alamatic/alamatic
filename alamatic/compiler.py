
from alamatic.parser import parse_module
from alamatic.compilelogging import (
    CompilerError,
    LogLine,
    INFO,
    WARNING,
    ERROR,
)


__all__ = [
    "CompileState",
]


class CompileState(object):

    def __init__(self):
        self.log_lines = []
        self.log_type_counts = {
            INFO: 0,
            WARNING: 0,
            ERROR: 0,
        }

    def log(self, type, parts):
        self.log_lines.append(LogLine(type, parts))
        self.log_type_counts[type] = self.log_type_counts[type] + 1

    def error(self, *parts):
        if type(parts[0]) is CompilerError:
            self.log_lines.append(parts[0].log_line)
        else:
            self.log(ERROR, parts)

    def warn(self, *parts):
        self.log(WARNING, parts)

    def info(self, *parts):
        self.log(INFO, parts)

    @property
    def error_count(self):
        return self.log_type_counts[ERROR]

    @property
    def warning_count(self):
        return self.log_type_counts[WARNING]
