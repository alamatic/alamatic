
from alamatic.ast import *
from alamatic.compilelogging import pos_link
from alamatic.interpreter import (
    interpreter,
    UnknownSymbolError,
    InconsistentTypesError,
)


class Expression(AstNode):

    def evaluate(self):
        raise Exception("evaluate is not implemented for %r" % self)


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


class SymbolStorageExpr(Expression):
    def __init__(self, source_node, storage):
        self.source_node = source_node
        self.position = source_node.position
        self.storage = storage

    @property
    def params(self):
        yield self.storage
