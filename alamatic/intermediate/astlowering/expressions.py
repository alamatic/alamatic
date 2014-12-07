
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


def lower_binary_op_expr(expr, operator_map, scope, builder):
    assert expr.op in operator_map
    operation = operator_map[expr.op]

    lhs_value = lower_expression(expr.lhs, scope, builder)
    rhs_value = lower_expression(expr.rhs, scope, builder)

    return operation(
        lhs=lhs_value,
        rhs=rhs_value,
        source_range=expr.source_range,
    )


@lower_expression.overload(NumericLiteralExpr)
def lower_numeric_literal_expr(expr, scope, builder):
    from alamatic.types import ConstNumber
    value = ConstNumber(ConstNumber.make_constant_data(expr.value))

    return builder.load_literal(
        source_range=expr.source_range,
        value=value,
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
            diagnostic=diag.UnknownSymbol(
                decl_name=expr.name,
            ),
            source_range=expr.source_range,
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
    operator_map = {
        "<": builder.lt,
        ">": builder.gt,
        "==": builder.eq,
    }
    return lower_binary_op_expr(expr, operator_map, scope, builder)


@lower_expression.overload(SumExpr)
def lower_sum_expr(expr, scope, builder):
    operator_map = {
        "+": builder.add,
        "-": builder.subtract,
    }
    return lower_binary_op_expr(expr, operator_map, scope, builder)
