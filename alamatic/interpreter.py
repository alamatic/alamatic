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
import weakref


def make_runtime_program(state, entry_point_module):
    from alamatic.codegen import RuntimeProgram
    old_state = interpreter.state
    interpreter.state = state
    try:
        with SymbolTable() as root_symbols:
            with DataState() as root_data:
                with CallFrame() as root_frame:
                    try:
                        entry_point_function = entry_point_module.execute()
                        root_data.finalize_values()
                        return RuntimeProgram(
                            root_data.runtime_functions,
                            root_data.runtime_types,
                            root_data.top_level_scopes,
                            entry_point_function,
                        )
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

    def child_call_frame(self):
        return self.frame.create_child()

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
        self.data.declare_symbol(symbol, position=position)
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
        symbol = self.symbols.get_symbol(name, position=position)
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
        except UnknownSymbolError:
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

    def register_runtime_function(self, function):
        self.data.register_runtime_function(function)

    def register_runtime_type(self, type_):
        self.data.register_runtime_type(type_)

    def register_top_level_scope(self, symbols):
        self.data.register_top_level_scope(symbols)


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
            possibilities = []
            for possibility in chosen_values:
                if type(possibility[0]) is MergeConflict:
                    possibilities.extend(possibility[0].possibilities)
                else:
                    possibilities.append(possibility)
            orig_table.set_with_position(
                key,
                MergeConflict(
                    possibilities
                ),
                None,
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

    def generate_c_decls(self, state, writer):
        for symbol in self.local_symbols:
            symbol.generate_c_decl(state, writer)

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
        self.runtime_functions = set()
        self.runtime_types = set()
        self.top_level_scopes = set()
        self.used_at_runtime = {}

    def declare_symbol(self, symbol, position=None):
        self.symbol_types.set_with_position(symbol, None, position)

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
                "Symbol '%s' does not have a definite type" % (
                    symbol.decl_name
                ),
                " at ", pos_link(position),
                conflict=result,
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
                pos_link(position),
                conflict=result,
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
            symbol_type = self.get_symbol_type(symbol, position=position)
            if type(value) is not symbol_type:
                raise IncompatibleTypesError(
                    "Can't assign ", type(value).__name__,
                    " to symbol '%s' " % (
                        symbol.decl_name,
                    ),
                    "(of type ", symbol_type.__name__, "), at ",
                    pos_link(position)
                )
        else:
            self.symbol_types.set_with_position(symbol, type(value), position)

        self.symbol_values.set_with_position(symbol, value, position)

    def clear_symbol_value(self, symbol, known_type=None, position=None):
        from alamatic.types import Void

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
                # This case will arise if someone tries to initialize a
                # variable using a function call that returns no value.
                if known_type is Void:
                    raise InvalidAssignmentError(
                        "Can't initialize '%s' " % symbol.decl_name,
                        "with an expression that returns no value ",
                        "at ", pos_link(position),
                    )
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

    def register_runtime_function(self, function):
        self.runtime_functions.add(function)

    def register_runtime_type(self, type_):
        self.runtime_types.add(type_)

    def register_top_level_scope(self, symbols):
        self.top_level_scopes.add(symbols)

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
            self.runtime_functions = self.runtime_functions.union(
                child.runtime_functions
            )
            self.runtime_types = self.runtime_types.union(
                child.runtime_types
            )
            self.top_level_scopes = self.top_level_scopes.union(
                child.top_level_scopes
            )

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

    def __repr__(self):
        return "<alamatic.interpreter.Symbol %r (%s) from %r>" % (
            self.decl_name,
            self.codegen_name,
            self.decl_position,
        )

    @property
    def codegen_name(self):
        return "_ala_%x" % id(self)

    def generate_c_decl(self, state, writer):
        if self.final_runtime_usage_position is None:
            # Don't bother generating any symbols that aren't used
            # at runtime.
            return
        if self.const:
            writer.write("const ")
        if self.final_type is None:
            # Should never happen
            raise Exception(
                "Symbol used at runtime but never initialized"
            )
        writer.write(self.final_type.c_type_spec(), " ")
        writer.write(self.codegen_name)
        if self.const:
            writer.write(" = ")
            self.final_value.generate_c_code(state, writer)
        writer.writeln(";")


class RuntimeFunction(object):

    def __init__(
        self,
        decl_position,
        runtime_block,
        args_type,
        return_type,
    ):
        self.decl_position = decl_position
        self.runtime_block = runtime_block
        self.args_type = args_type
        self.return_type = return_type

    @property
    def codegen_name(self):
        return "_ala_%x" % id(self)

    def _generate_c_header(self, state, writer):
        writer.write(self.return_type.c_type_spec(), " ")
        writer.write(self.codegen_name)
        writer.write("(")
        self.args_type.generate_c_args_decl(state, writer)
        writer.write(")")

    def generate_c_forward_decl(self, state, writer):
        self._generate_c_header(state, writer)
        writer.writeln(";")

    def generate_c_decl(self, state, writer, include_data_decls=True):
        self._generate_c_header(state, writer)
        with writer.braces():
            if include_data_decls:
                self.runtime_block.generate_decl_c_code(state, writer)
            self.runtime_block.generate_body_c_code(state, writer)


class RuntimeFunctionArgs(object):

    subtypes = weakref.WeakValueDictionary()

    def __init__(self, arg_exprs):
        if type(self) is RuntimeFunctionArgs:
            raise Exception(
                "RuntimeFunctionArgs is an abstract class. "
                "Call RuntimeFunctionArgs.make_args_type to make a concrete "
                "subclass you can instantiate."
            )
        self.arg_exprs = arg_exprs

    @classmethod
    def make_args_type(cls, param_symbols):
        names_str = ",".join(
            ("const " if x.const else "") +
            interpreter.get_symbol_type(x).__name__
            for x in param_symbols
        )
        if names_str not in cls.subtypes:
            cls.subtypes[names_str] = type(
                "RuntimeFunctionArgs(%s)" % names_str,
                (RuntimeFunctionArgs,),
                {
                    "param_symbols": param_symbols,
                }
            )
        return cls.subtypes[names_str]

    @classmethod
    def generate_c_args_decl(cls, state, writer):
        first = True
        for symbol in cls.param_symbols:
            if symbol.const:
                continue
            if first:
                first = False
            else:
                writer.write(", ")
            writer.write(symbol.final_type.c_type_spec(), " ")
            writer.write(symbol.codegen_name)

    def generate_c_args_call(self, state, writer):
        pass


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
    def __init__(self, *args, **kwargs):
        self.conflict = kwargs.get("conflict")
        super(SymbolTypeAmbiguousError, self).__init__(*args)

    @property
    def additional_info_items(self):
        for possibility in self.conflict.possibilities:
            type_ = possibility[0]
            position = possibility[1]
            if type_ is not None:
                yield (
                    "Possibly initialized as %s at " % type_.__name__,
                    pos_link(position),
                )
            else:
                yield (
                    "Declared without initialization at ",
                    pos_link(position),
                )


class SymbolValueNotKnownError(CompilerError):
    pass


class SymbolValueAmbiguousError(SymbolValueNotKnownError):
    def __init__(self, *args, **kwargs):
        self.conflict = kwargs.get("conflict")
        super(SymbolValueAmbiguousError, self).__init__(*args)


class NotConstantError(CompilerError):
    pass


class CannotChangeConstantError(CompilerError):
    pass


class InvalidAssignmentError(CompilerError):
    pass


class InvalidParameterListError(CompilerError):
    pass
