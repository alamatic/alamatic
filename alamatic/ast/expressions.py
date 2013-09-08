
from alamatic.ast import *
from alamatic.compilelogging import pos_link
from alamatic.interpreter import (
    interpreter,
    UnknownSymbolError,
    IncompatibleTypesError,
    SymbolNotInitializedError,
    InvalidAssignmentError,
    SymbolValueNotKnownError,
    NotConstantError,
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

    def assign(self, expr):
        raise InvalidAssignmentError(
            "Invalid assignment target at ", pos_link(self.position)
        )

    @property
    def constant_value(self):
        raise NotConstantError(
            "Value of expression at ", pos_link(self.position),
            "cannot be determined at compile time."
        )

    @property
    def has_constant_value(self):
        try:
            value = self.constant_value
        except NotConstantError:
            return False
        else:
            return True


class SymbolNameExpr(Expression):

    def __init__(self, position, name):
        self.position = position
        self.name = name

    @property
    def params(self):
        yield self.name

    def evaluate(self):
        # If we know the value of the symbol then we can just return it.
        name = self.name

        try:
            value = interpreter.retrieve(name, position=self.position)
        except SymbolValueNotKnownError:
            symbol = interpreter.get_symbol(name, position=self.position)
            interpreter.mark_symbol_used_at_runtime(symbol, self.position)
            return SymbolExpr(
                self.position,
                symbol,
            )
        else:
            return ValueExpr(
                self.position,
                interpreter.retrieve(name),
            )

    def assign(self, expr):
        name = self.name

        symbol = interpreter.get_symbol(name, position=self.position)

        symbol_expr = SymbolExpr(
            self.position,
            symbol,
        )
        return symbol_expr.assign(expr)


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
                    self.position,
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
        return method(lhs, rhs, position=self.position)

    def generate_c_code(self, state, writer):
        writer.write("(")
        self.lhs.generate_c_code(state, writer)
        writer.write(" ", self.c_operator, " ")
        self.rhs.generate_c_code(state, writer)
        writer.write(")")


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

    def evaluate(self):
        # FIXME: This only supports the simple assign operation, but
        # this node type also needs to support all of the shorthands
        # like +=, -=, etc.
        rhs = self.rhs.evaluate()
        return self.lhs.assign(rhs)

    @property
    def c_operator(self):
        return "="


class LogicalOrExpr(BinaryOpExpr):
    pass


class LogicalNotExpr(UnaryOpExpr):
    pass


class LogicalAndExpr(BinaryOpExpr):
    pass


class ComparisonExpr(BinaryOpExpr):

    @property
    def type_impl_method_name(self):
        if self.op == "==":
            return "equals"
        elif self.op == "!=":
            return "not_equals"
        else:
            raise Exception("Unknown ComparisonExpr operator " + self.op)

    @property
    def result_type(self):
        from alamatic.types import Bool
        return Bool

    @property
    def c_operator(self):
        if self.op == "==":
            return "=="
        elif self.op == "!=":
            return "!="
        else:
            raise Exception("Unknown ComparisonExpr operator " + self.op)


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

    @property
    def c_operator(self):
        if self.op == "+":
            return "+"
        elif self.op == "-":
            return "-"
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


class CallExpr(Expression):
    def __init__(self, position, callee_expr, args):
        self.position = position
        self.callee_expr = callee_expr
        self.args = args

    @property
    def child_nodes(self):
        yield self.callee_expr
        yield self.args

    def evaluate(self):
        callee_expr = self.callee_expr.evaluate()
        args = self.args.evaluate()

        callee_type = callee_expr.result_type
        return callee_type.call(callee_expr, args, position=self.position)


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


# The remaining nodes are never produced by the parser, but get substituted
# for literals and variable references when we produce the tree to feed into
# the code generator.

class ValueExpr(Expression):
    def __init__(self, position, value):
        self.position = position
        self.value = value

    @property
    def params(self):
        yield self.value

    def evaluate(self):
        return self

    @property
    def result_type(self):
        return type(self.value)

    def generate_c_code(self, state, writer):
        self.value.generate_c_code(state, writer)

    @property
    def constant_value(self):
        return self.value


class SymbolExpr(Expression):
    def __init__(self, position, symbol):
        self.position = position
        self.symbol = symbol

    @property
    def params(self):
        yield self.symbol

    def evaluate(self):
        return self

    def assign(self, expr):
        from alamatic.interpreter import interpreter
        try:
            value = expr.constant_value
            interpreter.set_symbol_value(
                self.symbol,
                value,
                position=self.position,
            )
        except NotConstantError:
            interpreter.mark_symbol_unknown(
                self.symbol,
                expr.result_type,
                position=self.position,
            )

        if self.symbol.const:
            # Just return the expression alone if the symbol is a constant,
            # since we can't assign to it at runtime anyway. The resulting
            # expression will end up being a no-op value that should get
            # optimized away by the code generator.
            return expr
        else:
            interpreter.mark_symbol_used_at_runtime(
                self.symbol,
                self.position,
            )
            return AssignExpr(
                self.position,
                SymbolExpr(
                    self.position,
                    self.symbol,
                ),
                "=",
                expr,
            )

    @property
    def result_type(self):
        from alamatic.interpreter import interpreter
        return interpreter.get_symbol_type(self.symbol)

    def generate_c_code(self, state, writer):
        writer.write(
            self.symbol.codegen_name,
        )


class RuntimeFunctionCallExpr(Expression):
    def __init__(self, position, function, args):
        self.position = position
        self.function = function
        self.args = args

    @property
    def result_type(self):
        return self.function.return_type

    def generate_c_code(self, state, writer):
        writer.write(
            self.function.codegen_name,
        )
        writer.write("(")
        first = True
        for arg_expr in self.args.arg_exprs.exprs:
            if not first:
                writer.write(", ")
            else:
                first = False
            arg_expr.generate_c_code(state, writer)
        writer.write(")")


class VoidExpr(Expression):

    def __init__(self, position):
        self.position = position

    @property
    def result_type(self):
        from alamatic.types import Void
        return Void

    def generate_c_code(self, state, writer):
        # This should never get called if our type system is doing its work,
        # but just to complete the interface we'll produce something that'll
        # cause valid C syntax, though presumably not valid semantics.
        writer.write("((void)0)")
