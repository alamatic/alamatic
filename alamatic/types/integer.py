
import weakref

from alamatic.types import (
    TypeImplementation,
    OperationImplementation,
)


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


class BinaryOperationImpl(OperationImplementation):

    def __init__(self, name, build_impl, const_impl):
        self.name = name
        self.build_impl = build_impl
        self.const_impl = const_impl

    def get_constant_result(self, lhs, rhs):
        if not self.const_impl:
            from alamatic.intermediate import Unknown
            return Unknown

        # TODO: Handle overflow by wrapping
        return self.const_impl(lhs.value, rhs.value)

    def build_llvm_value(self, builder, lhs, rhs):
        # TODO: insert conversion for rhs if it's an UnknownSizeInteger
        return self.const_impl(builder, lhs.value, rhs.value)

    def __repr__(self):
        return "<IntegerImpl.%s>" % self.name


class BinaryArithmeticOperationImpl(BinaryOperationImpl):

    def get_result_type(self, lhs, rhs, source_range=None):
        # TODO: Verify the result type
        return lhs.type


class BinaryTestOperationImpl(BinaryOperationImpl):

    def get_result_type(self, lhs, rhs, source_range=None):
        from alamatic.types import Bool
        return Bool


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

    def __init__(self):
        TypeImplementation.__init__(self, "UnknownSizeInteger")

    add = BinaryArithmeticOperationImpl(
        "add",
        lambda b, lhs, rhs: b.add(lhs, rhs),
        lambda lhs, rhs: lhs + rhs,
    )

    is_less_than = BinaryTestOperationImpl(
        "is_less_than",
        None,
        lambda lhs, rhs: lhs < rhs,
    )


operation_impls = [
    BinaryArithmeticOperationImpl(
        "add",
        lambda b, lhs, rhs: b.add(lhs, rhs),
        lambda lhs, rhs: lhs + rhs,
    ),
    BinaryArithmeticOperationImpl(
        "sub",
        lambda b, lhs, rhs: r.sub(lhs, rhs),
        lambda lhs, rhs: lhs - rhs,
    ),
]


class IntegerImpl(TypeImplementation):

    def __init__(self, bits, signed):
        self.bits = bits
        self.signed = signed
        display_name = "%sInt%i" % (
            "" if self.signed else "U",
            self.bits,
        )
        super(
            IntegerImpl,
            self,
        ).__init__(display_name)

    def __metaclass__(name, bases, dict):
        for operation in operation_impls:
            dict[operation.name] = operation
        return type(name, bases, dict)


Int64 = IntegerImpl(64, True).make_no_arg_type()
UInt64 = IntegerImpl(64, False).make_no_arg_type()
Int32 = IntegerImpl(32, True).make_no_arg_type()
UInt32 = IntegerImpl(32, False).make_no_arg_type()
Int16 = IntegerImpl(16, True).make_no_arg_type()
UInt16 = IntegerImpl(16, False).make_no_arg_type()
Int8 = IntegerImpl(8, True).make_no_arg_type()
UInt8 = IntegerImpl(8, False).make_no_arg_type()
IntUnknownSize = UnknownSizeIntegerImpl().make_no_arg_type()
