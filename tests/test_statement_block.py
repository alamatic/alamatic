
from alamatic.ast import *
from alamatic.types import *
from alamatic.testutil import *


class TestStatementBlock(LanguageTestCase):

    def test_execute(self):
        from alamatic.interpreter import (
            SymbolTable,
            Symbol,
            UnknownSymbolError,
        )

        stmts = [
            DummyStmtCompileTime(10),
            DummyStmtRuntime(11),
            DummyStmtCompileTime(12),
            DummyDataDeclStmt("a", 1),
            DummyStmtCompileTime(13),
            DummyStmtRuntime(14),
            DummyStmtCompileTime(15),
        ]
        block = StatementBlock(stmts)
        with interpreter_context() as context:
            root_symbols = context.symbols
            runtime_block = block.execute()

        got = ast_comparison_node(runtime_block)
        self.assertEqual(
            ast_comparison_node(runtime_block),
            ('StatementBlock', (), [
                ('DummyStmtRuntime', (11,), []),
                ('DummyStmtRuntime', (14,), []),
            ])
        )

        self.assertTrue(
            all(s.executed for s in stmts),
            "Not all statements were executed",
        )

        # Test that the new block has a scope and that it's populated
        # with the symbol that DeclStmt creates.
        self.assertEqual(
            type(runtime_block.symbols),
            SymbolTable,
        )
        # Parent symbol table should be our symbol table.
        self.assertEqual(
            runtime_block.symbols.parent,
            root_symbols,
        )
        symbol = runtime_block.symbols.get_symbol("a")
        self.assertEqual(
            type(symbol),
            Symbol,
        )
        self.assertEqual(
            symbol.get_value(),
            1,
        )
        # The new symbol should not be in our root symbol table, though
        self.assertRaises(
            UnknownSymbolError,
            lambda: root_symbols.get_symbol("a"),
        )

    def test_codegen(self):
        from alamatic.interpreter import SymbolTable, Registry
        self.assertCCode(
            StatementBlock(
                [
                    DummyStmtRuntime(11),
                    DummyStmtRuntime(12),
                ],
                symbols=SymbolTable(),
            ),
            "{\n"
            "  // DUMMY 11\n"
            "  // DUMMY 12\n"
            "}\n"
        )

        symbols = SymbolTable()
        with Registry():
            sym_a = symbols.create_symbol("a")
            sym_b = symbols.create_symbol("b")
            sym_c = symbols.create_symbol("c")
            sym_a.initialize(DummyType)
            sym_b.initialize(DummyType)
            # Tell the codegen that stor_a and stor_b were used,
            # but skip stor_c to emulate what happens when a symbol
            # is only used at compile time.
            sym_a.mark_used_at_runtime(position=('', 0, 0))
            sym_b.mark_used_at_runtime(position=('', 0, 0))

        self.assertCCode(
            StatementBlock(
                [
                    DummyStmtRuntime(11),
                    DummyStmtRuntime(12),
                ],
                symbols=symbols,
            ),
            "{\n"
            "  DummyType %s;\n"
            "  DummyType %s;\n"
            "  // DUMMY 11\n"
            "  // DUMMY 12\n"
            "}\n" % (sym_a.codegen_name, sym_b.codegen_name)
        )

        # TODO: also test individually generating the decls
        # and the body. And generating union types for variables
        # whose type varies during the program.
