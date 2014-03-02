

class AstNode(object):
    position = None

    def __init__(self, position):
        self.position = position

    @property
    def child_nodes(self):
        return []

    @property
    def params(self):
        return []

    def __str__(self):
        return type(self).__name__ + "(" + (','.join(
            (str(x) for x in self.params)
        )) + " : " + repr(self.position) + ")"

    def as_tree_rows(self, indent=0):
        yield ("  " * indent) + "- " + str(self)
        for child in self.child_nodes:
            g = child.as_tree_rows(indent + 1)
            for row in g:
                yield row

    def find_assigned_symbols(self):
        for child_node in self.child_nodes:
            for symbol in child_node.find_assigned_symbols():
                yield symbol

    def __repr__(self):
        return "<alamatic.ast.%s>" % str(self)


class StatementBlock(AstNode):
    def __init__(self, stmts, symbols=None):
        self.stmts = stmts
        # symbols is only populated in a code generation tree; it's
        # always None in a parse tree.
        self.symbols = symbols

    @property
    def child_nodes(self):
        return self.stmts

    @property
    def is_empty(self):
        return len(self.stmts) == 0

    def make_intermediate_form(self, elems, parent_symbols):
        symbols = parent_symbols.create_child()
        for stmt in self.stmts:
            stmt.make_intermediate_form(elems, symbols)


class Arguments(AstNode):
    def __init__(self, pos_exprs, kw_exprs):
        self.pos_exprs = pos_exprs
        self.kw_exprs = kw_exprs

    @property
    def positional(self):
        return self.pos_exprs

    @property
    def keyword(self):
        return self.kw_exprs

    @property
    def child_nodes(self):
        for expr in self.pos_exprs:
            yield expr
        for key in sorted(self.kw_exprs):
            yield self.kw_exprs[key]

    @property
    def params(self):
        for i, expr in enumerate(self.pos_exprs):
            yield i
        for key in sorted(self.kw_exprs):
            yield key


class ExpressionList(AstNode):
    def __init__(self, exprs):
        self.exprs = exprs

    @property
    def child_nodes(self):
        return self.exprs

    def evaluate(self):
        # Note that ExpressionList isn't an Expression, so this is not the
        # expression evaluate() interface even though the method has the
        # same name.
        evaled_exprs = [
            x.evaluate() for x in self.exprs
        ]
        return ExpressionList(
            evaled_exprs,
        )

    @property
    def has_all_constant_values(self):
        return all(x.has_constant_value for x in self.exprs)

    @property
    def constant_values(self):
        return [
            x.constant_value for x in self.exprs
        ]


class Module(AstNode):

    def __init__(self, position, name, block, doc=None):
        self.name = name
        self.block = block
        self.position = position
        self.doc = doc

    @property
    def params(self):
        return [self.name]

    @property
    def child_nodes(self):
        yield self.block

    def get_intermediate_form(self):
        from alamatic.intermediate import (
            SymbolTable,
            Unit,
        )
        from alamatic.intermediate import build_control_flow_graph
        symbols = SymbolTable()
        elems = []
        self.block.make_intermediate_form(elems, symbols)
        graph = build_control_flow_graph(elems)
        return Unit(
            graph=graph,
            symbols=symbols,
            # FIXME: Need to figure out what sort of thing this parameter
            # list will be. Modules don't need it but functions will later.
            params=[],
        )

    def execute(self):
        """
        Execute the module and generate a
        :py:class:`alamatic.interpreter.RuntimeFunction` object representing
        its main body.

        Along the way the other items that this module uses will be written
        to the currently-active data state. Therefore in order to produce
        a complete :py:class:`alamatic.codegen.RuntimeProgram` these
        additional objects must also be included by the caller.
        """
        from alamatic.interpreter import (
            interpreter,
            RuntimeFunction,
            RuntimeFunctionArgs,
            SymbolTable,
        )
        from alamatic.types import (
            Void,
        )

        # Modules don't take any parameters, but a RuntimeFunction uses
        # a scope to describe its arguments so we need to create an empty
        # one in this case.
        param_symbols = interpreter.child_symbol_table()

        with param_symbols:
            runtime_block = self.block.execute()

        interpreter.register_top_level_scope(runtime_block.symbols)

        args_type = RuntimeFunctionArgs.make_args_type([])

        function = RuntimeFunction(
            self.position,
            runtime_block,
            args_type,
            # Modules never return anything.
            Void,
        )

        interpreter.register_runtime_function(function)

        return function


# These imports depend on the above symbols, so they must appear after
# them in this file.
from alamatic.ast.statements import *
from alamatic.ast.expressions import *
from alamatic.ast.declarations import *
