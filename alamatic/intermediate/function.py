
from alamatic.intermediate.scope import Symbol


class LocalVariable(Symbol):

    def __init__(self, index, decl_name, decl_range):
        self.index = index
        Symbol.__init__(self, decl_name, decl_range)

    def make_ir_load(self, builder, source_range=None):
        return builder.load_local(
            location=self,
            source_range=source_range,
        )

    def make_ir_store(self, builder, value, source_range=None):
        builder.store_local(
            location=self,
            source=value,
            source_range=source_range,
        )

    @property
    def codegen_name(self):
        return "ala_%03x" % self.index

    def __repr__(self):
        return "<LocalVariable %s for %s at %s>" % (
            self.codegen_name,
            self.decl_name,
            self.decl_range,
        )

    @property
    def as_debug_value(self):
        return self.codegen_name


class Function(object):
    """
    An IR function.

    At the IR layer all independent bodies of code are represented as
    functions. From the AST perspective, functions and entry files both
    lower to functions, with the latter just being a function with
    no explicit arguments.
    """

    def __init__(self, graph):
        self.local_variables = []
        self.graph = graph

    def declare_variable(self, decl_name, decl_range):
        index = len(self.local_variables)
        variable = LocalVariable(index, decl_name, decl_range)
        self.local_variables.append(variable)
        return variable
