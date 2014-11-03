

class AstNode(object):
    source_range = None

    def __init__(self, source_range):
        self.source_range = source_range

    @property
    def child_nodes(self):
        return []

    @property
    def params(self):
        return []

    def __str__(self):
        return type(self).__name__ + "(" + (','.join(
            (str(x) for x in self.params)
        )) + " : " + repr(self.source_range) + ")"

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
    def __init__(self, stmts, source_range=None):
        self.stmts = stmts
        self.source_range = source_range

    @property
    def child_nodes(self):
        return self.stmts

    @property
    def is_empty(self):
        return len(self.stmts) == 0


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

    def __init__(self, source_range, name, block, doc=None):
        self.name = name
        self.block = block
        self.source_range = source_range
        self.doc = doc

    @property
    def params(self):
        return [self.name]

    @property
    def child_nodes(self):
        yield self.block


class EntryFile(AstNode):

    def __init__(self, source_range, block, doc=None):
        self.block = block
        self.source_range = source_range
        self.doc = doc

    @property
    def child_nodes(self):
        yield self.block


# These imports depend on the above symbols, so they must appear after
# them in this file.
from alamatic.ast.statements import *
from alamatic.ast.expressions import *
from alamatic.ast.declarations import *
