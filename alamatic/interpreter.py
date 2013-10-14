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
import datafork
import weakref


def make_runtime_program(state, entry_point_module):
    from alamatic.codegen import RuntimeProgram
    old_state = interpreter.state
    interpreter.state = state
    try:
        with Registry() as root_registry:
            with SymbolTable() as root_symbols:
                with CallFrame() as root_frame:
                    try:
                        entry_point_function = entry_point_module.execute()
                        return RuntimeProgram(
                            root_registry.runtime_functions,
                            root_registry.runtime_types,
                            root_registry.runtime_top_level_scopes,
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
    registry = None
    frame = None
    state = None

    def child_symbol_table(self):
        return self.symbols.create_child()

    def child_registry(self):
        return self.registry.create_child()

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
        if type_ is not None and initial_value is not None:
            raise Exception(
                "When declaring a symbol, set either type_ or initial_value "
                "but not both."
            )
        if initial_value is not None:
            symbol.assign(initial_value, position=position)
        else:
            # type_ might still be None here, meaning we don't know
            # what the type is at declaration time. We'll figure it out
            # when the symbol is initialized (assigned for the first time)
            if type_ is not None:
                symbol.initialize(type_, position=position)

    def assign(self, name, value, position=None):
        symbol = self.symbols.get_symbol(name, position=position)
        self.set_symbol_value(symbol, value, position=position)

    def mark_unknown(self, name, known_type=None, position=None):
        symbol = self.symbols.get_symbol(name)
        self.mark_symbol_unknown(
            symbol,
            known_type=known_type,
            position=position,
        )

    def set_symbol_value(self, symbol, value, position=None):
        symbol.assign(value, position=position)

    def mark_symbol_unknown(self, symbol, known_type=None, position=None):
        symbol.mark_value_unknown(known_type=known_type, position=position)

    def get_symbol(self, name, position=None):
        return self.symbols.get_symbol(name, position=position)

    def retrieve(self, name, position=None):
        symbol = self.get_symbol(name, position=position)
        return symbol.get_value(position=position)

    def get_symbol_type(self, symbol, position=None):
        return symbol.get_type(position=position)

    def symbol_is_initialized(self, symbol):
        return symbol.is_initialized

    def is_definitely_initialized(self, name):
        return self.get_symbol(name).is_definitely_initialized

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
        if not symbol.is_definitely_initialized:
            return False
        try:
            value = symbol.get_value()
        except SymbolValueNotKnownError:
            return False
        else:
            return True

    def mark_symbol_used_at_runtime(self, symbol, position):
        symbol.mark_used_at_runtime(position=position)

    def get_runtime_usage_position(self, symbol):
        return symbol.runtime_usage_position

    def register_runtime_function(self, function):
        self.registry.register_runtime_function(function)

    def register_runtime_type(self, type_):
        self.registry.register_runtime_type(type_)

    def register_top_level_scope(self, symbols):
        self.registry.register_runtime_top_level_scope(symbols)


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


class Symbol(object):

    def __init__(self, const=False, decl_position=None, decl_name=None):
        if interpreter.registry is None:
            raise Exception("Can't create a symbol: no active registry")
        self.value_slot = interpreter.registry.create_slot()
        self.type_slot = interpreter.registry.create_slot()
        self.is_initialized_slot = interpreter.registry.create_slot()
        self.runtime_usage_position_slot = interpreter.registry.create_slot()
        self.const = const
        self.decl_position = decl_position
        self.decl_name = decl_name

    def __repr__(self):
        return "<alamatic.interpreter.Symbol %r (%s) from %r>" % (
            self.decl_name,
            self.codegen_name,
            self.decl_position,
        )

    def get_value(self, position=None):
        # first try to retrieve the type, even though we're not going to
        # do anything with it, just to make sure it's known.
        dummy = self.get_type(position=position)
        try:
            return self.value_slot.value
        except datafork.ValueAmbiguousError, ex:
            # FIXME: Include the merge conflict possibilities in the error
            # message for ease of debugging.
            raise SymbolValueAmbiguousError(
                "Value of '%s' is not known at " % (self.decl_name),
                pos_link(position),
                conflict=ex.conflict,
            )
        except datafork.ValueNotKnownError:
            raise SymbolValueNotKnownError(
                "Value of '%s' is not known at " % (self.decl_name),
                pos_link(position),
            )

    def assign(self, value, position=None):
        if not self.is_possibly_initialized:
            # we're initializing the symbol for the first time
            self.initialize(type(value), position=position)
        else:
            try:
                current_type = self.type_slot.value
            except datafork.ValueNotKnownError:
                # FIXME: If it's a merge conflict (which is most likely is)
                # then include the set of possibilities and their positions
                # in the error message to help the user debug.
                raise SymbolTypeNotKnownError(
                    "Type of '%s' is not known at " % self.decl_name,
                    pos_link(position)
                )
            if type(value) is not current_type:
                raise IncompatibleTypesError(
                    "Can't assign %s to %s %s '%s'" % (
                        type(value).__name__,
                        current_type.__name__,
                        'constant' if self.const else 'variable',
                        self.decl_name,
                    ),
                    " at ", pos_link(position),
                )
        self.value_slot.set_value(value, position=position)

    def mark_value_unknown(self, known_type=None, position=None):
        if known_type:
            if not self.is_possibly_initialized:
                self.initialize(known_type, position=position)
            else:
                try:
                    current_type = self.type_slot.value
                except datafork.ValueNotKnownError:
                    # FIXME: If it's a merge conflict (which is most likely is)
                    # then include the set of possibilities and their positions
                    # in the error message to help the user debug.
                    raise SymbolTypeNotKnownError(
                        "Type of '%s' is not known at " % self.decl_name,
                        pos_link(position)
                    )
                if known_type is not current_type:
                    raise IncompatibleTypesError(
                        "Can't assign %s to %s %s '%s'" % (
                            known_type.__name__,
                            current_type.__name__,
                            'constant' if self.const else 'variable',
                            self.decl_name,
                        ),
                        " at ", pos_link(position),
                    )

        self.value_slot.set_value_not_known(position=position)

    def get_type(self, position=None):
        try:
            return self.type_slot.value
        except datafork.ValueAmbiguousError, ex:
            # FIXME: include the set of competing initializations in the
            # error message to help the user debug.
            raise SymbolValueAmbiguousError(
                "Type of '%s' is ambiguous at " % self.decl_name,
                pos_link(position),
                conflict=ex.conflict,
            )
        except datafork.ValueNotKnownError, ex:
            raise SymbolNotInitializedError(
                "'%s' has not yet been initialized at " % self.decl_name,
                pos_link(position),
            )

    def initialize(self, new_type, position=None):
        if len(self.type_slot.positions) > 0:
            # should never happen
            raise Exception("Can't initialize '%s': already has a type" % (
                self.decl_name
            ))
        else:
            self.type_slot.set_value(new_type, position=position)
            self.type_slot.value = new_type
            self.is_initialized_slot.set_value(True, position=position)

    def mark_used_at_runtime(self, position=None):
        # if we're already marked as used at runtime then this is a no-op,
        # because we want to keep the *first* runtime usage position.
        # We use the positions of this slot and disregard the value, because
        # the positions combine together nicely when merging datafork states.
        if len(self.runtime_usage_position_slot.positions) == 0:
            self.runtime_usage_position_slot.set_value(
                True,
                position=position,
            )

    @property
    def is_possibly_initialized(self):
        try:
            return True if self.is_initialized_slot.value else False
        except datafork.ValueAmbiguousError:
            return True
        except datafork.ValueNotKnownError:
            return False

    @property
    def is_definitely_initialized(self):
        if self.is_initialized_slot.value_is_known:
            return True if self.is_initialized_slot.value else False
        else:
            return False

    @property
    def is_used_at_runtime(self):
        return self.runtime_usage_position is not None

    @property
    def init_position(self):
        if len(self.is_initialized_slot.positions) > 0:
            return list(sorted(self.is_initialized_slot.positions))[0]
        else:
            return None

    @property
    def assign_position(self):
        if len(self.value_slot.positions) > 0:
            return list(sorted(self.value_slot.positions))[0]
        else:
            return None

    @property
    def runtime_usage_position(self):
        if len(self.runtime_usage_position_slot.positions) > 0:
            return list(sorted(self.runtime_usage_position_slot.positions))[0]
        else:
            return None

    @property
    def codegen_name(self):
        return "_ala_%x" % id(self)

    def generate_c_decl(self, state, writer):
        if not self.is_used_at_runtime:
            # Don't bother generating any symbols that aren't used
            # at runtime.
            return
        if self.const:
            writer.write("const ")
        if not self.is_definitely_initialized:
            # Should never happen
            raise Exception(
                "Symbol used at runtime but never initialized"
            )
        writer.write(self.get_type().c_type_spec(), " ")
        writer.write(self.codegen_name)
        if self.const:
            writer.write(" = ")
            self.get_value().generate_c_code(state, writer)
        writer.writeln(";")


class Registry(object):

    def __init__(self, parent=None):
        self.parent = parent
        if parent:
            self.data_state_context = parent.data_state.fork()
        else:
            self.data_state_context = datafork.Root()
        self.runtime_functions = set()
        self.runtime_types = set()
        self.runtime_top_level_scopes = set()

    def __enter__(self):
        self.data_state = self.data_state_context.__enter__()
        self.previous_registry = interpreter.registry
        interpreter.registry = self
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        interpreter.registry = self.previous_registry
        self.data_state_context.__exit__(exc_type, exc_value, traceback)

    def create_child(self):
        return Registry(self)

    def register_runtime_function(self, function):
        self.runtime_functions.add(function)

    def register_runtime_type(self, type_):
        self.runtime_types.add(type_)

    def register_runtime_top_level_scope(self, symbols):
        self.runtime_top_level_scopes.add(symbols)

    def merge_children(self, children, or_none=False):
        child_data_states = [
            x.data_state for x in children
        ]
        self.data_state.merge_children(child_data_states, or_none=or_none)

        # The runtime object registries just union together, since they
        # cannot conflict with one another.
        for child in children:
            self.runtime_functions.update(child.runtime_functions)
            self.runtime_types.update(child.runtime_functions)
            self.runtime_top_level_scopes.update(
                child.runtime_top_level_scopes,
            )

    def create_slot(self):
        return self.data_state.root.slot()


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
            writer.write(symbol.get_type().c_type_spec(), " ")
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
