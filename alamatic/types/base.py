
from alamatic.compilelogging import pos_link, CompilerError


__all__ = [
    "Type",
    "is_our_type",
    "is_our_value",
    "Value",
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
            if lhs_first:
                tmp = rhs
                rhs = lhs
                lhs = tmp
            raise OperationNotSupportedError(
                "Cannot ", verb, " ", rhs.result_type.__name__,
                " ", preposition, " ", lhs.result_type.__name__,
                " at ", pos_link(position),
            )
        return op
    return decorator


class Value(object):
    __metaclass__ = Type

    @classmethod
    def generate_c_forward_decl(self, state, writer):
        pass

    @classmethod
    def generate_c_decl(self, state, writer):
        pass

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
    def call(cls, callee_expr, args, position=None):
        raise OperationNotSupportedError(
            "Cannot call ", cls.__name__, " at ", pos_link(position),
        )


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
