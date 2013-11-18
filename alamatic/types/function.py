
from alamatic.compilelogging import pos_link
from alamatic.types.base import *

import weakref


class FunctionTemplate(Value):

    def __init__(self, decl_node, decl_scope):
        self.decl_node = decl_node
        self.decl_scope = decl_scope
        self.instances = []

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

    def _assert_correct_args(self, args, position=None):
        from alamatic.interpreter import InvalidParameterListError
        param_decls = self.decl_node.decl.param_decls
        if len(param_decls) != len(args.exprs):
            raise InvalidParameterListError(
                "Function '", self.decl_node.decl.name,
                "' (declared at ", pos_link(self.decl_node.position), ")",
                " expects ", len(param_decls),
                # FIXME: Make this say "parameter" when there's only one?
                " parameters, but call at ", pos_link(position),
                " provides ", len(args.exprs),
            )
        # TODO: Also check type constraints.

    def constant_call(self, args, position=None):
        from alamatic.interpreter import (
            interpreter,
            NotConstantError,
            ReturnValueNotKnownError,
        )
        self._assert_correct_args(args, position=position)
        param_decls = self.decl_node.decl.param_decls

        # this will raise NotConstantError if any of the provided
        # expressions are not constant.
        arg_values = args.constant_values

        frame = interpreter.child_call_frame()
        symbols = self.decl_scope.create_child()

        with frame:
            with symbols:
                for i, arg_value in enumerate(arg_values):
                    param_decl = param_decls[i]
                    interpreter.declare_and_init(
                        param_decl.name,
                        arg_value,
                        position=args.exprs[i].position,
                    )
                    runtime_block = self.decl_node.block.execute()
                    if not runtime_block.is_empty:
                        raise NotConstantError(
                            "The function '%s'" % self.decl_node.decl.name,
                            " could not be executed "
                            "at compile time for ", pos_link(position),
                        )

        try:
            return frame.result
        except ReturnValueNotKnownError:
            raise NotConstantError(
                "The return value of function '%s'" % self.decl_node.decl.name,
                " could not be determined at compile time for "
                "at compile time for ", pos_link(position),
            )

    def instantiate(self, template_key, call_position=None):
        from alamatic.interpreter import (
            interpreter,
            RuntimeFunction,
            RuntimeFunctionArgs,
            InvalidParameterListError,
        )
        from alamatic.types import Void

        for key, instance in self.instances:
            if key == template_key:
                return instance

        param_decls = self.decl_node.decl.param_decls
        if len(param_decls) != len(template_key):
            raise InvalidParameterListError(
                "Template key for function template '",
                self.decl_node.decl.name,
                "' (declared at ", pos_link(self.decl_node.position), ")",
                " must have ", len(param_decls), " elements, but ",
                len(template_key), " were passed at ",
                pos_link(call_position), ".",
            )

        frame = interpreter.child_call_frame()
        symbols = self.decl_scope.create_child()
        symbols_list = []

        with frame:
            with symbols:

                for i, param_decl in enumerate(param_decls):
                    key_entry = template_key[i]

                    # TODO: Once we have support for constant parameters,
                    # we'll have a value rather than a type in key_entry
                    # and so we should call declare_and_init rather than
                    # just declare.

                    interpreter.declare(
                        param_decl.name,
                        key_entry,
                        # It'd be nicer to return the position of the
                        # actual expression that created the key entry,
                        # but we don't have that by the time we get in
                        # here so the position of the whole call will have
                        # to do for now.
                        position=call_position,
                    )
                    symbols_list.append(
                        interpreter.get_symbol(
                            param_decl.name,
                            position=call_position,
                        )
                    )

                with interpreter.force_runtime():
                    runtime_block = self.decl_node.block.execute()

        args_type = RuntimeFunctionArgs.make_args_type(symbols_list)

        result_type = frame.result_type

        instance = RuntimeFunction(
            self.decl_node.position,
            runtime_block,
            args_type,
            result_type,
        )

        self.instances.append(
            (template_key, instance),
        )

        return instance

    @classmethod
    def call(cls, callee_expr, arg_exprs, position=None):
        from alamatic.interpreter import (
            interpreter,
            NotConstantError,
        )
        from alamatic.ast import (
            ValueExpr,
            VoidExpr,
            RuntimeFunctionCallExpr,
        )

        try:
            callee = callee_expr.constant_value
        except NotConstantError:
            # We need to know which template we're calling at compile time,
            # since we can't instantiate a template at runtime.
            raise NotConstantError(
                "Call to FunctionTemplate at ", pos_link(position),
                " which can't be resolved at compile time."
            )

        try:
            registry = interpreter.child_registry()
            with registry:
                result = callee.constant_call(arg_exprs, position=position)
            interpreter.registry.merge_children([registry])
            if result is not None:
                return ValueExpr(
                    position,
                    result,
                )
            else:
                return VoidExpr(position)
        except NotConstantError:
            callee._assert_correct_args(arg_exprs, position=position)
            template_key = []
            for i, arg_expr in enumerate(arg_exprs.exprs):

                # TODO: handle const params, once the parser and AST actually
                # supports that concept. In that case, we'll put the constant
                # value of the expr in the template key, rather than the type.
                template_key.append(
                    arg_expr.result_type,
                )

            function = callee.instantiate(
                template_key,
                call_position=position,
            )

            args = function.args_type(arg_exprs)

            interpreter.register_runtime_function(function)

            # FIXME: Need to filter out the constant args somewhere,
            # since we don't want them to appear in the runtime function
            # declaration or calls.
            return RuntimeFunctionCallExpr(
                position,
                function,
                args,
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
