
import unittest
from alamatic.ast import *
from alamatic.interpreter import (
    interpreter,
    UnknownSymbolError,
    InconsistentTypesError,
    SymbolTable,
    DataState,
)


class TestInterpreterEval(unittest.TestCase):

    def state(self):
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

    def test_symbol_expr(self):
        with self.state():
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
                type(result_b),
                SymbolStorageExpr,
            )
            self.assertEqual(
                result_b.source_node,
                src_b,
            )

            self.assertRaises(
                InconsistentTypesError,
                src_c.evaluate,
            )
            self.assertRaises(
                UnknownSymbolError,
                src_d.evaluate,
            )
