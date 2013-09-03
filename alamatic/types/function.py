
from alamatic.compilelogging import pos_link
from alamatic.types.base import *

import weakref


class FunctionTemplate(Value):

    def __init__(self, decl_node, decl_scope):
        self.decl_node = decl_node
        self.decl_scope = decl_scope

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return (
            self.decl_node is other.decl_node
            and self.decl_scope is other.decl_scope
        )

    def __repr__(self):
        return "<alamatic.types.FunctionTemplate %r in %r>" % (
            self.decl_node,
            self.decl_scope,
        )


function_types = weakref.WeakValueDictionary()


class FunctionBase(Value):

    def __init__(self):
        if type(self) is FunctionBase:
            raise Exception(
                "FunctionBase is an abstract base type. "
                "Call Function to generate a subclass."
            )
        # TODO: Finish this


def Function(param_types, return_type, error_type):
    key = (tuple(param_types), return_type, error_type)
    if key not in function_types:
        name_parts = []
        name_parts.append(
            "(%s)" % (
                ", ".join(x.__name__ for x in param_types)
            )
        )
        if return_type is not None:
            name_parts.append(" -> ")
            name_parts.append(return_type.__name__)
        if error_type is not None:
            name_parts.append(" except ")
            name_parts.append(error_type.__name__)
        name = "Function(%s)" % ("".join(name_parts))
        subtype = type(name, (FunctionBase,), {
            "param_types": param_types,
            "return_type": return_type,
            "error_type": error_type,
        })
        function_types[key] = subtype

    return function_types[key]
