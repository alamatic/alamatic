
from alamatic.parser import parse_module
from alamatic.compilelogging import (
    CompilerError,
    LogLine,
    INFO,
    WARNING,
    ERROR,
    CompileLogHandler,
)


__all__ = [
    "CompileState",
]


class CompileState(object):

    def __init__(self, log_handler=CompileLogHandler()):
        self.log_handler = log_handler
        self.log_type_counts = {
            INFO: 0,
            WARNING: 0,
            ERROR: 0,
        }

    def log(self, type, parts):
        self.log_handler(LogLine(type, parts))
        self.log_type_counts[type] = self.log_type_counts[type] + 1

    def error(self, *parts):
        if type(parts[0]) is CompilerError:
            self.log_handler(parts[0].log_line)
            level = parts[0].log_line.level
            self.log_type_counts[level] = self.log_type_counts[level] + 1
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
