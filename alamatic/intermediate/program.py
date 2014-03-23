
class Program(object):
    """
    Represents a complete program, which is the result of running the
    preprocessor.
    """

    def __init__(
        self,
        entry_unit,
        symbol_values,
        imported_modules,
        called_functions
    ):
        self.entry_unit = entry_unit
        self.symbol_values = symbol_values
        self.imported_modules = imported_modules
        self.called_functions = called_functions

    @property
    def modules(self):
        for unit in self.imported_modules:
            yield unit

    @property
    def functions(self):
        for unit in self.modules:
            yield unit

        yield self.entry_unit
