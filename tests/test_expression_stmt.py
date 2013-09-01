
from alamatic.ast import *
from alamatic.types import *
from alamatic.testutil import *


class TestExpressionStmt(LanguageTestCase):

    def test_parser(self):
        self.assertStmtParseTree(
            "baz",
            [
                ("ExpressionStmt", (), [
                    ('SymbolNameExpr', ('baz',), []),
                ]),
            ]
        )

    def test_execute(self):
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

        compile_time_expr = DummyExprCompileTime("a")
        runtime_expr = DummyExprRuntime("b")

        self.assertCodegenTree(
            ExpressionStmt(None, compile_time_expr),
            [],
        )
        self.assertTrue(
            compile_time_expr.evaluated,
            "Didn't evaluate compile_time_expr",
        )

        self.assertCodegenTree(
            ExpressionStmt(None, runtime_expr),
            [
                ('ExpressionStmt', (), [
                    ('DummyExprRuntime', ('b', DummyType), []),
                ]),
            ],
        )
        self.assertTrue(
            runtime_expr.evaluated,
            "Didn't evaluate runtime_expr",
        )
