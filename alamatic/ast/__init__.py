
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
            g = child.as_tree_rows(indent+1)
            for row in g:
                yield row

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
        return len(self.stmts) > 0

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
            union_braces = writer.braces(trailing_newline=False)
            if symbol.codegen_uses_union:
                writer.write("typedef union")
                union_type_name = symbol.codegen_name + "_type"
                union_braces.__enter__()
            for storage in symbol.storages:
                if symbol.const:
                    writer.write("const ")
                writer.write(storage.type.c_type_spec(), " ")
                writer.write(storage.codegen_name);
                if symbol.const:
                    writer.write(" = ")
                    # TODO: Need to make the data state visible in
                    # here so that we can see the constant's value.
                    writer.write("0");
                writer.writeln(";")
            if symbol.codegen_uses_union:
                union_braces.__exit__()
                writer.writeln(
                    " ",
                    union_type_name,
                    ";",
                )
                writer.writeln(
                    union_type_name,
                    " ",
                    symbol.codegen_name,
                    ";"
                )

    def generate_body_c_code(self, state, writer):
        for stmt in self.stmts:
            stmt.generate_c_code(state, writer)

    def generate_c_code(self, state, writer):
        with writer.braces():
            self.generate_decl_c_code(state, writer)
            self.generate_body_c_code(state, writer)


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


# These imports depend on the above symbols, so they must appear after
# them in this file.
from alamatic.ast.statements import *
from alamatic.ast.expressions import *
from alamatic.ast.declarations import *
