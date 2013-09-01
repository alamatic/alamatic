
import unittest
import functools
from alamatic.ast import *
from alamatic.interpreter import (
    interpreter,
    UnknownSymbolError,
    SymbolTable,
    DataState,
)


def state(func=None):
    if func is not None:
        @functools.wraps(func)
        def ret(self):
            with state():
                func(self)
        return ret

    class TestState:
        def __init__(self, symbols, data):
            self.symbols = symbols
            self.data = data

        def __enter__(self):
            self.symbols.__enter__()
            self.data.__enter__()

        def __exit__(self, *args):
            self.symbols.__exit__(*args)
            self.data.__exit__(*args)

    return TestState(
        SymbolTable(),
        DataState(),
    )


class TestInterpreterEval(unittest.TestCase):

    @state
    def test_symbol_expr(self):
        interpreter.declare_and_init('a', 1)
        interpreter.declare_and_init('b', 2)

        interpreter.mark_unknown('b', known_type=int)

        src_a = SymbolNameExpr(None, "a")
        src_b = SymbolNameExpr(None, "b")
        src_d = SymbolNameExpr(None, "d")

        result_a = src_a.evaluate()
        result_b = src_b.evaluate()

        self.assertEqual(
            type(result_a),
            ValueExpr,
        )
        self.assertEqual(
            result_a.source_node,
            src_a,
        )
        self.assertEqual(
            result_a.result_type,
            int,
        )
        self.assertEqual(
            type(result_b),
            SymbolExpr,
        )
        self.assertEqual(
            result_b.source_node,
            src_b,
        )
        self.assertEqual(
            result_b.result_type,
            int,
        )

        self.assertRaises(
            UnknownSymbolError,
            src_d.evaluate,
        )

    @state
    def test_integer_literal_expr(self):
        from alamatic.types import (
            Int8,
            Int16,
            Int32,
            Int64,
            UInt64,
        )

        tests = [
            (Int8, 127),
            (Int8, -128),
            (Int16, 128),
            (Int16, 32767),
            (Int16, -32768),
            (Int32, 32768),
            (Int32, -32769),
            (Int64, 2 ** 32),
            (Int64, -2 ** 32),
            (UInt64, (2 ** 64) - 1),
        ]

        for expected_type, src_value in tests:
            src_node = IntegerLiteralExpr(None, src_value)
            eval_node = src_node.evaluate()
            self.assertEqual(
                type(eval_node),
                ValueExpr,
            )
            self.assertEqual(
                type(eval_node.value),
                expected_type,
            )

    @state
    def test_arithmetic_ops(self):
        from alamatic.types import Value

        # These are arrays just so we can modify them in the closures
        # in the classes below.
        performed = []

        # Some mock types so we can test the expression behavior without
        # depending on the behavior of any specific type.
        class Dummy1(Value):
            @classmethod
            def add(cls, source_node, lhs, rhs):
                performed.append("add")
                return source_node
            @classmethod
            def multiply(cls, source_node, lhs, rhs):
                performed.append("multiply")
                return source_node
        class Dummy2(Value):
            @classmethod
            def subtract(cls, source_node, lhs, rhs):
                performed.append("subtract")
                return source_node
            @classmethod
            def divide(cls, source_node, lhs, rhs):
                performed.append("divide")
                return source_node
            @classmethod
            def modulo(cls, source_node, lhs, rhs):
                performed.append("modulo")
                return source_node

        val1 = Dummy1()
        val2 = Dummy2()

        # Add

        lhs = ValueExpr(None, val1)
        rhs = ValueExpr(None, val2)

        src_node = SumExpr(None, lhs, "+", rhs)
        eval_node = src_node.evaluate()
        self.assertEqual(
            src_node,
            eval_node,
        )

        # Subtract (Swap sides this time)
        rhs = ValueExpr(None, val1)
        lhs = ValueExpr(None, val2)

        src_node = SumExpr(None, lhs, "-", rhs)
        eval_node = src_node.evaluate()
        self.assertEqual(
            src_node,
            eval_node,
        )

        # Multiply (Swap back)
        lhs = ValueExpr(None, val1)
        rhs = ValueExpr(None, val2)

        src_node = MultiplyExpr(None, lhs, "*", rhs)
        eval_node = src_node.evaluate()
        self.assertEqual(
            src_node,
            eval_node,
        )

        # Divide (And swap again)
        rhs = ValueExpr(None, val1)
        lhs = ValueExpr(None, val2)

        src_node = MultiplyExpr(None, lhs, "/", rhs)
        eval_node = src_node.evaluate()
        self.assertEqual(
            src_node,
            eval_node,
        )

        # Modulo
        rhs = ValueExpr(None, val1)
        lhs = ValueExpr(None, val2)

        src_node = MultiplyExpr(None, lhs, "%", rhs)
        eval_node = src_node.evaluate()
        self.assertEqual(
            src_node,
            eval_node,
        )

        self.assertEqual(
            performed,
            [
                "add",
                "subtract",
                "multiply",
                "divide",
                "modulo",
            ],
        )
