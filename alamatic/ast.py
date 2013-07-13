
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


class ExpressionStmt(Statement):

    def __init__(self, position, expr):
        self.position = position
        self.expr = expr

    @property
    def child_nodes(self):
        yield self.expr


class PassStmt(Statement):
    pass


class BreakStmt(Statement):
    pass


class ContinueStmt(Statement):
    pass


class ReturnStmt(Statement):

    def __init__(self, position, expr=None):
        self.position = position
        self.expr = expr

    @property
    def child_nodes(self):
        if self.expr is not None:
            yield self.expr


class IfStmt(Statement):

    def __init__(self, position, clauses):
        self.position = position
        self.clauses = clauses

    @property
    def child_nodes(self):
        for clause in self.clauses:
            yield clause


class IfClause(AstNode):

    def __init__(self, position, test_expr, stmts):
        self.position = position
        self.test_expr = test_expr
        self.stmts = stmts

    @property
    def child_nodes(self):
        yield self.test_expr
        for stmt in self.stmts:
            yield stmt


class ElseClause(AstNode):

    def __init__(self, position, stmts):
        self.position = position
        self.stmts = stmts

    @property
    def child_nodes(self):
        return self.stmts


class SymbolExpr(Expression):

    def __init__(self, position, symbol):
        self.position = position
        self.symbol = symbol

    @property
    def params(self):
        yield self.symbol


class LiteralExpr(Expression):

    def __init__(self, position, value):
        self.position = position
        self.value = value

    @property
    def params(self):
        yield self.value


class IntegerLiteralExpr(LiteralExpr):
    pass

class FloatLiteralExpr(LiteralExpr):
    pass
