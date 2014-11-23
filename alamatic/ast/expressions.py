
from alamatic.ast import *


class Expression(AstNode):
    can_be_statement = False
    can_be_lvalue = False


class ErroredExpression(Expression):
    """
    Not a real expression, but rather a placeholder for where a potential
    expression was skipped due to an error.
    """
    def __init__(self, error):
        self.error = error


class SymbolNameExpr(Expression):
    can_be_lvalue = True

    def __init__(self, source_range, name):
        self.source_range = source_range
        self.name = name

    @property
    def params(self):
        yield self.name


class LiteralExpr(Expression):

    def __init__(self, source_range, value):
        self.source_range = source_range
        self.value = value

    @property
    def params(self):
        yield self.value


class BinaryOpExpr(Expression):

    def __init__(self, source_range, lhs, op, rhs):
        self.source_range = source_range
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

    def __init__(self, source_range, operand, op):
        self.source_range = source_range
        self.operand = operand
        self.op = op

    @property
    def params(self):
        yield self.op

    @property
    def child_nodes(self):
        yield self.operand


class AssignExpr(BinaryOpExpr):
    can_be_statement = True


class LogicalOrExpr(BinaryOpExpr):
    pass


class LogicalNotExpr(UnaryOpExpr):
    pass


class LogicalAndExpr(BinaryOpExpr):
    pass


class ComparisonExpr(BinaryOpExpr):

    @property
    def operator_name(self):
        if self.op == "==":
            return "equals"
        elif self.op == "!=":
            return "not_equals"
        elif self.op == "<":
            return "is_less_than"
        elif self.op == "<=":
            return "is_less_than_or_equal_to"
        elif self.op == ">":
            return "is_greater_than"
        elif self.op == ">=":
            return "is_greater_than_or_equal_to"
        else:
            raise Exception("Unknown ComparisonExpr operator " + self.op)


class BitwiseOrExpr(BinaryOpExpr):
    pass


class BitwiseAndExpr(BinaryOpExpr):
    pass


class ShiftExpr(BinaryOpExpr):
    pass


class BinaryOpArithmeticExpr(BinaryOpExpr):
    pass


class SumExpr(BinaryOpArithmeticExpr):

    @property
    def operator_name(self):
        if self.op == "+":
            return "add"
        elif self.op == "-":
            return "subtract"
        else:
            raise Exception("Unknown SumExpr operator " + self.op)


class MultiplyExpr(BinaryOpArithmeticExpr):

    @property
    def operator_name(self):
        if self.op == "*":
            return "multiply"
        elif self.op == "%":
            return "modulo"
        elif self.op == "/":
            return "divide"
        else:
            raise Exception("Unknown MultiplyExpr operator " + self.op)


class SignExpr(UnaryOpExpr):
    pass


class BitwiseNotExpr(UnaryOpExpr):
    pass


class CallExpr(Expression):
    can_be_statement = True

    def __init__(self, source_range, callee_expr, args):
        self.source_range = source_range
        self.callee_expr = callee_expr
        self.args = args

    @property
    def child_nodes(self):
        yield self.callee_expr
        yield self.args


class SubscriptExpr(Expression):
    can_be_lvalue = True

    def __init__(self, source_range, target_expr, args):
        self.source_range = source_range
        self.target_expr = target_expr
        self.args = args

    @property
    def child_nodes(self):
        yield self.target_expr
        yield self.args


class AttributeExpr(Expression):
    can_be_lvalue = True

    def __init__(self, source_range, target_expr, attr_name):
        self.source_range = source_range
        self.target_expr = target_expr
        self.attr_name = attr_name

    @property
    def params(self):
        yield self.attr_name

    @property
    def child_nodes(self):
        yield self.target_expr
