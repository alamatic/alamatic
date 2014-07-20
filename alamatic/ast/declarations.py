
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

    def __init__(self, source_range, name, type_expr):
        self.source_range = source_range
        self.name = name
        self.type_expr = type_expr

    @property
    def params(self):
        yield self.name

    @property
    def child_nodes(self):
        if self.type_expr is not None:
            yield self.type_expr
