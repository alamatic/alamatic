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

    def declare(self, name, type=None, const=False, position=None):
        self._declare(
            name,
            type_=type,
            const=const,
            position=position,
        )

    def declare_and_init(
        self,
        name,
        initial_value,
        const=False,
        position=None,
    ):
        self._declare(
            name,
            initial_value=initial_value,
            const=const,
            position=position,
        )

    def _declare(
        self,
        name,
        type_=None,
        initial_value=None,
        const=False,
        position=None,
    ):
        symbol = self.symbols.create_symbol(
            name,
            const=const,
            decl_position=position,
        )
        if type_ is not None and initial_value is not None:
            raise Exception(
                "When declaring a symbol, set either type_ or initial_value "
                "but not both."
            )
        if initial_value is not None:
            self.data.set_symbol_value(
                symbol,
                initial_value,
                position=position,
            )
        else:
            # type_ might still be None here, meaning we don't know
            # what the type is at declaration time. We'll figure it out
            # when the symbol is initialized (assigned for the first time)
            self.data.clear_symbol_value(
                symbol,
                type_,
                position=position,
            )

    def assign(self, name, value, position=None):
        symbol = self.symbols.get_symbol(name)
        self.data.set_symbol_value(
            symbol,
            value,
            position=position,
        )

    def mark_unknown(self, name, known_type=None, position=None):
        symbol = self.symbols.get_symbol(name)
        self.data.clear_symbol_value(
            symbol,
            known_type=known_type,
            position=position,
        )

    def set_symbol_value(self, symbol, value, position=None):
        self.data.set_symbol_value(
            symbol,
            value,
            position=position,
        )

    def mark_symbol_unknown(self, symbol, known_type=None, position=None):
        self.data.clear_symbol_value(
            symbol,
            known_type=known_type,
            position=position,
        )

    def get_symbol(self, name, position=None):
        return self.symbols.get_symbol(name, position=position)

    def retrieve(self, name, position=None):
        symbol = self.symbols.get_symbol(name, position=position)
        return self.data.get_symbol_value(symbol, position=position)

    def get_symbol_type(self, symbol, position=None):
        return self.data.get_symbol_type(symbol, position=position)

    def symbol_is_initialized(self, symbol):
        return self.data.symbol_is_initialized(symbol)

    def is_initialized(self, name):
        return self.symbol_is_initialized(self.get_symbol(name))

    def get_type(self, name, position=None):
        return self.get_symbol_type(
            self.get_symbol(name, position=position),
            position=position,
        )

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
        if not self.data.symbol_is_initialized(symbol):
            return False
        try:
            value = self.data.get_symbol_value(symbol)
        except SymbolValueNotKnownError:
            return False
        else:
            return True

    def mark_symbol_used_at_runtime(self, symbol, position):
        self.data.mark_symbol_used_at_runtime(symbol, position)

    def get_runtime_usage_position(self, symbol):
        return self.data.get_runtime_usage_position(symbol)


interpreter = Interpreter()


class PositionTrackingDict(dict):
    """
    Dictionary that can keep track of the source position responsible for
    each of its current values.

    The normal :py:class:`dict` methods work as normal, but additional
    methods are provided to get and set items annotated with position
    information.

    This class does not comprehensively support the dict interface, but rather
    just provides the parts that are used for interpreter state tables.
    """
    def __init__(self):
        self.positions = {}

    def set_with_position(self, key, value, position):
        self[key] = value
        self.positions[key] = position

    def get_with_position(self, key):
        return (self[key], self.positions.get(key, None))

    def get_position(self, key):
        return self.positions[key]

    def iteritems_with_position(self):
        for k, v in self.iteritems():
            yield (k, v, self.positions.get(k, None))

    def __delitem__(self, key):
        raise NotImplementedError("Can't delete from a PositionTrackingDict")

    def clear(self):
        raise NotImplementedError("Can't clear a PositionTrackingDict")


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


def _search_tables_with_position(start, table_name, key):
    current = start
    value = None

    while current is not None:
        table = getattr(current, table_name)
        try:
            value = table.get_with_position(key)
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
                    _search_tables_with_position(possible, table_name, key)
                )
        except KeyError:
            chosen_values.append((None, None))

        if or_none:
            chosen_values.append(
                _search_tables_with_position(orig, table_name, key)
            )

        all_agreed = all(
            chosen_values[0][0] == chosen_value[0]
            for chosen_value in chosen_values
        )
        if all_agreed:
            orig_table.set_with_position(
                key,
                chosen_values[0][0],
                chosen_values[0][1],
            )
        else:
            # Signal that the true result is unknown
            orig_table[key] = MergeConflict(
                chosen_values
            )


