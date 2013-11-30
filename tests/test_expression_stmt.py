
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
