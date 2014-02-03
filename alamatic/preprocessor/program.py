
# This means that 'execute' must be loaded before us in __init__.py and
# any other place that loads both, or else we'll end up importing nothing.
from alamatic.preprocessor.execute import execute_unit


class Program(object):

    def __init__(self, entry_unit):
        self.entry_unit = entry_unit
        self.analysis = execute_unit(entry_unit)
