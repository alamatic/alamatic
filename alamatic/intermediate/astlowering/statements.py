
import alamatic.util
from alamatic.ast.statements import *
import alamatic.diagnostics as diag
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


@lower_statement.overload(WhileStmt)
def lower_while_stmt(stmt, scope, builder):
    header_block = builder.create_block()
    body_block = builder.create_block()
    after_block = builder.create_block()

    builder.jump(
        target_block=header_block,
        source_range=stmt.source_range,
    )

    builder.set_current_block(header_block)
    cond_value = lower_expression(stmt.test_expr, scope, builder)
    builder.jump_if(
        cond_value=cond_value,
        true_block=body_block,
        false_block=after_block,
        source_range=stmt.source_range,
    )

    builder.set_current_block(body_block)
    block_scope = scope.create_child(
        continue_block=header_block,
        break_block=after_block,
    )
    lower_stmt_block(stmt.block, block_scope, builder)
    builder.jump(
        target_block=header_block,
        source_range=stmt.source_range,
    )

    builder.set_current_block(after_block)


@lower_statement.overload(ExpressionStmt)
def lower_expression_stmt(stmt, scope, builder):
    lower_expression(stmt.expr, scope, builder)


@lower_statement.overload(PassStmt)
def lower_pass_stmt(stmt, scope, builder):
    pass


@lower_statement.overload(ContinueStmt)
def lower_continue_stmt(stmt, scope, builder):
    continue_block = scope.continue_block
    if continue_block is not None:
        builder.jump(
            target_block=continue_block,
            source_range=stmt.source_range,
        )
    else:
        builder.error(
            diagnostic=diag.ContinueOutsideLoop(),
            source_range=stmt.source_range,
        )
        builder.end(source_range=None)

    # Create a dummy block for any following statements to get
    # dropped into. These statements will not actually be reachable.
    # FIXME: Make the builder aware of the concept of unreachable
    # code so we can generate warnings about it.
    unreachable_block = builder.create_block()
    builder.set_current_block(unreachable_block)


@lower_statement.overload(BreakStmt)
def lower_break_stmt(stmt, scope, builder):
    break_block = scope.break_block
    if break_block is not None:
        builder.jump(
            target_block=break_block,
            source_range=stmt.source_range,
        )
    else:
        builder.error(
            diagnostic=diag.BreakOutsideLoop(),
            source_range=stmt.source_range,
        )
        builder.end(source_range=None)

    # Create a dummy block for any following statements to get
    # dropped into. These statements will not actually be reachable.
    # FIXME: Make the builder aware of the concept of unreachable
    # code so we can generate warnings about it.
    unreachable_block = builder.create_block()
    builder.set_current_block(unreachable_block)


@lower_statement.overload(ErroredStatement)
def lower_errored_statement(stmt, scope, builder):
    builder.error(
        diagnostic=stmt.error,
        source_range=stmt.source_range,
    )
