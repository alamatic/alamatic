

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

    def execute(self):
        # Note that StatementBlock isn't a Statement, so this is not the
        # statement execute() interface even though the method has the
        # same name.
        from alamatic.interpreter import interpreter
        with interpreter.child_symbol_table() as symbols:
            runtime_stmts = []
            for stmt in self.stmts:
                stmt.execute(runtime_stmts)
            return StatementBlock(
                runtime_stmts,
                symbols,
            )

    @property
    def inlined(self):
        from alamatic.ast import InlineStatementBlock
        return InlineStatementBlock(self)

    def generate_decl_c_code(self, state, writer):
        for symbol in self.symbols.local_symbols:
            if not symbol.is_used_at_runtime:
                # Don't bother generating any symbols that aren't used
                # at runtime.
                continue
            if symbol.const:
                writer.write("const ")
            if not symbol.is_definitely_initialized:
                # Should never happen
                raise Exception(
                    "Symbol used at runtime but never initialized"
                )
            writer.write(symbol.get_type().c_type_spec(), " ")
            writer.write(symbol.codegen_name)
            if symbol.const:
                writer.write(" = ")
                symbol.get_value().generate_c_code(state, writer)
            writer.writeln(";")

    def generate_body_c_code(self, state, writer):
        for stmt in self.stmts:
            stmt.generate_c_code(state, writer)

    def generate_c_code(self, state, writer):
        with writer.braces():
            self.generate_decl_c_code(state, writer)
            self.generate_body_c_code(state, writer)


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

    def __init__(self, position, name, block):
        self.name = name
        self.block = block
        self.position = position

    @property
    def params(self):
        return [self.name]

    @property
    def child_nodes(self):
        yield self.block

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
