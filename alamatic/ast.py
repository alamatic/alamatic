
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


class Module(AstNode):

    def __init__(self, position, name, stmts):
        self.name = name
        self.stmts = stmts
        self.position = position

    @property
    def params(self):
        return [self.name]

    @property
    def child_nodes(self):
        return self.stmts


class Statement(AstNode):
    pass


class Expression(AstNode):
    pass


class ExpressionStatement(Statement):

    def __init__(self, position, expr):
        self.position = position
        self.expr = expr

    @property
    def child_nodes(self):
        yield self.expr


class PassStatement(Statement):
    pass


class BreakStatement(Statement):
    pass


class ContinueStatement(Statement):
    pass


class SymbolExpression(Expression):

    def __init__(self, position, symbol):
        self.position = position
        self.symbol = symbol

    @property
    def params(self):
        yield self.symbol


class LiteralExpression(Expression):

    def __init__(self, position, value):
        self.position = position
        self.value = value

    @property
    def params(self):
        yield self.value


class IntegerLiteralExpression(LiteralExpression):
    pass

class FloatLiteralExpression(LiteralExpression):
    pass
