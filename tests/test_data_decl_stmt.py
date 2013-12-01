
from alamatic.ast import *
from alamatic.types import *
from alamatic.intermediate import *
from alamatic.testutil import *
from mock import MagicMock


class TestParse(LanguageTestCase):

    def test_var_no_expr(self):
        self.assertStmtParseTree(
            'var i',
            [
                ('DataDeclStmt', (), [
                    ('VarDeclClause', ('i',), []),
                ]),
            ]
        )

    def test_var_expr(self):
        self.assertStmtParseTree(
            'var i = 1',
            [
                ('DataDeclStmt', (), [
                    ('VarDeclClause', ('i',), []),
                    ('IntegerLiteralExpr', (1,), []),
                ]),
            ]
        )

    def test_const_no_expr(self):
        self.assertStmtParseTree(
            'const i',
            [
                ('DataDeclStmt', (), [
                    ('ConstDeclClause', ('i',), []),
                ]),
            ]
        )

    def test_const_expr(self):
        self.assertStmtParseTree(
            'const i = 1',
            [
                ('DataDeclStmt', (), [
                    ('ConstDeclClause', ('i',), []),
                    ('IntegerLiteralExpr', (1,), []),
                ]),
            ]
        )

    def test_missing_equals(self):
        self.assertErrorsInStmts(
            "var i 1",
            [
                (1, 6),
            ]
        )

    def test_number_as_name(self):
        self.assertErrorsInStmts(
            "var 1",
            [
                (1, 4),
            ]
        )

    def test_extra_expression(self):
        self.assertErrorsInStmts(
            "var i = 1 2",
            [
                (1, 10),
            ]
        )
