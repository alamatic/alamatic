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

    def declare(self, name, initial_value=None, const=False):
        symbol = self.symbols.create_symbol(name, const=const)
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


def _merge_possible_child_tables(orig, table_name, possibles, or_none=False):
    if len(possibles) == 0:
        return

    # Sanity check: make sure all of the possibles are children of
    # the original, or crazy things will happen.
    for possible in possibles:
        if possible.parent != orig:
            raise Exception(
                "Can't merge %s for %r into %r: not a child" % (
                    table_name, possible, original,
                )
            )

    orig_table = getattr(orig, table_name)
    possible_tables = [
        getattr(possible, table_name) for possible in possibles
    ]

    keys = set([])
    # Add to the keyset only those keys where one of the possibles
    # disagrees with the original.
    for possible_table in possible_tables:
        for key in possible_table.iterkeys():
            mine = orig_table.get(key, None)
            theirs = possible_table[key]
            if mine != theirs:
                keys.add(key)

    for key in keys:
        chosen_values = []
        try:
            for possible in possibles:
                chosen_values.append(
                    _search_tables(possible, table_name, key)
                )
        except KeyError:
            chosen_values.append(None)

        if or_none:
            chosen_values.append(
                _search_tables(orig, table_name, key)
            )

        all_agreed = all(
            chosen_values[0] == chosen_value
            for chosen_value in chosen_values
        )
        if all_agreed:
            orig_table[key] = chosen_values[0]
        else:
            # Signal that the true result is unknown
            orig_table[key] = None


class SymbolTable(object):

    def __init__(self, parent_table=None):
        self.parent = parent_table
        self.symbols = {}

    def get_symbol(self, name):
        return _search_tables(self, "symbols", name)

    def create_symbol(self, name, const=False):
        # If the name was already used then we'll "lose" the symbol
        # that was there before, but that's okay because any code we
        # already generated that refers to the old symbol will still
        # have a reference to it.
        self.symbols[name] = Symbol(const=const)
        return self.symbols[name]

    def create_child(self):
        return SymbolTable(parent_table=self)

    @property
    def local_symbols(self):
        return self.symbols.values()

    @property
    def all_names(self):
        if self.parent is None:
            ret = set([])
        else:
            ret = self.parent.all_names
        ret.update(self.symbols.keys())
        return ret

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

    def merge_children(self, children, or_none=False):
        """
        Given an iterable of child states representing possible outcomes,
        merge these back into their parent.

        This method will investigate which data still has a known value
        if we consider that any one of the given children may be selected
        at runtime. If `or_none` is set, the method will also allow for the
        possibility that _none_ of the given children may be selected,
        such as is the case when there's an ``if`` statement with no ``else``
        clause.
        """
        _merge_possible_child_tables(
            self, "symbol_storages", children, or_none=or_none
        )
        _merge_possible_child_tables(
            self, "storage_values", children, or_none=or_none
        )

    def __enter__(self):
        self.previous_state = interpreter.data
        interpreter.data = self
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        interpreter.data = self.previous_state


class Symbol(object):

    def __init__(self, const=False):
        self.storage_by_type = {}
        self.const = const

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
            self.storage_by_type[type] = Storage(self, type)
            return self.storage_by_type[type]

    @property
    def storages(self):
        return self.storage_by_type.values()

    @property
    def codegen_name(self):
        return "_ala_%x" % id(self)

    @property
    def codegen_uses_union(self):
        # We only use a union for a variable that has several different
        # storages during its life.
        # We flatten constants because a constant union doesn't make
        # much sense anyway.
        # We flatten single-storage variables to help the C compiler
        # optimize access to them better.
        if self.const:
            return False
        elif len(self.storage_by_type) < 2:
            return False
        else:
            return True


class Storage(object):

    def __init__(self, symbol, type):
        self.symbol = symbol
        self.type = type

    @property
    def codegen_name(self):
        return "_ala_%x" % id(self)


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


class NotConstantError(CompilerError):
    pass
