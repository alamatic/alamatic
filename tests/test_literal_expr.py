
from alamatic.ast import *
from alamatic.intermediate import *
from alamatic.testutil import *


class TestIntermediate(LanguageTestCase):

    def test_can_be_statement(self):
        self.assertFalse(
            LiteralExpr.can_be_statement,
        )

    def test_intermediate_form(self):
        expr = LiteralExpr(
            ("int16.ala", 1, 0),
            'baz',
        )
        self.assertIntermediateForm(
            expr,
            [
                ('OperationInstruction', [
                    ('SymbolOperand', [
                        ('TemporarySymbol', 1),
                    ]),
                    ('CopyOperation', [
                        ('ConstantOperand', [
                            'baz',
                        ]),
                    ]),
                ]),
            ],
            ('SymbolOperand', [
                ('TemporarySymbol', 1),
            ]),
        )
