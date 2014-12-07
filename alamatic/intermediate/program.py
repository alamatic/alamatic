
from alamatic.intermediate.scope import Scope, Symbol


class GlobalVariable(Symbol):

    def __init__(self, index, decl_name, decl_range):
        self.index = index
        Symbol.__init__(self, decl_name, decl_range)

    def make_ir_load(self, builder, source_range=None):
        return builder.load_global(
            location=self,
            source_range=source_range,
        )

    def make_ir_store(self, builder, value, source_range=None):
        builder.store_global(
            location=self,
            source=value,
            source_range=source_range,
        )

    @property
    def codegen_name(self):
        return "glob_%03x" % self.index

    def __repr__(self):
        return "<GlobalVariable %s for %s at %s>" % (
            self.codegen_name,
            self.decl_name,
            self.decl_range,
        )

    @property
    def as_debug_value(self):
        return self.codegen_name


class Constant(Symbol):

    def __init__(self, index, decl_name, decl_range):
        self.index = index
        Symbol.__init__(self, decl_name, decl_range)

    @property
    def codegen_name(self):
        return "const_%03x" % self.index

    def make_ir_load(self, builder, source_range=None):
        return builder.load_constant(
            location=self,
            source_range=source_range,
        )

    def make_ir_store(self, builder, value, source_range=None):
        builder.store_constant(
            location=self,
            source=value,
            source_range=source_range,
        )

    def __repr__(self):
        return "<Constant %s for %s at %s>" % (
            self.codegen_name,
            self.decl_name,
            self.decl_range,
        )

    @property
    def as_debug_value(self):
        return self.codegen_name


class Program(object):
    """
    An IR program.

    An Alamatic IR program is roughly an analog of an LLVM IR Module: it
    represents an entire program, including the function call graph rooted
    at the function representing the entry file and the program's global
    variables.
    """

    def __init__(self, entry_func):
        self.global_variables = []
        self.constants = []
        self.entry_func = entry_func
        self.root_scope = Scope(
            variable_cons=self.declare_variable,
            constant_cons=self.declare_constant,
        )

    def declare_variable(self, decl_name, decl_range):
        index = len(self.global_variables)
        variable = GlobalVariable(index, decl_name, decl_range)
        self.global_variables.append(variable)
        return variable

    def declare_constant(self, decl_name, decl_range):
        index = len(self.constants)
        constant = Constant(index, decl_name, decl_range)
        self.constants.append(constant)
        return constant
