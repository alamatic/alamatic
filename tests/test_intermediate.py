
from alamatic.ast import *
from alamatic.types import *
from alamatic.intermediate import *
from alamatic.testutil import *


class TestSimplifyTemporaries(LanguageTestCase):

    def test_simplify(self):
        symbols = SymbolTable()
        temp_symbol = symbols.create_temporary()
        named_symbol = symbols.declare("baz")
        elems = [
            CopyOperation(
                SymbolOperand(temp_symbol),
                ConstantOperand(UInt8(1)),
            ),
            CopyOperation(
                SymbolOperand(named_symbol),
                ConstantOperand(UInt8(2)),
            ),
            BinaryOperation(
                SymbolOperand(named_symbol),
                SymbolOperand(temp_symbol),
                'add',
                SymbolOperand(temp_symbol),
            ),
            BinaryOperation(
                SymbolOperand(named_symbol),
                SymbolOperand(named_symbol),
                'subtract',
                SymbolOperand(named_symbol),
            ),
        ]
        simpler_elems = simplify_temporaries_in_element_list(elems)
        self.assertEqual(
            element_comparison_nodes(simpler_elems),
            [
                ('CopyOperation', [
                    ('SymbolOperand', [
                        ('NamedSymbol', 'baz'),
                    ]),
                    ('ConstantOperand', [UInt8(2)]),
                ]),
                # The copy to the temporary is removed.
                ('BinaryOperation', [
                    ('SymbolOperand', [
                        ('NamedSymbol', 'baz')
                    ]),
                    # the operands are now the constant
                    ('ConstantOperand', [UInt8(1)]),
                    'add',
                    ('ConstantOperand', [UInt8(1)]),
                ]),
                # The other operation is unaffected
                ('BinaryOperation', [
                    ('SymbolOperand', [
                        ('NamedSymbol', 'baz')
                    ]),
                    ('SymbolOperand', [
                        ('NamedSymbol', 'baz')
                    ]),
                    'subtract',
                    ('SymbolOperand', [
                        ('NamedSymbol', 'baz')
                    ]),
                ]),
            ],
        )
