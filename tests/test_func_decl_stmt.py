
from alamatic.ast import *
from alamatic.types import *
from alamatic.intermediate import *
from alamatic.testutil import *
from mock import MagicMock


class TestParse(LanguageTestCase):

    def test_simple_parse(self):
        self.assertStmtParseTree(
            'func doot(a, b as foo):\n'
            '    pass',
            [
                ('FuncDeclStmt', (), [
                    ('FuncDeclClause', ('doot',), [
                        ('ParamDeclClause', ('a',), []),
                        ('ParamDeclClause', ('b',), [
                            ('SymbolNameExpr', ('foo',), []),
                        ]),
                    ]),
                    ('StatementBlock', (), [
                        ('PassStmt', (), []),
                    ]),
                ]),
            ]
        )


class TestIntermediate(LanguageTestCase):

    def test_intermediate(self):
        decl = MagicMock
        decl.name = 'baz'
        block = MagicMock
        stmt = FuncDeclStmt(
            ('funcdecl.ala', 1, 0),
            decl,
            block,
        )
        symbols = SymbolTable()
        elems = []
        stmt.make_intermediate_form(elems, symbols)

        self.assertEqual(
            len(elems),
            1,
        )
        elems_comp = element_comparison_nodes(elems)
        self.assertEqual(
            elems_comp[0][0],
            'CopyOperation',
        )
        self.assertEqual(
            elems_comp[0][1][0],
            ('SymbolOperand', [
                ('NamedSymbol', 'baz'),
            ])
        )
        self.assertEqual(
            elems_comp[0][1][1][0],
            'ConstantOperand',
        )
        self.assertEqual(
            elems_comp[0][1][1][1][0],
            ('FunctionTemplate', ()),
        )

        symbol = symbols.lookup("baz")
        self.assertEqual(
            type(symbol),
            NamedSymbol,
        )
        self.assertTrue(
            symbol.const,
        )
        self.assertEqual(
            symbol.decl_position,
            ('funcdecl.ala', 1, 0),
        )
