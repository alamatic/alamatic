"""
Functionality related to the runtime state of the interpreter.

A symbol table (:py:class:`SymbolTable`) maps simple names to
:py:class:`Symbol` objects, which exist independently of their names.

Each symbol has a particular type that persists over the course of its life.
The current value for each symbol lives inside :py:class:`DataState` instances,
with each statement evaluated in the context of a particular symbol table
_and_ data state. Child data states are the mechanism by which we can evaluate
both branches of an if statement whose condition cannot be fully evaluated at
compile time.
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
                    root_data.finalize_values()
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

    def declare(self, name, type_, initial_value=None, const=False):
        symbol = self.symbols.create_symbol(
            name,
            type_,
            const=const,
        )
        if initial_value is not None:
            self.data.set_symbol_value(symbol, initial_value)
        else:
            self.data.clear_symbol_value(symbol, type_)

    def assign(self, name, value):
        symbol = self.symbols.get_symbol(name)
        try:
            self.data.set_symbol_value(symbol, value)
        except CannotChangeConstantError, ex:
            # re-raise with the symbol_name populated
            raise CannotChangeConstantError(
                usage_position=ex.usage_position,
                symbol_name=name,
            )

    def mark_unknown(self, name, known_type=None):
        symbol = self.symbols.get_symbol(name)
        self.data.clear_symbol_value(symbol, known_type=known_type)

    def get_symbol(self, name):
        return self.symbols.get_symbol(name)

    def retrieve(self, name):
        symbol = self.symbols.get_symbol(name)
        return self.data.get_symbol_value(symbol)

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

    def mark_symbol_used_at_runtime(self, symbol, position):
        self.data.mark_symbol_used_at_runtime(symbol, position)

    def get_runtime_usage_position(self, symbol):
        return self.data.get_runtime_usage_position(symbol)


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

    def create_symbol(self, name, type_, const=False):
        # If the name was already used then we'll "lose" the symbol
        # that was there before, but that's okay because any code we
        # already generated that refers to the old symbol will still
        # have a reference to it.
        self.symbols[name] = Symbol(type_, const=const)
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
        self.symbol_values = {}
        self.used_at_runtime = {}

    def get_symbol_value(self, symbol):
        return _search_tables(self, "symbol_values", symbol)

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
        if symbol.const:
            runtime_usage_pos = self.get_runtime_usage_position(symbol)
            if runtime_usage_pos is not None:
                raise CannotChangeConstantError(
                    usage_position=runtime_usage_pos,
                )

        if type(value) is not symbol.type:
            # We can't generate a very helpful error message in this context
            # so a caller handling an assignment ought to catch and re-raise
            # this with a bit more context about what's being assigned to.
            raise IncompatibleTypesError(
                "Can't assign a ", type(value), " value to a ",
                "symbol of type ", symbol.type, "."
            )

        self.symbol_values[symbol] = value

    def clear_symbol_value(self, symbol, known_type=None):

        if known_type is not None:
            if known_type is not symbol.type:
                raise IncompatibleTypesError(
                    "Can't assign a ", known_type, " value to a ",
                    "symbol of type ", symbol.type, "."
                )

        self.symbol_values[symbol] = None

    def mark_symbol_used_at_runtime(self, symbol, position):
        try:
            _search_tables(self, "used_at_runtime", symbol)
        except KeyError:
            self.used_at_runtime[symbol] = position

    def get_runtime_usage_position(self, symbol):
        """
        Given a symbol, returns the first source position at which the symbol
        was used (or possibly used) at runtime, or ``None`` if the symbol has
        not yet been used at runtime.
        """
        try:
            return _search_tables(self, "used_at_runtime", symbol)
        except KeyError:
            return None

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
            self, "symbol_values", children, or_none=or_none
        )
        # For the "used at runtime" we don't bother with the "maybe" case
        # because even a possible use requires us to definitely allocate
        # the item at runtime, just in case it's used.
        for child in children:
            for item, position in child.used_at_runtime.iteritems():
                if item not in self.used_at_runtime:
                    self.used_at_runtime[item] = position

    def __enter__(self):
        self.previous_state = interpreter.data
        interpreter.data = self
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        interpreter.data = self.previous_state

    def finalize_values(self):
        """
        Once the interpreter phase has finished, call this method on the root
        data state to commit all of the final symbol/storage state directly
        to the objects themselves, so that it's visible to the code
        generation phase.
        """
        for symbol, value in self.symbol_values.iteritems():
            if symbol.const and value is None:
                # TODO: Need to retain information about declaration/assignment
                # positions of symbols so we can actually include a useful
                # source code position in this error message... otherwise
                # this message is useless when it comes to fixing the issue.
                raise NotConstantError(
                    "Value of constant not known at compile time"
                )

            symbol.final_value = value

        for item, runtime_usage_position in self.used_at_runtime.iteritems():
            item.final_runtime_usage_position = runtime_usage_position


class Symbol(object):

    def __init__(self, type_, const=False):
        self.type = type_
        self.const = const
        # These will be populated by DataState.finalize_values once we're
        # done with the interpreter phase.
        self.final_type = None
        self.final_runtime_usage_position = None

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


class IncompatibleTypesError(CompilerError):
    pass


class NotConstantError(CompilerError):
    pass


class CannotChangeConstantError(CompilerError):
    # This is a bit of a weird one since the data required to build this
    # exception is spread across multiple layers. Therefore we raise this
    # error initially with just usage_position defined, and then the caller
    # that knows the symbol_name catches it and re-raises it, and finally
    # the caller that knows the assign position (if any) catches it and
    # re-raises it once more.
    def __init__(self, usage_position, symbol_name=None, assign_position=None):
        self.usage_position = usage_position
        self.symbol_name = symbol_name
        self.assign_position = assign_position
        if symbol_name is not None:
            symbol_disp = "constant '%s'" % symbol_name
        else:
            symbol_disp = "constant"
        if assign_position:
            message = [
                "Can't assign to ", symbol_disp, " at ",
                pos_link(assign_position), " because it was used at runtime ",
                " at ", pos_link(usage_position)
            ]
        else:
            message = [
                "Can't assign to ", symbol_disp,
                " because it was used at runtime ",
                " at ", pos_link(usage_position)
            ]
        CompilerError.__init__(self, *message)
    pass
