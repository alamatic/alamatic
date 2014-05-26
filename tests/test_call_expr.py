
from alamatic.ast import *
from alamatic.testutil import *
from mock import MagicMock


class TestParse(LanguageTestCase):

    def test_simple(self):
        self.assertExprParseTree(
            "a(1)",
            ('CallExpr', (), [
                ('SymbolNameExpr', ('a',), []),
                ('Arguments', (0,), [
                    ('LiteralExpr', (1,), []),
                ]),
            ])
        )
        self.assertExprParseTree(
            "a(1,2)",
            ('CallExpr', (), [
                ('SymbolNameExpr', ('a',), []),
                ('Arguments', (0, 1), [
                    ('LiteralExpr', (1,), []),
                    ('LiteralExpr', (2,), []),
                ]),
            ])
        )
        self.assertExprParseTree(
            "a(1,)",
            ('CallExpr', (), [
                ('SymbolNameExpr', ('a',), []),
                ('Arguments', (0,), [
                    ('LiteralExpr', (1,), []),
                ]),
            ])
        )
        self.assertExprParseTree(
            "a(1,2,3,)",
            ('CallExpr', (), [
                ('SymbolNameExpr', ('a',), []),
                ('Arguments', (0, 1, 2), [
                    ('LiteralExpr', (1,), []),
                    ('LiteralExpr', (2,), []),
                    ('LiteralExpr', (3,), []),
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
                        ('LiteralExpr', (1,), []),
                    ]),
                ]),
                ('Arguments', (0,), [
                    ('LiteralExpr', (2,), []),
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
                            ('LiteralExpr', (1,), []),
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
                    ('LiteralExpr', (1,), []),
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
                    ('LiteralExpr', (1,), []),
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
                        ('LiteralExpr', (1,), []),
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
                        ('LiteralExpr', (1,), []),
                    ]),
                ]),
                ('CallExpr', (), [
                    ('SymbolNameExpr', ('b',), []),
                    ('Arguments', (0,), [
                        ('LiteralExpr', (1,), []),
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
                    ('LiteralExpr', (1,), []),
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
                        ('LiteralExpr', (1,), []),
                    ]),
                ]),
                ('Arguments', (0,), [
                    ('LiteralExpr', (2,), []),
                ]),
            ])
        )


class TestIntermediate(LanguageTestCase):

    def test_no_args(self):
        self.assertIntermediateForm(
            CallExpr(
                None,
                DummyExpr("callee"),
                Arguments(
                    pos_exprs=[],
                    kw_exprs={},
                )
            ),
            [
                ('DummyInstruction', ['callee']),
                ('OperationInstruction', [
                    ('SymbolOperand', [
                        ('TemporarySymbol', 1),
                    ]),
                    ('CallOperation', [
                        ('DummyOperand', ['callee']),
                        [],
                        {},
                    ]),
                ]),
            ],
            ('SymbolOperand', [
                ('TemporarySymbol', 1),
            ]),
        )

    def test_pos_args(self):
        self.assertIntermediateForm(
            CallExpr(
                None,
                DummyExpr("callee"),
                Arguments(
                    pos_exprs=[
                        DummyExpr("arg1"),
                        DummyExpr("arg2"),
                        DummyExpr("arg3"),
                    ],
                    kw_exprs={},
                )
            ),
            [
                ('DummyInstruction', ['callee']),
                ('DummyInstruction', ['arg1']),
                ('DummyInstruction', ['arg2']),
                ('DummyInstruction', ['arg3']),
                ('OperationInstruction', [
                    ('SymbolOperand', [
                        ('TemporarySymbol', 1),
                    ]),
                    ('CallOperation', [
                        ('DummyOperand', ['callee']),
                        [
                            ('DummyOperand', ['arg1']),
                            ('DummyOperand', ['arg2']),
                            ('DummyOperand', ['arg3']),
                        ],
                        {},
                    ]),
                ]),
            ],
            ('SymbolOperand', [
                ('TemporarySymbol', 1),
            ]),
        )

    def test_keyword_args(self):
        self.assertIntermediateForm(
            CallExpr(
                None,
                DummyExpr("callee"),
                Arguments(
                    pos_exprs=[],
                    kw_exprs={
                        "kw1": DummyExpr("arg1"),
                        "kw2": DummyExpr("arg2"),
                        "kw3": DummyExpr("arg3"),
                    },
                )
            ),
            [
                ('DummyInstruction', ['callee']),
                ('DummyInstruction', ['arg1']),
                ('DummyInstruction', ['arg2']),
                ('DummyInstruction', ['arg3']),
                ('OperationInstruction', [
                    ('SymbolOperand', [
                        ('TemporarySymbol', 1),
                    ]),
                    ('CallOperation', [
                        ('DummyOperand', ['callee']),
                        [],
                        {
                            "kw1": ('DummyOperand', ['arg1']),
                            "kw2": ('DummyOperand', ['arg2']),
                            "kw3": ('DummyOperand', ['arg3']),
                        },
                    ]),
                ]),
            ],
            ('SymbolOperand', [
                ('TemporarySymbol', 1),
            ]),
        )
