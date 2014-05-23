
from alamatic.ast import *
from alamatic.testutil import *


class TestParse(LanguageTestCase):

    def test_simple(self):
        self.assertExprParseTree(
            "a[1]",
            ('SubscriptExpr', (), [
                ('SymbolNameExpr', ('a',), []),
                ('ExpressionList', (), [
                    ('IntegerLiteralExpr', (1,), []),
                ]),
            ])
        )
        self.assertExprParseTree(
            "a[1,2]",
            ('SubscriptExpr', (), [
                ('SymbolNameExpr', ('a',), []),
                ('ExpressionList', (), [
                    ('IntegerLiteralExpr', (1,), []),
                    ('IntegerLiteralExpr', (2,), []),
                ]),
            ])
        )
        self.assertExprParseTree(
            "a[1,]",
            ('SubscriptExpr', (), [
                ('SymbolNameExpr', ('a',), []),
                ('ExpressionList', (), [
                    ('IntegerLiteralExpr', (1,), []),
                ]),
            ])
        )
        self.assertExprParseTree(
            "a[1,2,3,]",
            ('SubscriptExpr', (), [
                ('SymbolNameExpr', ('a',), []),
                ('ExpressionList', (), [
                    ('IntegerLiteralExpr', (1,), []),
                    ('IntegerLiteralExpr', (2,), []),
                    ('IntegerLiteralExpr', (3,), []),
                ]),
            ])
        )

    def test_chained(self):
        self.assertExprParseTree(
            "a[1][2]",
            ('SubscriptExpr', (), [
                ('SubscriptExpr', (), [
                    ('SymbolNameExpr', ('a',), []),
                    ('ExpressionList', (), [
                        ('IntegerLiteralExpr', (1,), []),
                    ]),
                ]),
                ('ExpressionList', (), [
                    ('IntegerLiteralExpr', (2,), []),
                ]),
            ])
        )

    def test_nested(self):
        self.assertExprParseTree(
            "a[b[1]]",
            ('SubscriptExpr', (), [
                ('SymbolNameExpr', ('a',), []),
                ('ExpressionList', (), [
                    ('SubscriptExpr', (), [
                        ('SymbolNameExpr', ('b',), []),
                        ('ExpressionList', (), [
                            ('IntegerLiteralExpr', (1,), []),
                        ]),
                    ]),
                ]),
            ])
        )

    def test_complex_expr(self):
        self.assertExprParseTree(
            "(a)[1]",
            ('SubscriptExpr', (), [
                ('SymbolNameExpr', ('a',), []),
                ('ExpressionList', (), [
                    ('IntegerLiteralExpr', (1,), []),
                ]),
            ])
        )
        self.assertExprParseTree(
            "(a+b)[1]",
            ('SubscriptExpr', (), [
                ('SumExpr', ('+',), [
                    ('SymbolNameExpr', ('a',), []),
                    ('SymbolNameExpr', ('b',), []),
                ]),
                ('ExpressionList', (), [
                    ('IntegerLiteralExpr', (1,), []),
                ]),
            ])
        )
        self.assertExprParseTree(
            "a+b[1]",
            ('SumExpr', ('+',), [
                ('SymbolNameExpr', ('a',), []),
                ('SubscriptExpr', (), [
                    ('SymbolNameExpr', ('b',), []),
                    ('ExpressionList', (), [
                        ('IntegerLiteralExpr', (1,), []),
                    ]),
                ]),
            ])
        )

    def test_embedded(self):
        self.assertExprParseTree(
            "a[1] + b[1]",
            ('SumExpr', ('+',), [
                ('SubscriptExpr', (), [
                    ('SymbolNameExpr', ('a',), []),
                    ('ExpressionList', (), [
                        ('IntegerLiteralExpr', (1,), []),
                    ]),
                ]),
                ('SubscriptExpr', (), [
                    ('SymbolNameExpr', ('b',), []),
                    ('ExpressionList', (), [
                        ('IntegerLiteralExpr', (1,), []),
                    ]),
                ]),
            ]),
        )

    def test_index_attribute(self):
        self.assertExprParseTree(
            "a.b[1]",
            ('SubscriptExpr', (), [
                ('AttributeExpr', ('b',), [
                    ('SymbolNameExpr', ('a',), []),
                ]),
                ('ExpressionList', (), [
                    ('IntegerLiteralExpr', (1,), []),
                ]),
            ])
        )
