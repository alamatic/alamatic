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

from alamatic.compilelogging import CompilerError, pos_link


def execute_module(state, module):
    from alamatic.ast import Module
    old_state = interpreter.state
    interpreter.state = state
    try:
        with SymbolTable() as root_symbols:
            with DataState() as root_data:
                try:
                    runtime_block = module.block.execute()
                    return Module(module.position, module.name, runtime_block)
                except CompilerError, ex:
                    state.error(ex)
                else:
                    return None
    finally:
        interpreter.state = old_state


class Interpreter(object):

    symbols = None
    data = None
    frame = None
    state = None

    def child_symbol_table(self):
        return self.symbols.create_child()

    def child_data_state(self):
        return self.data.create_child()

    def child_symbol_table(self):
        return self.symbols.create_child()

    def declare(self, name, initial_value=None):
        symbol = self.symbols.create_symbol(name)
        if initial_value is not None:
            self.data.set_symbol_value(symbol, initial_value)
        else:
            self.data.mark_symbol_unknown(symbol)

    def assign(self, name, value):
        symbol = self.symbols.get_symbol(name)
        self.data.set_symbol_value(symbol, value)

    def mark_unknown(self, name, known_type=None):
        symbol = self.symbols.get_symbol(name)
        self.data.mark_symbol_unknown(symbol, known_type=known_type)

    def retrieve(self, name):
        symbol = self.symbols.get_symbol(name)
        return self.data.get_symbol_value(symbol)

    def get_storage(self, name):
        symbol = self.symbols.get_symbol(name)
        return self.data.get_symbol_storage(symbol)

    def name_is_defined(self, name):
        try:
            symbol = self.symbols.get_symbol(name)
        except KeyError:
            return False
        else:
            if symbol is None:
                return False
            else:
                return True

    def value_is_known(self, name):
        symbol = self.symbols.get_symbol(name)
        try:
            value = self.data.get_symbol_value(symbol)
        except KeyError:
            return False
        else:
            if value is None:
                return False
            else:
                return True

    def storage_is_known(self, name):
        symbol = self.symbols.get_symbol(name)
        try:
            storage = self.data.get_symbol_storage(symbol)
        except KeyError:
            return False
        else:
            if storage is None:
                return False
            else:
                return True


interpreter = Interpreter()


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

    def __enter__(self):
        self.previous_table = interpreter.symbols
        interpreter.symbols = self
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        interpreter.symbols = self.previous_table


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

    def mark_symbol_unknown(self, symbol, known_type=None):

        if known_type is not None:
            storage = symbol.get_storage_for_type(known_type)
            # FIXME: Should detect if we're switching to a new storage and
            # kill the value for the old one from self.storage_values, since
            # it can never be reached again anyway so is just wasting memory.
            self.symbol_storages[symbol] = storage
            self.storage_values[storage] = None
        else:
            self.symbol_storages[symbol] = None

    def create_child(self):
        return DataState(parent_state=self)

    def merge_child(self, child):
        if child.parent != self:
            raise Exception(
                "Can't merge %r into %r: not a child" % (
                    child,
                    self,
                )
            )
        for symbol in child.symbol_storages:
            self.symbol_storages[symbol] = child.symbol_storages[symbol]
        for storage in child.storage_values:
            self.storage_values[storage] = child.storage_values[storage]

    def combine(self, other, *others):
        """
        Given a bunch of states, return a new state that represents the
        situation after any one of the given states could've run.

        In other words, given the states from the if, elif and else clauses of
        an if statement, this returns what the state should look like in
        the code _following_ the whole if statement, assuming that we won't
        know until runtime which of the blocks will actually execute.
        """
        if self.parent != other.parent:
            raise Exception(
                "Can't combine %s and %s because parents don't match" % (
                    self,
                    other,
                )
            )
        symbols = (
            set(self.symbol_storages.iterkeys()) |
            set(other.symbol_storages.iterkeys())
        )
        storages = (
            set(self.storage_values.iterkeys()) |
            set(other.storage_values.iterkeys())
        )
        ret = DataState(parent_state=self.parent)

        for symbol in symbols:
            mine = self.symbol_storages.get(symbol)
            theirs = other.symbol_storages.get(symbol)
            if mine == theirs:
                ret.symbol_storages[symbol] = mine
            else:
                ret.symbol_storages[symbol] = None

        for storage in storages:
            mine = self.storage_values.get(storage)
            theirs = other.storage_values.get(storage)
            if mine == theirs:
                ret.storage_values[storage] = mine
            else:
                ret.storage_values[storage] = None

        if len(others) > 0:
            return ret.combine(*others)
        else:
            return ret

    def __enter__(self):
        self.previous_state = interpreter.data
        interpreter.data = self
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        interpreter.data = self.previous_state


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

    def __enter__(self):
        self.previous_frame = interpreter.frame
        interpreter.frame = self

    def __exit__(self, exc_type, exc_value, traceback):
        interpreter.frame = self.previous_frame


class UnknownSymbolError(CompilerError):
    def __init__(self, symbol_name, node):
        CompilerError.__init__(
            self,
            "Unknown symbol '", symbol_name,
            "' at ", pos_link(node.position),
        )


class InconsistentTypesError(CompilerError):
    pass


class IncompatibleTypesError(CompilerError):
    pass
