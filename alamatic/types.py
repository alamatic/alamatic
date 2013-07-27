
class Type(type):
    def __new__(cls, name, bases, dict):
        return type.__new__(cls, name, bases, dict)


def is_our_type(some_type):
    return type(some_type) is Type


def is_our_value(some_value):
    return is_our_type(type(some_value))


class Value(object):
    __metaclass__ = Type


class Number(Value):
    pass


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
            raise Exception("Integer out of range: %i to %i" % limits)

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


class Int64(Integer):
    value_size = 63
    signed = True


class Int32(Integer):
    value_size = 31
    signed = True


class Int16(Integer):
    value_size = 15
    signed = True


class Int8(Integer):
    value_size = 7
    signed = True


class UInt64(Integer):
    value_size = 64
    signed = False


class UInt32(Integer):
    value_size = 32
    signed = False


class UInt16(Integer):
    value_size = 16
    signed = False


class UInt8(Integer):
    value_size = 8
    signed = False


class String(Value):
    pass


class ArrayType(Type):

    def __new__(cls, element_type, element_count):
        d = {}
        d["element_type"] = element_type
        d["element_count"] = element_count
        name = "Array(%i %r)" % (element_count, element_type)
        return Type.__new__(cls, name, (Value,), d)

    def __init__(self, element_type, element_count):
        pass
