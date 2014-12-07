
import alamatic.util
from alamatic.ast.declarations import *

__all__ = [
    "lower_declaration"
]


@alamatic.util.overloadable
def lower_declaration(decl, scope, builder):
    raise Exception("lower_declaration not implemented for %r" % decl)


@lower_declaration.overload(VarDeclClause)
def lower_var_decl_clause(decl, scope, builder):
    return scope.declare_variable(decl.name, decl.source_range)


@lower_declaration.overload(ConstDeclClause)
def lower_const_decl_clause(decl, scope, builder):
    return scope.declare_constant(decl.name, decl.source_range)
