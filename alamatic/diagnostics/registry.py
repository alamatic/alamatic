
from alamatic.diagnostics.internals import *


def register(name, level, format_string):
    # There's some trickiness going on here.
    # register_diagnostic (from 'internals') will create a diagnostic
    # type and add it into this module's globals dict, making it available
    # for other modules to import.
    register_diagnostic(globals(), name, level, format_string)


# This will get filled out by calls to register()
__all__ = ['Diagnostic']

# The rest of this file is the registry itself, with one register() call
# per diagnostic type.

### Scanner Diagnostics
register(
    'UnexpectedToken', ERROR,
    u'Expected {wanted_token} but got {got_token}',
)
register(
    'InvalidCharacter', ERROR,
    u'{location:link(Invalid character)}',
)
register(
    'InvalidIndentation', ERROR,
    u'{location:link(Invalid indentation)}',
)

### Parser Diagnostics

### AST Lowering Diagnostics
register(
    'InvalidLValue', ERROR,
    u'Cannot assign to {assignee_node}',
)
register(
    'UnknownSymbol', ERROR,
    # FIXME: Need to include the reference's source range in here somehow.
    u'There is no variable or constant named {decl_name}',
)
register(
    'ContinueOutsideLoop', ERROR,
    # FIXME: Need to include the reference's source range in here somehow.
    u'Cannot use "continue" outside of a loop',
)
register(
    'BreakOutsideLoop', ERROR,
    # FIXME: Need to include the reference's source range in here somehow.
    u'Cannot use "break" outside of a loop',
)