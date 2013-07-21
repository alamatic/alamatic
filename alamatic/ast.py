
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


class BinaryOpExpr(Expression):

    def __init__(self, position, lhs, op, rhs):
        self.position = position
        self.lhs = lhs
        self.op = op
        self.rhs = rhs

    @property
    def params(self):
        yield self.op

    @property
    def child_nodes(self):
        yield self.lhs
        yield self.rhs


class UnaryOpExpr(Expression):

    def __init__(self, position, operand, op):
        self.position = position
        self.operand = operand
        self.op = op

    @property
    def params(self):
        yield self.op

    @property
    def child_nodes(self):
        yield self.operand


class AssignExpr(BinaryOpExpr):
    pass


class LogicalOrExpr(BinaryOpExpr):
    pass


class LogicalNotExpr(UnaryOpExpr):
    pass


class LogicalAndExpr(BinaryOpExpr):
    pass


class ComparisonExpr(BinaryOpExpr):
    pass


class BitwiseOrExpr(BinaryOpExpr):
    pass


class BitwiseAndExpr(BinaryOpExpr):
    pass


class ShiftExpr(BinaryOpExpr):
    pass


class SumExpr(BinaryOpExpr):
    pass


class MultiplyExpr(BinaryOpExpr):
    pass


class SignExpr(UnaryOpExpr):
    pass


class BitwiseNotExpr(UnaryOpExpr):
    pass


class DataDeclClause(AstNode):

    def __init__(self, position, name):
        self.position = position
        self.name = name

    @property
    def params(self):
        yield self.name


class VarDeclClause(DataDeclClause):
    pass


class ConstDeclClause(DataDeclClause):
    pass


class FuncDeclClause(AstNode):

    def __init__(self, position, name, param_decls):
        self.position = position
        self.name = name
        self.param_decls = param_decls

    @property
    def params(self):
        yield self.name

    @property
    def child_nodes(self):
        return self.param_decls


class ParamDeclClause(AstNode):

    def __init__(self, position, name, type_expr):
        self.position = position
        self.name = name
        self.type_expr = type_expr

    @property
    def params(self):
        yield self.name

    @property
    def child_nodes(self):
        if self.type_expr is not None:
            yield self.type_expr
