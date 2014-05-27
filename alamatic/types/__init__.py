
def unify_types(*types):
    # TODO: This is a dumb initial implementation that doesn't have any
    # unification rules at all. Ultimately this should be the place where
    # we test whether the types *can* be unified, as well as guaranteeing
    # that we'll always converge on the "most known" type, rather than
    # just picking the first type as we do here.
    unified_type = None
    notify_unify_funcs = set()

    for candidate_type in types:
        if unified_type is None:
            unified_type = candidate_type
        elif unified_type is candidate_type:
            # Nothing to do!
            continue
        else:
            notify_unify_funcs.update(candidate_type.unify_funcs)

    for func in notify_unify_funcs:
        func(unified_type)

    unified_type.unify_funcs.update(notify_unify_funcs)

    return unified_type


class TypeConstructor(object):

    def __init__(self):
        self.types = {}

    def get_type(self, args):
        if args not in self.types:
            new_type = Type(self, args)
            self.types[args] = new_type
            for i, arg in enumerate(args):
                if isinstance(arg, Type):
                    arg.on_unify(
                        self._unify_arg_cb(new_type, i)
                    )

        return self.types[args]

    def __call__(self, *args):
        return self.get_type(tuple(args))

    def _unify_arg_cb(self, type_inst, index):
        old_args = type_inst.args

        # This handles the unification of nested types, by in turn unifying
        # the types they are nested in.
        def update(new_arg):
            new_args = tuple(
                (new_arg if i == index else old_arg)
                for i, old_arg in enumerate(old_args)
            )
            new_type_inst = self.get_type(new_args)
            if type_inst is not new_type_inst:
                type_inst._notify_unify(new_type_inst)

            for i, arg in enumerate(new_args):
                new_type_inst.on_unify(
                    self._unify_arg_cb(new_type_inst, i)
                )

            del self.types[old_args]

        return update


class Type(object):

    def __init__(self, cons, args):
        self.cons = cons
        self.args = args
        self.unify_funcs = set()

    def on_unify(self, func):
        self.unify_funcs.add(func)

    def _notify_unify(self, new_type):
        for func in self.unify_funcs:
            func(new_type)
