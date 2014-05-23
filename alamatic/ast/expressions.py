
from alamatic.ast import *
from alamatic.compilelogging import pos_link


class Expression(AstNode):
    can_be_statement = False

    def make_intermediate_form(self, elems, symbols):
        raise Exception(
            "make_intermediate_form is not implemented for %r" % self,
        )

    def get_lvalue_operand(self, elems, symbols):
        from alamatic.intermediate import InvalidLValueError
        raise InvalidLValueError(
            "Expression at ", pos_link(self.position), " is not assignable"
        )


class SymbolNameExpr(Expression):

    def __init__(self, position, name):
        self.position = position
        self.name = name

    @property
    def params(self):
        yield self.name

    def make_intermediate_form(self, elems, symbols):
        from alamatic.intermediate import (
            OperationInstruction,
            CopyOperation,
            SymbolOperand,
        )
        target = symbols.create_temporary().make_operand(
            position=self.position,
        )
        symbol = symbols.lookup(self.name, position=self.position)
        elems.append(
            OperationInstruction(
                target,
                CopyOperation(
                    SymbolOperand(
                        symbol,
                        position=self.position,
                    ),
                ),
                position=self.position,
            )
        )
        return target

    def get_lvalue_operand(self, elems, symbols):
        from alamatic.intermediate import (
            SymbolOperand,
        )
        return symbols.lookup(self.name, self.position).make_operand(
            position=self.position,
        )


class LiteralExpr(Expression):

    def __init__(self, position, value):
        self.position = position
        self.value = value

    @property
    def params(self):
        yield self.value


class IntegerLiteralExpr(LiteralExpr):

    def make_intermediate_form(self, elems, symbols):
        from alamatic.intermediate import (
            OperationInstruction,
            CopyOperation,
            ConstantOperand,
            SymbolOperand,
        )
        value = long(self.value)

        target = symbols.create_temporary().make_operand(
            position=self.position,
        )

        elems.append(
            OperationInstruction(
                target,
                CopyOperation(
                    ConstantOperand(
                        value,
                        position=self.position,
                    ),
                ),
                position=self.position,
            )
        )
        return target


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

    def make_intermediate_form(self, elems, symbols):
        from alamatic.intermediate import (
            OperationInstruction,
            BinaryOperation,
        )
        target = symbols.create_temporary().make_operand(
            position=self.position,
        )

        lhs_operand = self.lhs.make_intermediate_form(elems, symbols)
        rhs_operand = self.rhs.make_intermediate_form(elems, symbols)
        operator_name = self.operator_name

        elems.append(
            OperationInstruction(
                target,
                BinaryOperation(
                    lhs_operand,
                    operator_name,
                    rhs_operand,
                ),
                position=self.position,
            )
        )
        return target


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
    can_be_statement = True

    def make_intermediate_form(self, elems, symbols):
        # FIXME: This only supports the simple assign operation, but
        # this node type also needs to support all of the shorthands
        # like +=, -=, etc.
        from alamatic.intermediate import (
            OperationInstruction,
            CopyOperation,
        )

        lhs_operand = self.lhs.get_lvalue_operand(elems, symbols)
        rhs_operand = self.rhs.make_intermediate_form(elems, symbols)

        elems.append(
            OperationInstruction(
                lhs_operand,
                CopyOperation(
                    rhs_operand,
                ),
                position=self.position,
            )
        )

        return rhs_operand


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

    def __init__(self, position, callee_expr, args):
        self.position = position
        self.callee_expr = callee_expr
        self.args = args

    @property
    def child_nodes(self):
        yield self.callee_expr
        yield self.args

    def make_intermediate_form(self, elems, symbols):
        from alamatic.intermediate import (
            OperationInstruction,
            CallOperation,
        )

        callee_operand = self.callee_expr.make_intermediate_form(
            elems, symbols,
        )
        arg_operands = [
            x.make_intermediate_form(elems, symbols)
            for x in self.args.positional
        ]
        kwarg_operands = {
            # we evaluate the kwargs in a sorted order to ensure that
            # we'll evaluate them in some predictable (if arbitrary) order.
            k: self.args.keyword[k].make_intermediate_form(elems, symbols)
            for k in sorted(self.args.keyword)
        }
        target = symbols.create_temporary().make_operand(
            position=self.position,
        )
        elems.append(
            OperationInstruction(
                target,
                CallOperation(
                    callee_operand,
                    arg_operands,
                    kwarg_operands,
                    ),
                position=self.position,
            )
        )
        return target


class SubscriptExpr(Expression):
    def __init__(self, position, target_expr, args):
        self.position = position
        self.target_expr = target_expr
        self.args = args

    @property
    def child_nodes(self):
        yield self.target_expr
        yield self.args


class AttributeExpr(Expression):
    def __init__(self, position, target_expr, attr_name):
        self.position = position
        self.target_expr = target_expr
        self.attr_name = attr_name

    @property
    def params(self):
        yield self.attr_name

    @property
    def child_nodes(self):
        yield self.target_expr
