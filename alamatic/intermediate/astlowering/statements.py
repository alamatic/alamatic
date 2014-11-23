
import alamatic.util
from alamatic.ast.statements import *
from alamatic.intermediate.astlowering.declarations import lower_declaration
from alamatic.intermediate.astlowering.expressions import lower_expression


__all__ = [
    "lower_statement",
    "lower_stmt_block",
]


def lower_stmt_block(block, scope, builder):
    for stmt in block.stmts:
        lower_statement(stmt, scope, builder)


@alamatic.util.overloadable
def lower_statement(stmt, scope, builder):
    raise Exception("lower_statement not implemented for %r" % stmt)


@lower_statement.overload(DataDeclStmt)
def lower_data_decl_stmt(stmt, scope, builder):
    decl = stmt.decl
    symbol = lower_declaration(decl, scope, builder)

    expr = stmt.expr
    if expr is not None:
        value = lower_expression(expr, scope, builder)
        symbol.make_ir_store(builder, value)


@lower_statement.overload(IfStmt)
def lower_if_stmt(stmt, scope, builder):
    after_block = builder.create_block()
    for clause in stmt.clauses:
        if hasattr(clause, "test_expr"):
            cond_value = lower_expression(
                clause.test_expr, scope, builder,
            )
            true_block = builder.create_block()
            false_block = builder.create_block()
            builder.jump_if(
                cond_value=cond_value,
                true_block=true_block,
                false_block=false_block,

                # FIXME: source range for the jump should just be the
                # 'header' of the clause, not including its block.
                source_range=clause.source_range,
            )

            builder.set_current_block(true_block)
            block_scope = scope.create_child()
            lower_stmt_block(clause.block, block_scope, builder)
            builder.jump(
                target_block=after_block,

                # FIXME: find something more sensible to use as the source
                # range here, rather than the entire clause.
                source_range=clause.source_range,
            )
            builder.set_current_block(false_block)
        else:
            block_scope = scope.create_child()
            lower_stmt_block(clause.block, block_scope, builder)

    builder.jump(
        target_block=after_block,

        # FIXME: Find something sensible to specify as the source range
        # for the final jump. The whole statement is not sensible.
        source_range=stmt.source_range,
    )
    builder.set_current_block(after_block)


@lower_statement.overload(ExpressionStmt)
def lower_expression_stmt(stmt, scope, builder):
    lower_expression(stmt.expr, scope, builder)
