
from alamatic.ast import *
from alamatic.intermediate import *
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


class TestIntermediate(LanguageTestCase):

    def test_can_be_statement(self):
        self.assertTrue(
            AssignExpr.can_be_statement,
            True,
        )

    def test_plain_assign(self):
        expr = AssignExpr(
            ("assign.ala", 1, 0),
            DummyExprLvalue("lhs"),
            "=",
            DummyExpr("rhs"),
        )
        self.assertIntermediateForm(
            expr,
            [
                ('DummyOperation', ['lhs']),
                ('DummyOperation', ['rhs']),
                ('CopyOperation', [
                    ('DummyOperand', ['lhs']),
                    ('DummyOperand', ['rhs']),
                ]),
            ],
            ('DummyOperand', ['rhs']),
        )

    def test_non_lvalue(self):
        elems = []
        symbols = SymbolTable()
        expr = AssignExpr(
            ("assign.ala", 1, 0),
            DummyExpr("lhs"),
            "=",
            DummyExpr("rhs"),
        )
        self.assertRaises(
            InvalidLValueError,
            lambda: expr.make_intermediate_form(elems, symbols),
        )
