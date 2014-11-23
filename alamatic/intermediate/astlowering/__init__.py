
from alamatic.intermediate.astlowering.expressions import lower_expression
from alamatic.intermediate.astlowering.statements import (
    lower_statement,
    lower_stmt_block,
)
from alamatic.intermediate.scope import Scope
from alamatic.intermediate.builder import Builder
from alamatic.intermediate.function import Function


__all__ = [
    "lower_expression",
    "lower_statement",
]


def lower_entry_file(ef):
    builder = Builder()
    function = Function(builder.graph)
    scope = Scope(
        variable_cons=function.declare_variable,

        # TODO: Need a constant constructor too.
        constant_cons=None,
    )

    lower_stmt_block(ef.block, scope, builder)
    builder.jump(
        target_block=builder.exit_block,

        # FIXME: What's a good source range to use here?
        source_range=ef.source_range,
    )
    return function


def lower_function(function):
    pass