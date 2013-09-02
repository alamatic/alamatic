
from alamatic.types.base import *
from alamatic.compilelogging import pos_link


class ArrayType(Type):

    def __new__(cls, element_type, element_count):
        d = {}
        d["element_type"] = element_type
        d["element_count"] = element_count
        name = "Array(%i %r)" % (element_count, element_type)
        return Type.__new__(cls, name, (Value,), d)

    def __init__(self, element_type, element_count):
        pass
