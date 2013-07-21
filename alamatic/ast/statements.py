
from alamatic.ast import *


class Statement(AstNode):
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


class WhileStmt(Statement):

    def __init__(self, position, test_expr, stmts):
        self.position = position
        self.test_expr = test_expr
        self.stmts = stmts

    @property
    def child_nodes(self):
        yield self.test_expr
        for stmt in self.stmts:
            yield stmt


class ForStmt(Statement):

    def __init__(self, position, target, source_expr, stmts):
        # target is either a variable declaration or an lvalue expression
        self.position = position
        self.target = target
        self.source_expr = source_expr
        self.stmts = stmts

    @property
    def child_nodes(self):
        yield self.target
        yield self.source_expr
        for stmt in self.stmts:
            yield stmt


class DataDeclStmt(Statement):

    def __init__(self, position, decl, expr):
        self.position = position
        self.decl = decl
        self.expr = expr

    @property
    def child_nodes(self):
        yield self.decl
        if self.expr is not None:
            yield self.expr


class FuncDeclStmt(Statement):

    def __init__(self, position, decl, stmts):
        self.position = position
        self.decl = decl
        self.stmts = stmts

    @property
    def child_nodes(self):
        yield self.decl
        for stmt in self.stmts:
            yield stmt
