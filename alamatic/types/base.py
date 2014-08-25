
import weakref


__all__ = [
    "TypeConstructor",
    "Type",
    "TypeImplementation",
]


class TypeConstructor(object):

    def __init__(self, impl=None):
        # Multiple implementations is not valid, but we permit it
        # during preprocessing with the intent that it be caught
        # and reported by the checking step run after preprocessing.
        #
        # This means that type inference can produce an invalid solution,
        # but it will always run to completion.
        self.impls = []
        if impl is not None:
            self.impls.append(impl)

        self._instances = weakref.WeakValueDictionary()

    def instantiate(self, type_args=(), value_args=()):
        type_args = tuple(type_args)
        value_args = tuple(value_args)
        instance_key = (type_args, value_args)
        if instance_key not in self._instances:
            # Important to hold this in a variable so that our weak ref
            # doesn't die before we get a chance to return the value.
            new_type = Type(
                self,
                type_args,
                value_args,
            )
            self._instances[instance_key] = new_type

        return self._instances[instance_key]

    @property
    def is_variable(self):
        return len(self.impls) == 0


class Type(object):

    def __init__(self, cons, type_args, value_args):
        self.cons = cons
        self.type_args = tuple(type_args)
        self.value_args = tuple(value_args)
        # We'll be hashing these things a lot, so compute the hash
        # value once up front so we can return it many times.
        # This is safe because types are immutable.
        self._hash = hash(
            (
                self.cons,
                self.type_args,
                self.value_args,
            )
        )

    def __hash__(self):
        return self._hash

    def __eq__(self, other):
        return (
            self.cons == other.cons and
            self.type_args == other.type_args and
            self.value_args == other.value_args
        )


class TypeImplementation(object):

    def make_no_arg_type(self):
        """
        Build a type constructor for this implementation and instantiate
        it with no arguments.

        This is a shorthand for the common case of a argument-less type
        that has exactly one constructor and exactly one instance. Users
        of this interface must only call it once, e.g. to assign to
        some global variable representing the type, since calling it
        more than once will cause a second constructor to be created, which
        will cause the two instances to be incompatible.

        For example:

        ..code-block:: python

            MyType = MyTypeImpl().make_no_arg_type()
        """
        return TypeConstructor(self).instantiate()
