
from alamatic.ast import *
from alamatic.types import *
from alamatic.testutil import *
from mock import MagicMock


class TestParse(LanguageTestCase):

    def test_simple(self):
        self.assertExprParseTree(
            "a(1)",
            ('CallExpr', (), [
                ('SymbolNameExpr', ('a',), []),
                ('Arguments', (0,), [
                    ('IntegerLiteralExpr', (1,), []),
                ]),
            ])
        )
        self.assertExprParseTree(
            "a(1,2)",
            ('CallExpr', (), [
                ('SymbolNameExpr', ('a',), []),
                ('Arguments', (0, 1), [
                    ('IntegerLiteralExpr', (1,), []),
                    ('IntegerLiteralExpr', (2,), []),
                ]),
            ])
        )
        self.assertExprParseTree(
            "a(1,)",
            ('CallExpr', (), [
                ('SymbolNameExpr', ('a',), []),
                ('Arguments', (0,), [
                    ('IntegerLiteralExpr', (1,), []),
                ]),
            ])
        )
        self.assertExprParseTree(
            "a(1,2,3,)",
            ('CallExpr', (), [
                ('SymbolNameExpr', ('a',), []),
                ('Arguments', (0, 1, 2), [
                    ('IntegerLiteralExpr', (1,), []),
                    ('IntegerLiteralExpr', (2,), []),
                    ('IntegerLiteralExpr', (3,), []),
                ]),
            ])
        )

    def test_chained(self):
        self.assertExprParseTree(
            "a(1)(2)",
            ('CallExpr', (), [
                ('CallExpr', (), [
                    ('SymbolNameExpr', ('a',), []),
                    ('Arguments', (0,), [
                        ('IntegerLiteralExpr', (1,), []),
                    ]),
                ]),
                ('Arguments', (0,), [
                    ('IntegerLiteralExpr', (2,), []),
                ]),
            ])
        )

    def test_nested(self):
        self.assertExprParseTree(
            "a(b(1))",
            ('CallExpr', (), [
                ('SymbolNameExpr', ('a',), []),
                ('Arguments', (0,), [
                    ('CallExpr', (), [
                        ('SymbolNameExpr', ('b',), []),
                        ('Arguments', (0,), [
                            ('IntegerLiteralExpr', (1,), []),
                        ]),
                    ]),
                ]),
            ])
        )

    def test_complex_callee(self):
        self.assertExprParseTree(
            "(a)(1)",
            ('CallExpr', (), [
                ('SymbolNameExpr', ('a',), []),
                ('Arguments', (0,), [
                    ('IntegerLiteralExpr', (1,), []),
                ]),
            ])
        )
        self.assertExprParseTree(
            "(a+b)(1)",
            ('CallExpr', (), [
                ('SumExpr', ('+',), [
                    ('SymbolNameExpr', ('a',), []),
                    ('SymbolNameExpr', ('b',), []),
                ]),
                ('Arguments', (0,), [
                    ('IntegerLiteralExpr', (1,), []),
                ]),
            ])
        )
        self.assertExprParseTree(
            "a+b(1)",
            ('SumExpr', ('+',), [
                ('SymbolNameExpr', ('a',), []),
                ('CallExpr', (), [
                    ('SymbolNameExpr', ('b',), []),
                    ('Arguments', (0,), [
                        ('IntegerLiteralExpr', (1,), []),
                    ]),
                ]),
            ])
        )

    def test_embedded(self):
        self.assertExprParseTree(
            "a(1) + b(1)",
            ('SumExpr', ('+',), [
                ('CallExpr', (), [
                    ('SymbolNameExpr', ('a',), []),
                    ('Arguments', (0,), [
                        ('IntegerLiteralExpr', (1,), []),
                    ]),
                ]),
                ('CallExpr', (), [
                    ('SymbolNameExpr', ('b',), []),
                    ('Arguments', (0,), [
                        ('IntegerLiteralExpr', (1,), []),
                    ]),
                ]),
            ]),
        )

    def test_call_attribute(self):
        self.assertExprParseTree(
            "a.b(1)",
            ('CallExpr', (), [
                ('AttributeExpr', ('b',), [
                    ('SymbolNameExpr', ('a',), []),
                ]),
                ('Arguments', (0,), [
                    ('IntegerLiteralExpr', (1,), []),
                ]),
            ])
        )

    def test_call_subscript(self):
        self.assertExprParseTree(
            "a[1](2)",
            ('CallExpr', (), [
                ('SubscriptExpr', (), [
                    ('SymbolNameExpr', ('a',), []),
                    ('ExpressionList', (), [
                        ('IntegerLiteralExpr', (1,), []),
                    ]),
                ]),
                ('Arguments', (0,), [
                    ('IntegerLiteralExpr', (2,), []),
                ]),
            ])
        )
