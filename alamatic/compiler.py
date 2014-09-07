
from alamatic.compilelogging import (
    CompilerError,
    LogLine,
    INFO,
    WARNING,
    ERROR,
    CompileLogHandler,
)

from alamatic.parser import parse_entry_file
from alamatic.intermediate import Program
from alamatic.preprocessor import preprocess_cfg


__all__ = [
    "CompileState",
]


def prepare_program(state, stream, filename):
    entry_file = parse_entry_file(state, stream, filename)

    entry_task = entry_file.get_intermediate_form()
    preprocessor_result = preprocess_cfg(entry_task.graph)

    return Program(
        entry_task,
        preprocessor_result,
    )


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
        if isinstance(parts[0], CompilerError):
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
