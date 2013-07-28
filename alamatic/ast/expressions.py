
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
        method_name = self.type_impl_method_name
        lhs = self.lhs.evaluate()
        rhs = self.rhs.evaluate()
        method = getattr(lhs.result_type, method_name)
        return method(self, lhs, rhs)


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

    @property
    def result_type(self):
        return self._result_type


class SumExpr(BinaryOpArithmeticExpr):

    @property
    def type_impl_method_name(self):
        if self.op == "+":
            return "add"
        elif self.op == "-":
            return "subtract"
        else:
            raise Exception("Unknown SumExpr operator " + self.op)


class MultiplyExpr(BinaryOpArithmeticExpr):

    @property
    def type_impl_method_name(self):
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


# The remaining nodes are never produced by the parser, but get substituted
# for literals and variable references when we produce the tree to feed into
# the code generator.

class ValueExpr(Expression):
    def __init__(self, source_node, value):
        self.source_node = source_node
        if source_node is not None:
            self.position = source_node.position
        else:
            self.position = None
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
        if source_node is not None:
            self.position = source_node.position
        else:
            self.position = None
        self.storage = storage

    @property
    def params(self):
        yield self.storage

    def evaluate(self):
        return self

    @property
    def result_type(self):
        return self.storage.type
