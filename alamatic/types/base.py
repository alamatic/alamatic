
from alamatic.compilelogging import pos_link


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
