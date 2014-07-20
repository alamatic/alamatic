
from alamatic.ast import *
from alamatic.intermediate import *
from alamatic.testutil import *
from mock import MagicMock


class TestParse(LanguageTestCase):

    def test_var_no_expr(self):
        self.assertStmtParseTree(
            'var i',
            [
                ('DataDeclStmt', (), [
                    ('VarDeclClause', ('i',), []),
                ]),
            ]
        )

    def test_var_expr(self):
        self.assertStmtParseTree(
            'var i = 1',
            [
                ('DataDeclStmt', (), [
                    ('VarDeclClause', ('i',), []),
                    ('LiteralExpr', (1,), []),
                ]),
            ]
        )

    def test_const_no_expr(self):
        self.assertStmtParseTree(
            'const i',
            [
                ('DataDeclStmt', (), [
                    ('ConstDeclClause', ('i',), []),
                ]),
            ]
        )

    def test_const_expr(self):
        self.assertStmtParseTree(
            'const i = 1',
            [
                ('DataDeclStmt', (), [
                    ('ConstDeclClause', ('i',), []),
                    ('LiteralExpr', (1,), []),
                ]),
            ]
        )

    def test_missing_equals(self):
        self.assertErrorsInStmts(
            "var i 1",
            [
                (1, 6),
            ]
        )

    def test_number_as_name(self):
        self.assertErrorsInStmts(
            "var 1",
            [
                (1, 4),
            ]
        )

    def test_extra_expression(self):
        self.assertErrorsInStmts(
            "var i = 1 2",
            [
                (1, 10),
            ]
        )


class TestIntermediate(LanguageTestCase):

    def test_var_no_expr(self):
        decl = VarDeclClause(None, "foo")
        symbols = SymbolTable()
        self.assertIntermediateForm(
            DataDeclStmt(
                ('datadecl.ala', 1, 0),
                decl,
                None,
            ),
            [],
            symbols=symbols,
        )
        symbol = symbols.lookup("foo")
        self.assertFalse(
            symbol.const,
        )
        self.assertEqual(
            symbol.decl_source_range,
            ('datadecl.ala', 1, 0),
        )

    def test_const_no_expr(self):
        decl = ConstDeclClause(None, "foo")
        stmt = DataDeclStmt(
            None,
            decl,
            None,
        )
        elems = []
        symbols = SymbolTable()
        self.assertRaises(
            NotConstantError,
            lambda: stmt.make_intermediate_form(elems, symbols),
        )

    def test_var_expr(self):
        decl = VarDeclClause(None, "foo")
        symbols = SymbolTable()
        self.assertIntermediateForm(
            DataDeclStmt(
                ('datadecl.ala', 1, 0),
                decl,
                DummyExpr("init"),
            ),
            [
                ('DummyInstruction', ['init']),
                ('OperationInstruction', [
                    ('SymbolOperand', [
                        ('NamedSymbol', 'foo'),
                    ]),
                    ('CopyOperation', [
                        ('DummyOperand', ['init']),
                    ]),
                ]),
            ],
            symbols=symbols,
        )
        symbol = symbols.lookup("foo")
        self.assertFalse(
            symbol.const,
        )
        self.assertEqual(
            symbol.decl_source_range,
            ('datadecl.ala', 1, 0),
        )

    def test_const_expr(self):
        decl = ConstDeclClause(None, "foo")
        symbols = SymbolTable()
        self.assertIntermediateForm(
            DataDeclStmt(
                ('datadecl.ala', 1, 0),
                decl,
                DummyExpr("init"),
            ),
            [
                ('DummyInstruction', ['init']),
                ('OperationInstruction', [
                    ('SymbolOperand', [
                        ('NamedSymbol', 'foo'),
                    ]),
                    ('CopyOperation', [
                        ('DummyOperand', ['init']),
                    ]),
                ]),
            ],
            symbols=symbols,
        )
        symbol = symbols.lookup("foo")
        self.assertTrue(
            symbol.const,
        )
        self.assertEqual(
            symbol.decl_source_range,
            ('datadecl.ala', 1, 0),
        )

    def test_self_initialize(self):
        # This test ensures that we correctly delay the declaration of
        # the symbol until *after* we've evaluated its initializer, so that
        # it's not possible to write var foo = foo where there isn't an
        # existing foo already declared.
        decl = DataDeclClause(None, "foo")
        stmt = DataDeclStmt(
            None,
            decl,
            SymbolNameExpr(None, "foo"),
        )
        elems = []
        symbols = SymbolTable()
        self.assertRaises(
            UnknownSymbolError,
            lambda: stmt.make_intermediate_form(elems, symbols),
        )
