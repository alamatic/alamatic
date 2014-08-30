
import weakref


__all__ = [
    "TypeConstructor",
    "Type",
    "TypeImplementation",
    "get_fresh_type_variable",
    "get_type_display_names",
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

    @property
    def display_name(self):
        return get_type_display_names([self])[self]

    def __repr__(self):
        return "<alamatic.types.Type %s at 0x%x>" % (
            self.display_name,
            id(self),
        )

    @property
    def is_variable(self):
        return self.cons.is_variable

    def __hash__(self):
        return self._hash

    def __eq__(self, other):
        if not isinstance(other, Type):
            return False

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

    @property
    def display_name(self):
        raise Exception("No display_name for %r" % type(self))


def get_fresh_type_variable():
    return TypeConstructor().instantiate()


def get_type_display_names(types):
    """
    Given an iterable of types, returns a mapping from each type to a
    string containing a reasonable display name for it.

    When type variables are present, this function guarantees that they
    will each have a unique placeholder name that will be consistent
    across all of the generated names. These will be single uppercase letters
    starting with T and continuing with U, V, etc. If there are more than
    26 distinct type variables then some of their names will overlap.
    """
    next_var_letter_idx = [19]  # index into the alphabet; 19 = T
    var_letters = {}
    ret = {}

    def cons_name(cons):
        display_name = None
        if len(cons.impls) == 1:
            display_name = cons.impls[0].display_name

        if display_name is not None:
            return display_name
        else:
            try:
                return var_letters[cons]
            except KeyError:
                letter = chr(65 + next_var_letter_idx[0])
                next_var_letter_idx[0] = next_var_letter_idx[0] + 1
                if next_var_letter_idx[0] > 25:
                    next_var_letter_idx[0] = 0
                var_letters[cons] = letter
                return letter

    def value_as_str(value):
        if type(value) is bool:
            return "true" if bool else "false"
        else:
            return repr(value)

    def name(type):
        if len(type.type_args) == 0 and len(type.value_args) == 0:
            # Easy case
            return cons_name(type.cons)
        else:
            base_name = cons_name(type.cons)
            arg_parts = tuple(
                name(t) for t in type.type_args
            ) + tuple(
                value_as_str(v) for v in type.value_args
            )
            return "%s<%s>" % (
                base_name,
                ", ".join(arg_parts),
            )

    for type in types:
        ret[type] = name(type)

    return ret
