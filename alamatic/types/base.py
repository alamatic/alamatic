
class Type(object):

    #: The lower-level type that represents the in-memory bit pattern
    #: for values of this type. Subclasses must override this and
    #: set it to an instance of a subtype of :py:class:`llvm.core.Type`.
    llvm_type = None

    def __call__(self, *args, **kwargs):
        data = self.make_constant_data(*args, **kwargs)
        return TypedValue(self, data)

    def repr_for_data(self, data):
        return str(data)


class TypedValue(object):

    #: Instance of a :py:class:`Type` subclass representing the type of this
    #: value.
    type = None

    #: :py:class:`llvm.core.Value` representing the raw data for this value.
    #: This data is considered opaque by all code except the class of
    #: :py:attr:`type`.
    data = None

    def __init__(self, type, data):
        self.type = type
        self.data = data

    def __repr__(self):
        return self.type.repr_for_data(self.data)

    @property
    def is_constant(self):
        from llvm.core import Constant
        return isinstance(self.data, Constant)
