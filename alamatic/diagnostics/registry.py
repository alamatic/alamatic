
from alamatic.diagnostics.internals import *


def register(name, level, format_string):
    # There's some trickiness going on here.
    # register_diagnostic (from 'internals') will create a diagnostic
    # type and add it into this module's globals dict, making it available
    # for other modules to import.
    register_diagnostic(globals(), name, level, format_string)


# This will get filled out by calls to register()
__all__ = []

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
