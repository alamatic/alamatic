
from alamatic.types.base import *
from alamatic.compilelogging import pos_link


class Integer(Number):
    value_size = None
    signed = None

    def __init__(self, value):
        cls = type(self)
        if cls.value_size is None:
            # TODO: Make this some special exception type that our runtime
            # can understand as its own.
            raise Exception("Cannot instantiate Integer")

        limits = cls.get_limits()
        if value < limits[0] or value > limits[1]:
            # TODO: Make this some special exception type that our runtime
            # can understand as its own.
            raise Exception("Integer %r out of range: %i to %i" % ((
                value,
            ) + limits))

        self.value = long(value)

    @classmethod
    def get_limits(cls):
        scope = long(2 ** cls.value_size)
        max_value = long(scope - 1)
        if cls.signed:
            min_value = long(-scope)
        else:
            min_value = 0

        return (min_value, max_value)

    @classmethod
    def get_min_value(cls):
        return cls.limits[0]

    @classmethod
    def get_max_value(self):
        return cls.limits[1]

    def __eq__(self, other):
        if not isinstance(other, Integer):
            return False
        return self.value == other.value

    def __ne__(self, other):
        return not self.__eq__(other)

    def is_changed_from(self, other):
        return self.value != other.value

    @property
    def params(self):
        yield self.value

    def generate_c_code(self, state, writer):
        writer.write(str(self.value))

    @classmethod
    def add(cls, lhs, rhs, position=None):
        from alamatic.preprocessor import (
            InappropriateTypeError,
        )

        if lhs.apparent_type is Unknown or rhs.apparent_type is Unknown:
            return Unknown()

        if not issubclass(rhs.apparent_type, Integer):
            raise InappropriateTypeError(
                "Can't add %s to %s at " % (
                    lhs.apparent_type,
                    rhs.apparent_type,
                ),
                pos_link(position),
            )

        # Whichever operand has the biggest type decides which type
        # we use for the return value, though if either of them are
        # signed then the result type is always signed.
        # FIXME: Is this the right promotion rule? Seems complex enough
        # that it's probably confusing.
        result_type = None
        lhs_type = lhs.apparent_type
        rhs_type = rhs.apparent_type

        if rhs_type.value_size > lhs_type.value_size:
            result_type = rhs_type
        else:
            result_type = lhs_type

        should_be_signed = lhs_type.signed or rhs_type.signed

        if should_be_signed and not result_type.signed:
            result_type = result_type.as_signed()

        # If either operand has an unknown value then our result value
        # is also unknown, but at least we now know the type.
        if type(lhs) is Unknown or type(rhs) is Unknown:
            return Unknown(result_type)

        # FIXME: Need to make this do the correct overflow behavior
        # if the result is too big for the target type, or else we'll
        # fail here assigning a value that's too big.
        return result_type(
            lhs.value + rhs.value
        )

    @classmethod
    def equals(cls, lhs, rhs, position=None):
        from alamatic.ast import ComparisonExpr, ValueExpr
        from alamatic.types.boolean import Bool
        from alamatic.interpreter import (
            IncompatibleTypesError,
            NotConstantError,
        )

        lhs_result_type = lhs.result_type
        rhs_result_type = rhs.result_type

        if not issubclass(rhs_result_type, Integer):
            raise IncompatibleTypesError(
                "Can't compare %s to %s at " % (
                    lhs_result_type.__name__,
                    rhs_result_type.__name__,
                ),
                pos_link(position)
            )

        try:
            lhs_value = lhs.constant_value
            rhs_value = rhs.constant_value
            return ValueExpr(
                position,
                Bool(lhs_value.value == rhs_value.value),
            )
        except NotConstantError:
            return ComparisonExpr(
                position,
                lhs, "==", rhs,
            )


class Int64(Integer):
    value_size = 63
    signed = True

    @classmethod
    def as_unsigned(cls):
        return UInt64

    @classmethod
    def c_type_spec(self):
        return "int64_t"


class Int32(Integer):
    value_size = 31
    signed = True

    @classmethod
    def as_unsigned(cls):
        return UInt32

    @classmethod
    def c_type_spec(self):
        return "int32_t"


class Int16(Integer):
    value_size = 15
    signed = True

    @classmethod
    def as_unsigned(cls):
        return UInt16

    @classmethod
    def c_type_spec(self):
        return "int16_t"


class Int8(Integer):
    value_size = 7
    signed = True

    @classmethod
    def as_unsigned(cls):
        return UInt8

    @classmethod
    def c_type_spec(self):
        return "int8_t"


class UInt64(Integer):
    value_size = 64
    signed = False

    @classmethod
    def as_signed(cls):
        return Int64

    @classmethod
    def c_type_spec(self):
        return "uint64_t"


class UInt32(Integer):
    value_size = 32
    signed = False

    @classmethod
    def as_signed(cls):
        return Int32

    @classmethod
    def c_type_spec(self):
        return "uint32_t"


class UInt16(Integer):
    value_size = 16
    signed = False

    @classmethod
    def as_signed(cls):
        return Int16

    @classmethod
    def c_type_spec(self):
        return "uint16_t"


class UInt8(Integer):
    value_size = 8
    signed = False

    @classmethod
    def as_signed(cls):
        return Int8

    @classmethod
    def c_type_spec(self):
        return "uint8_t"
