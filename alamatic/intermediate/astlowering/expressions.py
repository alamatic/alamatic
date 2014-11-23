
import alamatic.util
from alamatic.ast.expressions import *
import alamatic.diagnostics as diag


__all__ = [
    "lower_expression",
    "lower_expression_assignment",
]


@alamatic.util.overloadable
def lower_expression(expr, scope, builder):
    raise Exception("lower_expression not implemented for %r" % expr)


@alamatic.util.overloadable
def lower_expression_assignment(expr, value, scope, builder):
    if expr.can_be_lvalue:
        raise Exception(
            "lower_expression_assignment not implemented for %r" % expr
        )
    else:
        builder.error(
            diag.InvalidLValue(
                assignee_node=expr,
            )
        )


@lower_expression.overload(LiteralExpr)
def lower_literal_expr(expr, scope, builder):
    return builder.create_literal(
        expr.value,
        source_range=expr.source_range,
    )


@lower_expression.overload(AssignExpr)
def lower_assign_expr(expr, scope, builder):
    value = lower_expression(expr.rhs, scope, builder)
    lower_expression_assignment(expr.lhs, value, scope, builder)
    return value


@lower_expression.overload(SymbolNameExpr)
def lower_symbol_name_expr(expr, scope, builder):
    symbol = scope.get_symbol(expr.name)
    if symbol is not None:
        return symbol.make_ir_load(builder, expr.source_range)
    else:
        builder.error(
            diag.UnknownSymbol(
                decl_name=expr.name,
            )
        )
        return builder.poison(source_range=expr.source_range)


@lower_expression_assignment.overload(SymbolNameExpr)
def lower_symbol_name_expr_assignment(expr, value, scope, builder):
    symbol = scope.get_symbol(expr.name)
    if symbol is not None:
        symbol.make_ir_store(builder, value, expr.source_range)
    else:
        builder.error(
            diag.UnknownSymbol(
                decl_name=expr.name,
            )
        )


@lower_expression.overload(ComparisonExpr)
def lower_comparison_expr(expr, scope, builder):
    operator = expr.op
    if operator == "<":
        operation = builder.lt
    elif operator == ">":
        operation = builder.gt
    else:
        raise Exception("Unknown comparison operator %r" % operator)

    lhs_value = lower_expression(expr.lhs, scope, builder)
    rhs_value = lower_expression(expr.rhs, scope, builder)

    return operation(
        lhs=lhs_value,
        rhs=rhs_value,
        source_range=expr.source_range,
    )
