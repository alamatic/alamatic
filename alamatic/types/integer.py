
from alamatic.types import TypeImplementation


# We only export the type instances by default, since the implementations are
# not intended to be re-used.
__all__ = [
    "Int64",
    "UInt64",
    "Int32",
    "UInt32",
    "Int16",
    "UInt16",
    "Int8",
    "UInt8",
    "IntUnknownSize",
]


class IntegerImpl(TypeImplementation):

    def __init__(self, bits, signed):
        self.bits = bits
        self.signed = signed

    @property
    def display_name(self):
        return "%sInt%i" % (
            "" if self.signed else "U",
            self.bits,
        )


class UnknownSizeIntegerImpl(TypeImplementation):
    """
    Type of integer literals.

    An integer literal tells us that an integer is being defined but
    doesn't tell us the size. This type represents such an unsized integer.
    Unsized integers support no operations except conversion to a sized
    integer.

    This is really just an implementation detail of the following idiom:

    ..code-block:: alamatic

        var i = 5 as UInt8

    Special cases in our error reporting for unsupported operations will
    cause a special error message to be returned if a programmer attempts to
    use an integer literal without first converting it to a real integer type.
    """

    @property
    def display_name(self):
        # This type is an implementation detail and so it doesn't have a name
        # since the end-user should never see it.
        return None


Int64 = IntegerImpl(64, True).make_no_arg_type()
UInt64 = IntegerImpl(64, False).make_no_arg_type()
Int32 = IntegerImpl(32, True).make_no_arg_type()
UInt32 = IntegerImpl(32, False).make_no_arg_type()
Int16 = IntegerImpl(16, True).make_no_arg_type()
UInt16 = IntegerImpl(16, False).make_no_arg_type()
Int8 = IntegerImpl(8, True).make_no_arg_type()
UInt8 = IntegerImpl(8, False).make_no_arg_type()
IntUnknownSize = UnknownSizeIntegerImpl().make_no_arg_type()
