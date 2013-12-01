
from alamatic.ast import *
from alamatic.intermediate import *
from alamatic.types import *
from alamatic.testutil import *


class TestIntermediate(LanguageTestCase):

    def test_base(self):
        class DummyBinaryOpExpr(BinaryOpExpr):
            def __init__(self):
                super(DummyBinaryOpExpr, self).__init__(
                    None,
                    DummyExpr("lhs"),
                    '?',
                    DummyExpr("rhs"),
                )

            @property
            def operator_name(self):
                return 'frobnicate'

        expr = DummyBinaryOpExpr()

        self.assertIntermediateForm(
            expr,
            [
                ('DummyOperation', ['lhs']),
                ('DummyOperation', ['rhs']),
                ('BinaryOperation', [
                    ('SymbolOperand', [
                        ('TemporarySymbol', 1),
                    ]),
                    ('DummyOperand', ['lhs']),
                    'frobnicate',
                    ('DummyOperand', ['rhs']),
                ]),
            ],
            ('SymbolOperand', [
                ('TemporarySymbol', 1),
            ]),
        )
