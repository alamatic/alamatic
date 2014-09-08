
from alamatic.ast import *


class DataDeclClause(AstNode):

    def __init__(self, source_range, name):
        self.source_range = source_range
        self.name = name

    @property
    def params(self):
        yield self.name


class VarDeclClause(DataDeclClause):
    pass


class ConstDeclClause(DataDeclClause):
    pass


class FuncDeclClause(AstNode):

    def __init__(self, source_range, name, param_decls):
        self.source_range = source_range
        self.name = name
        self.param_decls = param_decls

    @property
    def params(self):
        yield self.name

    @property
    def child_nodes(self):
        return self.param_decls


class ParamDeclClause(AstNode):

    def __init__(
        self,
        source_range,
        name,
        const_required=False,
        named=False,
        default_expr=None,
        collector=False,
        type_constraint_expr=None,
    ):
        self.source_range = source_range
        self.name = name
        self.const_required = const_required
        self.named = named
        self.default_expr = default_expr
        self.collector = collector
        self.type_constraint_expr = type_constraint_expr

    @property
    def params(self):
        yield self.name
        if self.const_required:
            yield "const"
        if self.named:
            yield "named"
        if self.default_expr is not None:
            yield "optional"
        if self.collector:
            yield "..."

    @property
    def child_nodes(self):
        if self.type_constraint_expr is not None:
            yield self.type_constraint_expr
        if self.default_expr is not None:
            yield self.default_expr
