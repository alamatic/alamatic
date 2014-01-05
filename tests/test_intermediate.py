
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
            OperationInstruction(
                SymbolOperand(temp_symbol),
                CopyOperation(
                    ConstantOperand(UInt8(1)),
                ),
            ),
            OperationInstruction(
                SymbolOperand(named_symbol),
                CopyOperation(
                    ConstantOperand(UInt8(2)),
                ),
            ),
            OperationInstruction(
                SymbolOperand(named_symbol),
                BinaryOperation(
                    SymbolOperand(temp_symbol),
                    'add',
                    SymbolOperand(temp_symbol),
                ),
            ),
            OperationInstruction(
                SymbolOperand(named_symbol),
                BinaryOperation(
                    SymbolOperand(named_symbol),
                    'subtract',
                    SymbolOperand(named_symbol),
                ),
            ),
        ]
        simpler_elems = simplify_temporaries_in_element_list(elems)
        self.assertEqual(
            element_comparison_nodes(simpler_elems),
            [
                ('OperationInstruction', [
                    ('SymbolOperand', [
                        ('NamedSymbol', 'baz'),
                    ]),
                    ('CopyOperation', [
                        ('ConstantOperand', [
                            ('UInt8', (2,)),
                        ]),
                    ]),
                ]),
                # The copy to the temporary is removed.
                ('OperationInstruction', [
                    ('SymbolOperand', [
                        ('NamedSymbol', 'baz')
                    ]),
                    ('BinaryOperation', [
                        # the operands are now the constant
                        ('ConstantOperand', [
                            ('UInt8', (1,)),
                        ]),
                        'add',
                        ('ConstantOperand', [
                            ('UInt8', (1,)),
                        ]),
                    ]),
                ]),
                # The other operation is unaffected
                ('OperationInstruction', [
                    ('SymbolOperand', [
                        ('NamedSymbol', 'baz')
                    ]),
                    ('BinaryOperation', [
                        ('SymbolOperand', [
                            ('NamedSymbol', 'baz')
                        ]),
                        'subtract',
                        ('SymbolOperand', [
                            ('NamedSymbol', 'baz')
                        ]),
                    ]),
                ]),
            ],
        )
