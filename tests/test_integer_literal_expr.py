
from alamatic.ast import *
from alamatic.intermediate import *
from alamatic.types import *
from alamatic.testutil import *


class TestIntermediate(LanguageTestCase):

    def test_can_be_statement(self):
        self.assertFalse(
            IntegerLiteralExpr.can_be_statement,
        )

    def test_int8(self):
        expr = IntegerLiteralExpr(
            ("int8.ala", 1, 0),
            1,
        )
        self.assertIntermediateForm(
            expr,
            [
                ('CopyOperation', [
                    ('SymbolOperand', [
                        ('TemporarySymbol', 1),
                    ]),
                    ('ConstantOperand', [
                        Int8(1),
                    ]),
                ]),
            ],
            ('SymbolOperand', [
                ('TemporarySymbol', 1),
            ]),
        )
        expr = IntegerLiteralExpr(
            ("int8.ala", 1, 0),
            -1,
        )
        self.assertIntermediateForm(
            expr,
            [
                ('CopyOperation', [
                    ('SymbolOperand', [
                        ('TemporarySymbol', 1),
                    ]),
                    ('ConstantOperand', [
                        Int8(-1),
                    ]),
                ]),
            ],
            ('SymbolOperand', [
                ('TemporarySymbol', 1),
            ]),
        )

    def test_int16(self):
        expr = IntegerLiteralExpr(
            ("int16.ala", 1, 0),
            257,
        )
        self.assertIntermediateForm(
            expr,
            [
                ('CopyOperation', [
                    ('SymbolOperand', [
                        ('TemporarySymbol', 1),
                    ]),
                    ('ConstantOperand', [
                        Int16(257),
                    ]),
                ]),
            ],
            ('SymbolOperand', [
                ('TemporarySymbol', 1),
            ]),
        )

    def test_int32(self):
        expr = IntegerLiteralExpr(
            ("int32.ala", 1, 0),
            65537,
        )
        self.assertIntermediateForm(
            expr,
            [
                ('CopyOperation', [
                    ('SymbolOperand', [
                        ('TemporarySymbol', 1),
                    ]),
                    ('ConstantOperand', [
                        Int32(65537),
                    ]),
                ]),
            ],
            ('SymbolOperand', [
                ('TemporarySymbol', 1),
            ]),
        )

    def test_int64(self):
        expr = IntegerLiteralExpr(
            ("int64.ala", 1, 0),
            4294967297,
        )
        self.assertIntermediateForm(
            expr,
            [
                ('CopyOperation', [
                    ('SymbolOperand', [
                        ('TemporarySymbol', 1),
                    ]),
                    ('ConstantOperand', [
                        Int64(4294967297),
                    ]),
                ]),
            ],
            ('SymbolOperand', [
                ('TemporarySymbol', 1),
            ]),
        )

    def test_uint64(self):
        expr = IntegerLiteralExpr(
            ("uint64.ala", 1, 0),
            (2 ** 64) - 5,
        )
        self.assertIntermediateForm(
            expr,
            [
                ('CopyOperation', [
                    ('SymbolOperand', [
                        ('TemporarySymbol', 1),
                    ]),
                    ('ConstantOperand', [
                        UInt64((2 ** 64) - 5),
                    ]),
                ]),
            ],
            ('SymbolOperand', [
                ('TemporarySymbol', 1),
            ]),
        )
