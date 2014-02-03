
from alamatic.compilelogging import CompilerError, pos_link
from alamatic.intermediate.symbols import *
from alamatic.intermediate.instructions import *
from alamatic.intermediate.operations import *
from alamatic.intermediate.operands import *
from alamatic.intermediate.unit import *
from alamatic.intermediate.controlflowgraph import *
from alamatic.intermediate.base import *


class SymbolTable(object):

    def __init__(self, parent=None):
        self.parent = parent
        self.children = []
        self.symbols = {}
        self.temporaries = []
        self.next_temporary_index = 1
        self._break_label = None
        self._continue_label = None

    def lookup(self, name, position=None):
        current = self
        while current is not None:
            try:
                return current.symbols[name]
            except KeyError:
                current = current.parent
        raise UnknownSymbolError(
            "Unknown symbol '%s' at " % name,
            pos_link(position),
        )

    @property
    def locals(self):
        return self.symbols.itervalues()

    @property
    def break_label(self):
        current = self
        while current is not None:
            if current._break_label is not None:
                return current._break_label
            current = current.parent
        return None

    @break_label.setter
    def break_label(self, value):
        self._break_label = value

    @property
    def continue_label(self):
        current = self
        while current is not None:
            if current._continue_label is not None:
                return current._continue_label
            current = current.parent
        return None

    @continue_label.setter
    def continue_label(self, value):
        self._continue_label = value

    def declare(self, name, const=False, position=None):
        symbol = self.begin_declare(name, const=const, position=position)
        self.complete_declare(symbol)
        return symbol

    def begin_declare(self, name, const=False, position=None):
        return NamedSymbol(self, name, const, position)

    def complete_declare(self, symbol):
        if isinstance(symbol, NamedSymbol):
            self.symbols[symbol.decl_name] = symbol
        else:
            # Should never happen
            raise Exception(
                "Can only complete declaration of a named symbol."
            )

    def create_temporary(self):
        index = self.next_temporary_index
        self.next_temporary_index += 1
        symbol = TemporarySymbol(self, index)
        self.temporaries.append(symbol)
        return symbol

    def create_child(self):
        child = SymbolTable(self)
        self.children.append(child)
        return child


class IncompatibleTypesError(CompilerError):
    pass


class UnknownSymbolError(CompilerError):
    pass


class NotConstantError(CompilerError):
    pass


class InvalidLValueError(CompilerError):
    pass
