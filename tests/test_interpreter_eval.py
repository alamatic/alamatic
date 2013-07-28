
import unittest
import functools
from alamatic.ast import *
from alamatic.interpreter import (
    interpreter,
    UnknownSymbolError,
    InconsistentTypesError,
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
        interpreter.declare('a', 1)
        interpreter.declare('b')
        interpreter.declare('c')

        interpreter.mark_unknown('b', known_type=int)

        src_a = SymbolExpr(None, "a")
        src_b = SymbolExpr(None, "b")
        src_c = SymbolExpr(None, "c")
        src_d = SymbolExpr(None, "d")

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
            SymbolStorageExpr,
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
            InconsistentTypesError,
            src_c.evaluate,
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
