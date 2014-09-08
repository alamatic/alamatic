
from alamatic.ast import *
from alamatic.intermediate import *
from alamatic.testutil import *
from mock import MagicMock


class TestParse(LanguageTestCase):

    def test_simple_parse(self):
        self.assertStmtParseTree(
            'func doot(a, b when foo):\n'
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

    def test_named_params(self):
        self.assertStmtParseTree(
            'func doot(a, named b):\n'
            '    pass',
            [
                ('FuncDeclStmt', (), [
                    ('FuncDeclClause', ('doot',), [
                        ('ParamDeclClause', ('a',), []),
                        ('ParamDeclClause', ('b', 'named'), []),
                    ]),
                    ('StatementBlock', (), [
                        ('PassStmt', (), []),
                    ]),
                ]),
            ]
        )

    def test_const_params(self):
        self.assertStmtParseTree(
            'func doot(a, const b):\n'
            '    pass',
            [
                ('FuncDeclStmt', (), [
                    ('FuncDeclClause', ('doot',), [
                        ('ParamDeclClause', ('a',), []),
                        ('ParamDeclClause', ('b', 'const'), []),
                    ]),
                    ('StatementBlock', (), [
                        ('PassStmt', (), []),
                    ]),
                ]),
            ]
        )

    def test_collector_params(self):
        self.assertStmtParseTree(
            'func doot(a..., named b...):\n'
            '    pass',
            [
                ('FuncDeclStmt', (), [
                    ('FuncDeclClause', ('doot',), [
                        ('ParamDeclClause', ('a', '...'), []),
                        ('ParamDeclClause', ('b', 'named', '...'), []),
                    ]),
                    ('StatementBlock', (), [
                        ('PassStmt', (), []),
                    ]),
                ]),
            ]
        )

    def test_combination_1(self):
        self.assertStmtParseTree(
            'func doot(a, const named b, named c=2, named d when baz):\n'
            '    pass',
            [
                ('FuncDeclStmt', (), [
                    ('FuncDeclClause', ('doot',), [
                        ('ParamDeclClause', ('a',), []),
                        ('ParamDeclClause', ('b', 'const', 'named'), []),
                        ('ParamDeclClause', ('c', 'named', 'optional'), [
                            ('LiteralExpr', (2,), []),
                        ]),
                        ('ParamDeclClause', ('d', 'named'), [
                            ('SymbolNameExpr', ('baz',), []),
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
            elems_comp,
            [
                ('OperationInstruction', [
                    ('SymbolOperand', [
                        ('NamedSymbol', 'baz'),
                    ]),
                    ('CopyOperation', [
                        ('ConstantOperand', [
                            ('FunctionTemplate', 'baz'),
                        ]),
                    ]),
                ]),
            ]
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
            symbol.decl_source_range,
            ('funcdecl.ala', 1, 0),
        )
