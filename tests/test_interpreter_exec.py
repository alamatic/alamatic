
import unittest
from alamatic.ast import *
from alamatic.types import *


class TestInterpreterExec(unittest.TestCase):

    def test_execute_module(self):
        from alamatic.interpreter import (
            execute_module,
            DataState,
            SymbolTable,
        )
        from alamatic.compiler import CompileState

        dummy_block = StatementBlock([])
        state_stuff = {}
        class MockBlock(object):
            def execute(self):
                from alamatic.interpreter import interpreter
                # Grab these so we can verify that execute_module
                # did indeed create a symbol table and a data state.
                state_stuff["symbols"] = interpreter.symbols
                state_stuff["data"] = interpreter.data
                return dummy_block

        module = Module((1, 0, "test.ala"), "test", MockBlock())

        state = CompileState()
        runtime_module = execute_module(state, module)
        self.assertEqual(
            runtime_module.block,
            dummy_block,
        )
        self.assertEqual(
            type(state_stuff["symbols"]),
            SymbolTable,
        )
        self.assertEqual(
            type(state_stuff["data"]),
            DataState,
        )

    def test_statement_block(self):
        from alamatic.interpreter import (
            DataState,
            SymbolTable,
            Symbol,
        )

        class CompileTimeStmt(Statement):
            def __init__(self):
                pass
            def execute(self, runtime_stmts):
                return
        class RuntimeStmt(Statement):
            def __init__(self, source_stmt=None):
                self.source_stmt = source_stmt
            def execute(self, runtime_stmts):
                runtime_stmts.append(RuntimeStmt(self))
        class DeclStmt(Statement):
            def __init__(self):
                pass
            def execute(self, runtime_stmts):
                from alamatic.interpreter import interpreter
                interpreter.declare("a", 1)

        stmts = [
            CompileTimeStmt(),
            RuntimeStmt(),
            CompileTimeStmt(),
            DeclStmt(),
            CompileTimeStmt(),
            RuntimeStmt(),
            CompileTimeStmt(),
        ]
        block = StatementBlock(stmts)
        data = DataState()
        symbols = SymbolTable()
        with data:
            with symbols:
                runtime_block = block.execute()

        # Test that the RuntimeStmt instances were executed and handled
        # in the correct order.
        self.assertEqual(
            [
                type(x) for x in runtime_block.stmts
            ],
            [
                RuntimeStmt,
                RuntimeStmt,
            ]
        )
        self.assertEqual(
            [
                x.source_stmt for x in runtime_block.stmts
            ],
            [
                stmts[1],
                stmts[5],
            ]
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
            symbols,
        )
        symbol = runtime_block.symbols.get_symbol("a")
        self.assertEqual(
            type(symbol),
            Symbol,
        )
        self.assertEqual(
            data.get_symbol_value(symbol),
            1,
        )
        # The new symbol should not be in our root symbol table, though
        self.assertRaises(
            KeyError,
            lambda: symbols.get_symbol("a"),
        )

    def test_expression_stmt(self):
        class Dummy1Expr(Expression):
            evaluated = False
            def evaluate(self):
                Dummy1Expr.evaluated = True
                return ValueExpr(self, UInt8(1))
        class Dummy2Expr(Expression):
            evaluated = False
            def evaluate(self):
                Dummy2Expr.evaluated = True
                return Dummy2Expr(self.position)
            @property
            def result_type(self):
                return UInt8

        stmt = ExpressionStmt(None, Dummy1Expr(None))
        runtime_stmts = []
        stmt.execute(runtime_stmts)
        self.assertEqual(
            runtime_stmts,
            [],
        )
        self.assertTrue(
            Dummy1Expr.evaluated,
            "Didn't evaluate Dummy1Expr",
        )

        stmt = ExpressionStmt(None, Dummy2Expr(None))
        runtime_stmts = []
        stmt.execute(runtime_stmts)
        self.assertEqual(
            len(runtime_stmts),
            1,
        )
        self.assertEqual(
            type(runtime_stmts[0]),
            ExpressionStmt,
        )
        self.assertEqual(
            type(runtime_stmts[0].expr),
            Dummy2Expr,
        )
        self.assertTrue(
            Dummy2Expr.evaluated,
            "Didn't evaluate Dummy2Expr",
        )

