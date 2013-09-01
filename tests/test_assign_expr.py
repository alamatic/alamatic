
from alamatic.ast import *
from alamatic.types import *
from alamatic.testutil import *


class TestParse(LanguageTestCase):

    def test_parse(self):
        for operator in ("=", "+=", "-=", "*=", "/=", "|=", "&="):
            self.assertExprParseTree(
                "a %s 1" % operator,
                ('AssignExpr', (operator,), [
                    ('SymbolNameExpr', ('a',), []),
                    ('IntegerLiteralExpr', (1,), []),
                ]),
                allow_assign=True,
            )
        # But chaining is not allowed
        self.assertErrorsInExpr(
            "a = b = 1",
            [
                (1, 6),
            ],
            allow_assign=True,
        )


class TestExec(LanguageTestCase):

    def test_plain_assign(self):
        test_expr = AssignExpr(
            ('test', 1, 0),
            DummyExprLvalue(
                'target',
            ),
            '=',
            DummyExprRuntime(
                'value',
            ),
        )
        test_stmt = ExpressionStmt(
            None,
            test_expr,
        )

        self.assertCodegenTree(
            test_stmt,
            [
                ('ExpressionStmt', (), [
                    ('DummyExprLvalue', ('target',), [
                        ('DummyExprRuntime', ('value', DummyType), []),
                    ]),
                ]),
            ],
        )
