
from alamatic.ast import *
from alamatic.types import *
from alamatic.intermediate import *
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


class TestIntermediate(LanguageTestCase):

    def test_can_be_statement(self):
        class DummyExprStatement(DummyExpr):
            can_be_statement = True

        self.assertIntermediateForm(
            ExpressionStmt(
                None,
                DummyExprStatement("expr"),
            ),
            [
                ('DummyInstruction', ['expr']),
            ],
        )

    def test_cannot_be_statement(self):
        stmt = ExpressionStmt(
            None,
            DummyExpr("expr"),
        )
        elems = []
        symbols = SymbolTable()
        self.assertRaises(
            CompilerError,
            lambda: stmt.make_intermediate_form(elems, symbols),
        )
