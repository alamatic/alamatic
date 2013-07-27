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
        self.parent = parent_state
        self.symbol_storages = {}
        self.storage_values = {}

    def get_symbol_value(self, symbol):
        storage = self.get_symbol_storage(symbol)
        if storage is None:
            return None
        return self.get_storage_value(storage)

    def get_symbol_storage(self, symbol):
        return _search_tables(self, "symbol_storages", symbol)

    def get_storage_value(self, storage):
        return _search_tables(self, "storage_values", storage)

    def set_symbol_value(self, symbol, value):
        """
        Set the compile-time value for the given symbol, overwriting any
        previous value in this state.

        If the value is _not_ known at compile time, use
        :py:meth:`clear_symbol_value` instead, to make the undefined
        nature of it known to subsequent code.

        A symbol can change type over the lifetime of the program, but
        it can only have one type at a time. When multiple types are used,
        the largest of the set will decide the amount of memory allocated
        to the type at runtime, if the symbol is used at runtime.
        """
        # FIXME: Should detect if we're switching to a new storage and
        # kill the value for the old one from self.storage_values, since
        # it can never be reached again anyway so is just wasting memory.
        storage = symbol.get_storage_for_type(type(value))
        self.symbol_storages[symbol] = storage
        self.storage_values[storage] = value

    def clear_symbol_value(self, symbol):
        try:
            storage = self.symbol_storages[symbol]
        except KeyError:
            return

        try:
            del self.storage_values[storage]
        except KeyError:
            pass

        # We set this to None explicitly rather than deleting it so we
        # can distinguish between two sitations: either this state has
        # no opinion on the given symbol and defers to its parent (not present
        # at all) or this state considers the given symbol to be unknown,
        # temporarily masking the parent's opinion (explicitly set to None).
        self.symbol_storages[symbol] = None

    def create_child(self):
        return DataState(parent_state=self)


class Symbol(object):

    def __init__(self):
        self.storage_by_type = {}

    def get_storage_for_type(self, type):
        """
        Get this symbol's storage for the given type.

        If the symbol doesn't yet have a storage for the given type, one is
        created. It is guaranteed that repeated calls to this method with
        the same type will return the same storage object.
        """
        try:
            return self.storage_by_type[type]
        except KeyError:
            self.storage_by_type[type] = Storage(type)
            return self.storage_by_type[type]


class Storage(object):

    def __init__(self, type):
        self.type = type


class CallFrame(object):
    def __init__(self, parent=None):
        self.parent = parent

    def create_child(self):
        return CallFrame(parent=self)

    @property
    def trace(self):
        current = self
        while current is not None:
            yield current
            current = current.parent
