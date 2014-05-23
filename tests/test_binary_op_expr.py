
from alamatic.ast import *
from alamatic.intermediate import *
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
                ('DummyInstruction', ['lhs']),
                ('DummyInstruction', ['rhs']),
                ('OperationInstruction', [
                    ('SymbolOperand', [
                        ('TemporarySymbol', 1),
                    ]),
                    ('BinaryOperation', [
                        ('DummyOperand', ['lhs']),
                        'frobnicate',
                        ('DummyOperand', ['rhs']),
                    ]),
                ]),
            ],
            ('SymbolOperand', [
                ('TemporarySymbol', 1),
            ]),
        )
