
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
    def __init__(self, stmts, scope=None):
        self.stmts = stmts
        # scope is only populated in a code generation tree; it's
        # always None in a parse tree.
        self.scope = scope

    @property
    def child_nodes(self):
        return self.stmts


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
