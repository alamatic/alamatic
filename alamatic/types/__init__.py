
def unified_type_variable(type_var_a, type_var_b):
    """
    Takes two type variables and returns a third type variable which
    serves as a template for updates to the two given variables that
    will unify them.

    This allows two type variables to be tested to see *how* (and *whether*)
    they unify, without any mutation of those variables.
    :py:func:`unify_type_variables` wraps this function such that it
    *does* mutate the given variables.
    """

    # TODO: This is a dumb initial implementation that doesn't have any
    # unification rules at all. Ultimately this should be the place where
    # we test whether the types *can* be unified, as well as guaranteeing
    # that we'll always converge on the "most known" type, rather than
    # just picking the first type as we do here.

    bound_types = []
    unbound_vars = []

    for type_var in (type_var_a, type_var_b):
        if type_var.type is not None:
            bound_types.append(type_var.type)
        else:
            unbound_vars.append(type_var)

    ret_var = TypeVariable()

    if len(bound_types) == 1:
        # TODO: Check whether the unbound variable's constraint is
        # compatible with the type of the bound variable.
        # For now we just assume that it is.
        ret_var.type = bound_types[0]
    elif len(bound_types) == 2:
        if bound_types[0].cons == bound_types[1].cons:
            # Same constructor means the types are compatible as long
            # as we can unify the type's parameters.
            ret_var.type = bound_types[0].cons.get_type(
                tuple(unified_type_arguments(
                    bound_types[0].args, bound_types[1].args,
                ))
            )
        else:
            # TODO: This should be a type conflict, but we don't have
            # any mechanism for signalling that yet.
            pass
    else:
        ret_var.constraint = unbound_vars[0].constraint.merge(
            unbound_vars[1].constraint
        )

    return ret_var


def unified_type_arguments(args_a, args_b):
    for arg_a, arg_b in zip(args_a, args_b):
        yield unified_type_variable(arg_a, arg_b)


def unify_type_variables(type_var_a, type_var_b):
    """
    Takes two type variables and guarantees that they will all
    refer to the same type (or type error) after it returns, or if all
    variables are unbound will all have the same type *constraint*.
    """

    template_var = unified_type_variable(type_var_a, type_var_b)

    type_var_a.become(template_var)
    type_var_b.become(template_var)


class TypeConstructor(object):

    def __init__(self):
        self.types = {}

    def get_type(self, args):
        return Type(self, args)

    def __call__(self, *args):
        return self.get_type(tuple(args))


class TypeVariable(object):

    def __init__(self):
        self._type = None
        self._constraint = None

    @property
    def type(self):
        if isinstance(self._type, TypeVariable):
            # Opportunistically flatten chains of
            # variables that have cropped up during
            # unification.
            self._type = self._type.type

        return self._type

    @type.setter
    def type(self, new_type):
        self._type = new_type
        # Can't have a type and a constraint at the same time
        self._constraint = None

    @property
    def constraint(self):
        if self.type is not None:
            return self.type.constraint
        else:
            return self._constraint

    @constraint.setter
    def constraint(self, new_constraint):
        if self.type is not None:
            # Should never happen
            raise Exception('Bound TypeVariable cannot have local constraint')
        else:
            self._constraint = new_constraint

    def become(self, other_var):
        self._type = other_var._type
        self._constraint = other_var._constraint

    def __eq__(self, other_var):
        return (
            self._type == other._type and self._constraint == other._constraint
        )


class Type(object):

    def __init__(self, cons, args):
        self.cons = cons
        self.args = args

    def __hash__(self):
        # We hash by the constructor alone, since this part of the
        # object is immutable. The args are mutable, so we consider
        # them only for equality tests and not for hashing. This
        # complies with the letter of the __hash__ interface -- all equal
        # objects will have the same hash value since they have the
        # same constructor -- but not its spirit, since our hash bucket
        # distribution will be very uneven. This means a hash lookup
        # on type keys degenerates to a scan of all types of a given
        # constructor.
        return hash(self.cons)

    def __eq__(self, other):
        return self.cons == other.cons and self.args == other.args
