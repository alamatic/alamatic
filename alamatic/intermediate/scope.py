
class Scope(object):

    def __init__(
        self,
        variable_cons,
        constant_cons,
        continue_block=None,
        break_block=None,
        parent=None,
    ):
        self.parent_scope = parent
        self.variable_cons = variable_cons
        self.constant_cons = constant_cons
        self.continue_block = continue_block
        self.break_block = break_block
        self._symbols = {}

    def create_child(
        self,
        continue_block=None,
        break_block=None,
        variable_cons=None,
        constant_cons=None,
    ):
        if variable_cons is None:
            variable_cons = self.variable_cons
        if constant_cons is None:
            constant_cons = self.constant_cons
        if continue_block is None:
            continue_block = self.continue_block
        if break_block is None:
            break_block = self.break_block

        return Scope(
            variable_cons=variable_cons,
            constant_cons=constant_cons,
            continue_block=continue_block,
            break_block=break_block,
            parent=self,
        )

    def get_local_symbol(self, name):
        return self._symbols.get(name, None)

    @property
    def local_symbols(self):
        for name, symbol in self._symbols.iteritems():
            yield (name, symbol)

    def declare_variable(self, name, decl_range=None):
        variable = self.variable_cons(name, decl_range)
        self._symbols[name] = variable
        return variable

    def declare_constant(self, name, decl_range=None):
        constant = self.constant_cons(name, decl_range)
        self._symbols[name] = constant
        return constant

    def get_symbol(self, name):
        scope = self
        while scope is not None:
            symbol = scope.get_local_symbol(name)
            if symbol is not None:
                return symbol
            else:
                scope = scope.parent_scope
        return None


class Symbol(object):
    """
    Abstract type representing the symbol interface.

    Subsystems that instantiate :py:class:`Scope` will provide a constructor
    callable that returns objects that have the methods and attributes of
    this class.

    Inheriting this class can be useful, but is not required.
    """

    def __init__(self, decl_name, decl_range):
        self.decl_name = decl_name
        self.decl_range = decl_range

    def as_ir_operand(self, builder):
        raise Exception("as_ir_operand not implemented for %r" % builder)

    @property
    def codegen_name(self):
        raise Exception("codegen_name not implemented for %r" % self)
