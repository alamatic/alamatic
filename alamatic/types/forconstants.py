
from alamatic.types import *
import alamatic.intermediate as intermediate


__all__ = [
    "get_type_for_constant",
]


# Primitive constants are represented as values of built-in Python types.
# We can translate these to Alamatic types via a simple lookup.
primitive_type_map = {
    int: IntUnknownSize,
    long: IntUnknownSize,
    bool: Bool,
}


def get_type_for_constant(value):
    try:
        return primitive_type_map[type(value)]
    except KeyError:
        pass

    if isinstance(value, intermediate.FunctionTemplate):
        return FunctionTemplate

    # Should never happen, since we should have an appropriate mapping
    # for every kind of constant our intermediate code generator can produce.
    raise Exception(
        "Don't what type to use for %r" % value
    )
