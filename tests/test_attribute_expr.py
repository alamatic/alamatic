
from alamatic.ast import *
from alamatic.types import *
from alamatic.testutil import *


class TestParse(LanguageTestCase):

    def test_simple(self):
        self.assertExprParseTree(
            "a.b",
            ('AttributeExpr', ('b',), [
                ('SymbolNameExpr', ('a',), []),
            ])
        )

    def test_chained(self):
        self.assertExprParseTree(
            "a.b.c",
            ('AttributeExpr', ('c',), [
                ('AttributeExpr', ('b',), [
                    ('SymbolNameExpr', ('a',), []),
                ]),
            ]),
        )
