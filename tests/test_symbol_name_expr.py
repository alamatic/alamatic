
from alamatic.ast import *
from alamatic.intermediate import *
from alamatic.testutil import *


class TestIntermediate(LanguageTestCase):

    def test_can_be_statement(self):
        self.assertFalse(
            SymbolNameExpr.can_be_statement,
        )

    def test_rvalue(self):
        symbols = SymbolTable()
        symbols.declare("foo")
        self.assertIntermediateForm(
            SymbolNameExpr(
                ('symbolname.ala', 1, 0),
                'foo',
            ),
            [
                ('OperationInstruction', [
                    ('SymbolOperand', [
                        ('TemporarySymbol', 1),
                    ]),
                    ('CopyOperation', [
                        ('SymbolOperand', [
                            ('NamedSymbol', 'foo'),
                        ]),
                    ]),
                ]),
            ],
            ('SymbolOperand', [
                ('TemporarySymbol', 1),
            ]),
            symbols=symbols,
        )

    def test_nonexist(self):
        expr = SymbolNameExpr(
            ('symbolname.ala', 1, 0),
            'foo',
        )
        elems = []
        symbols = SymbolTable()
        self.assertRaises(
            UnknownSymbolError,
            lambda: expr.make_intermediate_form(elems, symbols),
        )
        self.assertRaises(
            UnknownSymbolError,
            lambda: expr.get_lvalue_operand(elems, symbols),
        )

    def test_lvalue(self):
        expr = SymbolNameExpr(
            ('symbolname.ala', 1, 0),
            'foo',
        )
        elems = []
        symbols = SymbolTable()
        symbols.declare('foo')
        operand = expr.get_lvalue_operand(elems, symbols)
        self.assertEqual(
            elems,
            [],
        )
        self.assertEqual(
            element_param_comparison_node(operand),
            ('SymbolOperand', [
                ('NamedSymbol', 'foo'),
            ]),
        )
