
from alamatic.ast import *


class Statement(AstNode):
    pass


class ErroredStatement(Statement):
    """
    Not a real statement, but rather a placeholder for where a potential
    statement was skipped due to an error.
    """
    def __init__(self, error):
        self.error = error


class ExpressionStmt(Statement):

    def __init__(self, source_range, expr):
        self.source_range = source_range
        self.expr = expr

    @property
    def child_nodes(self):
        yield self.expr


class PassStmt(Statement):
    pass


class LoopJumpStmt(Statement):
    pass


class BreakStmt(LoopJumpStmt):

    def get_target_label(self, symbols):
        return symbols.break_label

    @property
    def jump_type_name(self):
        return 'break'


class ContinueStmt(LoopJumpStmt):

    def get_target_label(self, symbols):
        return symbols.continue_label

    @property
    def jump_type_name(self):
        return 'continue'


class ReturnStmt(Statement):

    def __init__(self, source_range, expr=None):
        self.source_range = source_range
        self.expr = expr

    @property
    def child_nodes(self):
        if self.expr is not None:
            yield self.expr


class IfStmt(Statement):

    def __init__(self, source_range, clauses):
        self.source_range = source_range
        self.clauses = clauses

    @property
    def child_nodes(self):
        for clause in self.clauses:
            yield clause


class IfClause(AstNode):

    def __init__(self, source_range, test_expr, block):
        self.source_range = source_range
        self.test_expr = test_expr
        self.block = block

    @property
    def child_nodes(self):
        yield self.test_expr
        yield self.block


class ElseClause(AstNode):

    def __init__(self, source_range, block):
        self.source_range = source_range
        self.block = block

    @property
    def child_nodes(self):
        yield self.block


class WhileStmt(Statement):

    def __init__(self, source_range, test_expr, block):
        self.source_range = source_range
        self.test_expr = test_expr
        self.block = block

    @property
    def child_nodes(self):
        yield self.test_expr
        yield self.block


class ForStmt(Statement):

    def __init__(self, source_range, target, source_expr, block):
        # target is either a variable declaration or an lvalue expression
        self.source_range = source_range
        self.target = target
        self.source_expr = source_expr
        self.block = block

    @property
    def child_nodes(self):
        yield self.target
        yield self.source_expr
        yield self.block


class DataDeclStmt(Statement):

    def __init__(self, source_range, decl, expr):
        self.source_range = source_range
        self.decl = decl
        self.expr = expr

    @property
    def child_nodes(self):
        yield self.decl
        if self.expr is not None:
            yield self.expr


class FuncDeclStmt(Statement):

    def __init__(self, source_range, decl, block):
        self.source_range = source_range
        self.decl = decl
        self.block = block

    @property
    def child_nodes(self):
        yield self.decl
        yield self.block
