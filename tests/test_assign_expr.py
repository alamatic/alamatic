
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
