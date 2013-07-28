
import unittest
from alamatic.ast import *
from alamatic.types import *


class TestInterpreterExec(unittest.TestCase):

    def test_expression_stmt(self):
        class Dummy1Expr(Expression):
            evaluated = False
            def evaluate(self):
                Dummy1Expr.evaluated = True
                return ValueExpr(self, UInt8(1))
        class Dummy2Expr(Expression):
            evaluated = False
            def evaluate(self):
                Dummy2Expr.evaluated = True
                return Dummy2Expr(self.position)
            @property
            def result_type(self):
                return UInt8

        stmt = ExpressionStmt(None, Dummy1Expr(None))
        runtime_stmts = []
        stmt.execute(runtime_stmts)
        self.assertEqual(
            runtime_stmts,
            [],
        )
        self.assertTrue(
            Dummy1Expr.evaluated,
            "Didn't evaluate Dummy1Expr",
        )

        stmt = ExpressionStmt(None, Dummy2Expr(None))
        runtime_stmts = []
        stmt.execute(runtime_stmts)
        self.assertEqual(
            len(runtime_stmts),
            1,
        )
        self.assertEqual(
            type(runtime_stmts[0]),
            ExpressionStmt,
        )
        self.assertEqual(
            type(runtime_stmts[0].expr),
            Dummy2Expr,
        )
        self.assertTrue(
            Dummy2Expr.evaluated,
            "Didn't evaluate Dummy2Expr",
        )

