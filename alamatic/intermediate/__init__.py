
from alamatic.compilelogging import CompilerError, pos_link
from alamatic.intermediate.symbols import *
from alamatic.intermediate.instructions import *
from alamatic.intermediate.operations import *
from alamatic.intermediate.constanttypes import *
from alamatic.intermediate.operands import *
from alamatic.intermediate.unit import *
from alamatic.intermediate.controlflowgraph import *
from alamatic.intermediate.base import *
from alamatic.intermediate.program import *


class SymbolTable(object):

    def __init__(self, parent=None):
        self.parent = parent
        self.children = []
        self.symbols_by_name = {}
        # Keep a separate list because we need to keep track of
        # every symbol we've issued, even if one is subsequently
        # hidden by a later declaration with the same name.
        self.named_symbols = []
        self.temporaries = []
        self.next_temporary_index = 1
        self._break_label = None
        self._continue_label = None

    def lookup(self, name, position=None):
        current = self
        while current is not None:
            try:
                return current.symbols_by_name[name]
            except KeyError:
                current = current.parent
        raise UnknownSymbolError(
            "Unknown symbol '%s' at " % name,
            pos_link(position),
        )

    @property
    def all_symbols(self):
        for symbol in self.named_symbols:
            yield symbol
        for symbol in self.temporaries:
            yield symbol
        for child_symbols in self.children:
            for symbol in child_symbols.all_symbols:
                yield symbol

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
            self.symbols_by_name[symbol.decl_name] = symbol
            self.named_symbols.append(symbol)
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

    def create_child(self, disconnected=False):
        child = SymbolTable(self)
        if not disconnected:
            # A "disconnected" child can access symbols from its parent
            # but it's not included when we traverse down the tree to
            # flatten out the symbol table. Thus this flag should be used
            # in cases where the child represents a separated execution
            # context, such as the body of a function declaration.
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
