
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

        result = self.const_impl(lhs.constant_value, rhs.constant_value)
        return self.get_result_type(lhs, rhs).impl.constrain_value(result)

    def build_llvm_value(self, builder, lhs, rhs):
        lhs_value = lhs.build_llvm_value(builder)
        rhs_value = rhs.build_llvm_value(builder)

        # TODO: insert conversion for rhs if it's an UnknownSizeInteger
        return self.build_impl(builder, lhs_value, rhs_value)

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

    def get_llvm_type(self, types):
        # TODO: This should actually get handled as a PyObject*
        # since its implementation will exist entirely in Python during
        # compile time, but we don't support that yet.
        return types.int(32)

    def get_llvm_constant(self, builder, value):
        # TODO: This should actually be an error, since this type has no
        # business being in generated code. But we'll support it for now
        # because it makes debugging codegen easier.
        # No module using a constant of this type can ever be valid though,
        # since our constant type (i32) doesn't agree with our declared
        # value type (opaque)
        return builder.consts.int(builder.types.int(32), value)

    add = BinaryArithmeticOperationImpl(
        "add",
        lambda b, lhs, rhs: b.instrs.add(lhs, rhs),
        lambda lhs, rhs: lhs + rhs,
    )

    is_less_than = BinaryTestOperationImpl(
        "is_less_than",
        lambda b, lhs, rhs: b.instrs.icmp(b.icmps.SLT, lhs, rhs),
        lambda lhs, rhs: lhs < rhs,
    )


operation_impls = [
    BinaryArithmeticOperationImpl(
        "add",
        lambda b, lhs, rhs: b.instrs.add(lhs, rhs),
        lambda lhs, rhs: lhs + rhs,
    ),
    BinaryArithmeticOperationImpl(
        "sub",
        lambda b, lhs, rhs: b.instrs.sub(lhs, rhs),
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

    @property
    def limits(self):
        value_bits = self.bits - 1 if self.signed else self.bits
        num_values = 2 ** value_bits
        if self.signed:
            return (-num_values, num_values - 1)
        else:
            return (0, num_values - 1)

    @property
    def min_value(self):
        return self.limits[0]

    @property
    def max_value(self):
        return self.limits[1]

    def constrain_value(self, num):
        value_mask = (2 ** self.bits) - 1
        sign_mask = (2 ** (self.bits - 1))
        ret = num & value_mask
        if self.signed and (ret & sign_mask):
            value_mask = (2 ** (self.bits - 1)) - 1
            ret = self.min_value + (ret & value_mask)
        return ret

    def get_llvm_type(self, types):
        return types.int(self.bits)

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
