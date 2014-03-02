
from alamatic.compilelogging import pos_link, CompilerError


__all__ = [
    "Type",
    "is_our_type",
    "is_our_value",
    "Value",
    "Unknown",
    "Number",
    "Void",
    "OperationNotSupportedError",
]


class Type(type):
    def __new__(cls, name, bases, dict):
        return type.__new__(cls, name, bases, dict)


def is_our_type(some_type):
    return type(some_type) is Type


def is_our_value(some_value):
    return is_our_type(type(some_value))


def _binop_stub(verb, preposition="to", lhs_first=False):
    from functools import wraps

    def decorator(f):

        @classmethod
        @wraps(f)
        def op(cls, lhs, rhs, position=None):

            # If an operation is called on an unknown type then the
            # result is necessarily unknown too.
            if cls is Unknown:
                return Unknown()

            if lhs_first:
                tmp = rhs
                rhs = lhs
                lhs = tmp
            raise OperationNotSupportedError(
                "Cannot ", verb, " ", rhs.apparent_type.__name__,
                " ", preposition, " ", lhs.apparent_type.__name__,
                " at ", pos_link(position),
            )
        return op
    return decorator


class Value(object):
    __metaclass__ = Type

    @property
    def params(self):
        return ()

    def __repr__(self):
        base = "alamatic.types.%s" % type(self).__name__
        str_params = ", ".join(
            repr(x) for x in self.params
        )
        if len(str_params) > 0:
            return "<%s: %s>" % (base, str_params)
        else:
            return "<%s>" % (base)

    @classmethod
    def generate_c_forward_decl(self, state, writer):
        pass

    @classmethod
    def generate_c_decl(self, state, writer):
        pass

    @property
    def apparent_type(self):
        return type(self)

    @property
    def uncertainty(self):
        """
        Linear level of uncertainty about this value, with zero meaning
        completely certain.

        This will be 0 for all values except unknown ones, which will
        return 1 if the type is known but the value is not, or 2 if neither
        the type nor the value is known.

        This is used in :py:meth:`merge` to choose the most conservative
        value (i.e. the one with most uncertainty) when doing data flow
        analysis and type inference.
        """
        return 0

    @property
    def value_is_known(self):
        return self.uncertainty == 0

    def merge(self, other):
        # Order the two values by certainty to simplify the logic below.
        if other.uncertainty > self.uncertainty:
            most_certain = self
            least_certain = other
        else:
            most_certain = other
            least_certain = self

        if least_certain.apparent_type is Unknown:
            if most_certain.apparent_type is Unknown:
                return least_certain
            else:
                # Since we know that a slot's type must match throughout the
                # program, it is safe for us promote an unknown type to
                # a known type. If this leads to a mismatch later this will
                # cause an error, not a regression to a less-certain state.
                # This special case is important to allow slots mutated in
                # loops to still converge on a type, or else they'd never
                # get a known type.
                return Unknown(most_certain.apparent_type)

        # If we get here then we know the types of both sides.

        if most_certain.apparent_type is not least_certain.apparent_type:
            from alamatic.preprocessor import InappropriateTypeError
            # FIXME: We don't have enough information here for a useful
            # error message. Either need to move this logic out
            # somewhere else or have a caller catch and re-throw this
            # with symbol names, positions and a stack trace.
            raise InappropriateTypeError(
                "Inconsistent initialization ",
                " (", self.apparent_type,
                " vs ", other.apparent_type, ")"
            )

        # If we get here then we know both sides have the *same* type.

        if not least_certain.value_is_known:
            return least_certain

        # If we get here then both values are known and have the same type.

        if self.is_changed_from(other):
            return Unknown(self.apparent_type)
        else:
            return self

    def is_changed_from(self, other):
        raise Exception(
            "Value type %r does not implement is_changed_from" % type(self)
        )

    @_binop_stub("add")
    def add():
        pass

    @_binop_stub("subtract", "from")
    def subtract():
        pass

    @_binop_stub("multiply", "by", lhs_first=True)
    def multiply():
        pass

    @_binop_stub("divide", "by", lhs_first=True)
    def divide():
        pass

    @_binop_stub("take remainder of", "divided by", lhs_first=True)
    def modulo():
        pass

    @_binop_stub("compare")
    def equals():
        pass

    @_binop_stub("compare")
    def not_equals():
        pass

    @_binop_stub("compare")
    def is_less_than():
        pass

    @_binop_stub("compare")
    def is_greater_than():
        pass

    @_binop_stub("compare")
    def is_less_than_or_equal_to():
        pass

    @_binop_stub("compare")
    def is_greater_than_or_equal_to():
        pass

    @_binop_stub("apply logical or to", "and", lhs_first=True)
    def logical_or():
        pass

    @_binop_stub("apply logical and to", "and", lhs_first=True)
    def logical_and():
        pass

    @_binop_stub("apply bitwise or to", "and", lhs_first=True)
    def bitwise_or():
        pass

    @_binop_stub("apply bitwise and to", "and", lhs_first=True)
    def bitwise_and():
        pass

    @_binop_stub("shift", "with", lhs_first=True)
    def shift_left():
        pass

    @_binop_stub("shift", "with", lhs_first=True)
    def shift_right():
        pass

    @classmethod
    def call(cls, callee, args, position=None):
        if cls is Unknown:
            return Unknown()

        raise OperationNotSupportedError(
            "Cannot call ", callee.apparent_type.__name__,
            " at ", pos_link(position),
        )


class Unknown(Value):
    """
    Special value type used to represent unknown values (and possibly also
    unknown types) during analysis. By the time analysis completes all
    unknown values must have a known type for a program to be considered
    valid.
    """
    _instances = {}

    def __new__(cls, known_type=None):
        if known_type not in cls._instances:
            new_instance = super(Unknown, cls).__new__(cls)
            new_instance.known_type = known_type
            cls._instances[known_type] = new_instance
        return cls._instances[known_type]

    @property
    def params(self):
        if self.known_type is not None:
            yield self.known_type

    @property
    def apparent_type(self):
        if self.known_type is not None:
            return self.known_type
        else:
            return type(self)

    @property
    def uncertainty(self):
        return 2 if self.known_type is None else 1

    def is_changed_from(self, other):
        return self.known_type is not other.known_type


class Number(Value):
    pass


class Void(Value):
    def __init__(self):
        raise Exception(
            "Can't instantiate Void"
        )

    @classmethod
    def c_type_spec(self):
        return "void"


class OperationNotSupportedError(CompilerError):
    pass
