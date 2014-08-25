
from alamatic.types import *


__all__ = [
    "get_type_for_constant",
]


# Primitive constants are represented as values of built-in Python types.
# We can translate these to Alamatic types via a simple lookup.
primitive_type_map = {
    int: IntUnknownSize,
    long: IntUnknownSize,
}


def get_type_for_constant(value):
    try:
        return primitive_type_map[type(value)]
    except KeyError:
        pass

    # FIXME: Implement a complete set of mappings for complex types, after
    # which point it will be an implementation error to reach this point.
    return get_fresh_type_variable()