class SymbolTable(object):

    def __init__(self, parent_table=None):
        self.parent = parent_table
        self.symbols = {}

    def get_symbol(self, name, position=None):
        try:
            return _search_tables(self, "symbols", name)
        except KeyError:
            raise UnknownSymbolError(
                "Symbol '%s' is not defined at " % name,
                pos_link(position),
            )

    def create_symbol(self, name, const=False, decl_position=None):
        # If the name was already used then we'll "lose" the symbol
        # that was there before, but that's okay because any code we
        # already generated that refers to the old symbol will still
        # have a reference to it.
        self.symbols[name] = Symbol(
            const=const,
            decl_name=name,
            decl_position=decl_position,
        )
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
        self.symbol_values = PositionTrackingDict()
        self.symbol_types = PositionTrackingDict()
        self.used_at_runtime = {}

    def symbol_is_initialized(self, symbol):
        try:
            symbol_type = self.get_symbol_type(symbol)
        except SymbolTypeAmbiguousError:
            return True
        except SymbolNotInitializedError:
            return False
        else:
            return True

    def get_symbol_type(self, symbol, position=None):
        try:
            result = _search_tables(self, "symbol_types", symbol)
        except KeyError:
            result = None

        if type(result) is MergeConflict:
            raise SymbolTypeAmbiguousError(
                "Symbol '%s' does not have a consistent type" % (
                    symbol.decl_name
                ),
                " at ", pos_link(position)
            )
        elif result is None:
            raise SymbolNotInitializedError(
                "Symbol '%s' has not yet been initialized" % symbol.decl_name,
                " at ", pos_link(position)
            )
        else:
            return result

    def get_symbol_value(self, symbol, position=None):
        # First look up the symbol's type just so we can fail early if it's
        # not in a consistent state yet.
        self.get_symbol_type(symbol, position=position)

        try:
            result = _search_tables(self, "symbol_values", symbol)
        except KeyError:
            result = None

        if result is None:
            raise SymbolValueNotKnownError(
                "Value of symbol '%s' is not known at " % (
                    symbol.decl_name
                ),
                pos_link(position),
            )
        elif type(result) is MergeConflict:
            raise SymbolValueAmbiguousError(
                "Value of symbol '%s' is ambiguous  at " % (
                    symbol.decl_name
                ),
                pos_link(position)
            )
        else:
            return result

    def set_symbol_value(self, symbol, value, position=None):
        """
        Set the compile-time value for the given symbol, overwriting any
        previous value in this state.

        If the value is _not_ known at compile time, use
        :py:meth:`clear_symbol_value` instead, to make the undefined
        nature of it known to subsequent code.

        The first call for a particular symbol is the initializer for that
        symbol, which defines its type. All subsequent assignments must then
        conform to that type.
        """
        if symbol.const:
            runtime_usage_pos = self.get_runtime_usage_position(symbol)
            if runtime_usage_pos is not None:
                raise CannotChangeConstantError(
                    "Can't change constant '%s' at " % symbol.decl_name,
                    pos_link(position),
                    " because it was already used at runtime at ",
                    pos_link(runtime_usage_pos),
                )

        if self.symbol_is_initialized(symbol):
            symbol_type = self.get_symbol_type(symbol)
            if type(value) is not symbol_type:
                raise IncompatibleTypesError(
                    "Can't assign ", type(value), " to symbol '%s' " % (
                        symbol.decl_name,
                    ),
                    "(of type ", symbol_type, "), at ",
                    pos_link(position)
                )
        else:
            self.symbol_types.set_with_position(symbol, type(value), position)

        self.symbol_values.set_with_position(symbol, value, position)

    def clear_symbol_value(self, symbol, known_type=None, position=None):

        if known_type is not None:
            if self.symbol_is_initialized(symbol):
                symbol_type = self.get_symbol_type(symbol)
                if known_type is not symbol_type:
                    raise IncompatibleTypesError(
                        "Can't assign ", known_type, " to symbol '%s' " % (
                            symbol.decl_name,
                        ),
                        "(of type ", symbol_type, "), at ",
                        pos_link(position)
                    )
            else:
                self.symbol_types.set_with_position(
                    symbol, known_type, position,
                )

        self.symbol_values.set_with_position(symbol, None, position)

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
            self, "symbol_types", children, or_none=or_none
        )
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
        for symbol, value, pos in self.symbol_values.iteritems_with_position():
            if symbol.const and value is None:
                if symbol.decl_position and symbol.decl_name:
                    raise NotConstantError(
                        "Value of constant '%s' from " % symbol.decl_name,
                        pos_link(symbol.decl_position),
                        " does not have a definite value"
                    )
                else:
                    # Should never happen if everything's behaving well,
                    # unless the symbol is a dummy one created in a test.
                    raise NotConstantError(
                        "Value of anonymous constant not known at compile time"
                    )

            symbol.final_assign_position = pos
            symbol.final_value = value

        for symbol, type_, pos in self.symbol_types.iteritems_with_position():
            symbol.final_type = type_
            symbol.final_init_position = pos

        for item, runtime_usage_position in self.used_at_runtime.iteritems():
            item.final_runtime_usage_position = runtime_usage_position


class Symbol(object):

    def __init__(self, const=False, decl_position=None, decl_name=None):
        self.const = const
        # These will be populated by DataState.finalize_values once we're
        # done with the interpreter phase.
        self.final_type = None
        self.final_value = None
        self.final_runtime_usage_position = None
        self.final_init_position = None
        self.final_assign_position = None
        self.decl_position = decl_position
        self.decl_name = decl_name

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


class MergeConflict(object):

    def __init__(self, possibilities):
        self.possibilities = possibilities

    def __repr__(self):
        return "<MergeConflict %r>" % self.possibilities


class UnknownSymbolError(CompilerError):
    pass


class IncompatibleTypesError(CompilerError):
    pass


class SymbolTypeNotKnownError(CompilerError):
    pass


class SymbolNotInitializedError(SymbolTypeNotKnownError):
    pass


class SymbolTypeAmbiguousError(SymbolTypeNotKnownError):
    pass


class SymbolValueNotKnownError(CompilerError):
    pass


class SymbolValueAmbiguousError(SymbolValueNotKnownError):
    pass


class NotConstantError(CompilerError):
    pass


class CannotChangeConstantError(CompilerError):
    pass


class InvalidAssignmentError(CompilerError):
    pass
