
from alamatic.ast import *
from alamatic.compilelogging import pos_link
from alamatic.interpreter import (
    interpreter,
    UnknownSymbolError,
    InconsistentTypesError,
    IncompatibleTypesError,
)


class Expression(AstNode):

    def evaluate(self):
        raise Exception("evaluate is not implemented for %r" % self)

    @property
    def result_type(self):
        """
        Returns the type that will result from evaluating this expression.

        This method is only supported on the code generation tree generated
        by calls to :py:meth:`evaluate`, not on the parse tree generated
        by the parser, because the parse tree is generated before semantic
        analysis has been performed and thus has no type information present.
        """
        raise Exception("result_type is not implemented for %r" % self)


class SymbolExpr(Expression):

    def __init__(self, position, name):
        self.position = position
        self.name = name

    @property
    def params(self):
        yield self.name

    def evaluate(self):
        # If we know the value of the symbol then we can just return it.
        name = self.name
        if not interpreter.name_is_defined(name):
            raise UnknownSymbolError(name, self)

        if interpreter.value_is_known(name):
            return ValueExpr(
                self,
                interpreter.retrieve(name),
            )
        elif interpreter.storage_is_known(name):
            return SymbolStorageExpr(
                self,
                interpreter.get_storage(name),
            )
        else:
            raise InconsistentTypesError(
                "Type of symbol '", name ,"', "
                "referenced at ", pos_link(self.position),
                ", is not consistent",
            )


class LiteralExpr(Expression):

    def __init__(self, position, value):
        self.position = position
        self.value = value

    @property
    def params(self):
        yield self.value


class IntegerLiteralExpr(LiteralExpr):

    def evaluate(self):
        from alamatic.types import (
            Int8,
            Int16,
            Int32,
            Int64,
            UInt64,
        )
        src_value = long(self.value)
        for possible_type in (Int8, Int16, Int32, Int64, UInt64):
            limits = possible_type.get_limits()
            if src_value >= limits[0] and src_value <= limits[1]:
                return ValueExpr(
                    self,
                    possible_type(src_value),
                )

        # Should never happen
        raise Exception(
            "Integer value %i (in %r) does not fit in any integer type",
            self.value,
            self,
        )


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

    def evaluate(self):
        node_type = type(self)
        lhs_node = self.lhs.evaluate()
        rhs_node = self.rhs.evaluate()
        (lhs_node, rhs_node) = node_type.check_and_coerce_operands(
            self,
            lhs_node,
            self.op,
            rhs_node,
        )
        eval_node = node_type(
            lhs_node,
            self.op,
            rhs_node,
        )
        lhs_type = type(eval_node.lhs)
        rhs_type = type(eval_node.rhs)
        if lhs_type == lhs_type and lhs_type == ValueExpr:
            # Both sides are known at compile time, so we can do the
            # calculation right here.
            eval_val = type(eval_node).evaluate_values(
                self,
                lhs_type,
                eval_node.op,
                rhs_type,
            )
            return ValueExpr(
                self,
                eval_val,
            )
        else:
            return eval_node


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


class BinaryOpArithmeticExpr(BinaryOpExpr):

    def __init__(self, position, lhs, op, rhs, result_type=None):
        BinaryOpExpr.__init__(self, position, lhs, op, rhs)
        self._result_type = result_type
    @classmethod
    def check_and_coerce_operands(cls, source_node, lhs, op, rhs, position):
        lhs_type = lhs.result_type
        rhs_type = rhs.result_type
        if lhs_type == rhs_type:
            return (lhs, rhs)
        elif lhs_type.can_coerce_type(rhs_type):
            return (lhs, lhs_type.coerce_expr(rhs))
        elif rhs_type.can_coerce_type(lhs_type):
            return (rhs_type.coerce_expr(lhs), rhs)
        else:
            raise IncompatibleTypesError(
                "Cannot evaluate %s %s %s" % (
                    lhs_type.__name__,
                    op,
                    rhs_type.__name__,
                ),
                " at ", pos_link(source_node.position),
                ": incompatible types"
            )

    @property
    def result_type(self):
        return self._result_type


class SumExpr(BinaryOpArithmeticExpr):
    pass


class MultiplyExpr(BinaryOpArithmeticExpr):
    pass


class SignExpr(UnaryOpExpr):
    pass


class BitwiseNotExpr(UnaryOpExpr):
    pass


# The remaining nodes are never produced by the parser, but get substituted
# for literals and variable references when we produce the tree to feed into
# the code generator.

class ValueExpr(Expression):
    def __init__(self, source_node, value):
        self.source_node = source_node
        self.position = source_node.position
        self.value = value

    @property
    def params(self):
        yield self.value

    def evaluate(self):
        return self

    @property
    def result_type(self):
        return type(self.value)


class SymbolStorageExpr(Expression):
    def __init__(self, source_node, storage):
        self.source_node = source_node
        self.position = source_node.position
        self.storage = storage

    @property
    def params(self):
        yield self.storage

    def evaluate(self):
        return self

    @property
    def result_type(self):
        return self.storage.type
