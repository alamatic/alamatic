"""
Functionality related to the runtime state of the interpreter.

A symbol table (:py:class:`SymbolTable`) maps simple names to
:py:class:`Symbol` objects, which exist independently of their names.
A symbol can actually have several different types over the course of
its life, with each of these represented by a :py:class:`Storage` instance.

The selected storage for each symbol and the current value for each storage
live inside :py:class:`DataState` instances, with each statement evaluated
in the context of a particular symbol table _and_ data state; child data
states are the mechanism by which we can evaluate both branches of an if
statement whose condition cannot be fully evaluated at compile time.
"""


def _search_tables(start, table_name, key):
    current = start
    value = None

    while current is not None:
        table = getattr(current, table_name)
        try:
            value = table[key]
        except KeyError:
            current = current.parent
        else:
            return value

    raise KeyError(key)


class SymbolTable(object):

    def __init__(self, parent_table=None):
        self.parent = parent_table
        self.symbols = {}

    def get_symbol(self, name):
        return _search_tables(self, "symbols", name)

    def create_symbol(self, name):
        # If the name was already used then we'll "lose" the symbol
        # that was there before, but that's okay because any code we
        # already generated that refers to the old symbol will still
        # have a reference to it.
        self.symbols[name] = Symbol()
        return self.symbols[name]

    def create_child(self):
        return SymbolTable(parent_table=self)


class DataState(object):

    def __init__(self, parent_state=None):
        self.parent = parent_table
        self.symbol_storages = {}
        self.storage_values = {}

    def get_symbol_value(self, symbol):
        pass

    def set_symbol_value(self, symbol, value):
        pass

    def create_child(self):
        return DataState(parent_state=self)


class Symbol(object):
    pass


class Storage(object):
    pass


