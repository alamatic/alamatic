
import unittest
from alamatic.ast import *
from alamatic.types import *
from alamatic.testutil import *


class TestInterpreterExec(unittest.TestCase):

    assertCodegenTree = testcase_assertCodegenTree
    assertDataResult = testcase_assertDataResult

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

    def test_decl_stmt(self):
        from alamatic.interpreter import (
            DataState,
            SymbolTable,
            Symbol,
            NotConstantError,
        )
        class ConstantExpr(Expression):
            def __init__(self):
                pass
            def evaluate(self):
                return ValueExpr(self, UInt8(1))
        class NotConstantExpr(Expression):
            def __init__(self):
                pass
            def evaluate(self):
                return NotConstantExpr()
            @property
            def result_type(self):
                return UInt8

        class Result(object):
            pass

        def try_decl(decl_type, name, expr):
            decl = decl_type(
                None,
                name,
            )
            decl_stmt = DataDeclStmt(
                None,
                decl,
                expr,
            )
            runtime_stmts = []
            data = DataState()
            symbols = SymbolTable()
            with data:
                with symbols:
                    decl_stmt.execute(runtime_stmts)
            ret = Result()
            ret.runtime_stmts = runtime_stmts
            ret.data = data
            ret.symbols = symbols
            return ret

        # Var declaration with a constant value: populates the symbol table,
        # assigns a value, and generates an assignment in runtime code.
        result = try_decl(VarDeclClause, "baz", ConstantExpr())
        self.assertEqual(
            len(result.runtime_stmts),
            1,
        )
        self.assertEqual(
            type(result.runtime_stmts[0]),
            ExpressionStmt,
        )
        self.assertEqual(
            type(result.runtime_stmts[0].expr),
            AssignExpr,
        )
        self.assertEqual(
            type(result.runtime_stmts[0].expr.lhs),
            SymbolExpr,
        )
        self.assertEqual(
            type(result.runtime_stmts[0].expr.rhs),
            ValueExpr,
        )
        self.assertEqual(
            result.runtime_stmts[0].expr.rhs.value.value,
            1,
        )
        symbol = result.symbols.get_symbol("baz")
        self.assertFalse(
            symbol.const,
            "Symbol is const but expected var",
        )
        self.assertEqual(
            result.runtime_stmts[0].expr.lhs.symbol,
            symbol,
        )

        # Var declaration with a non-constant value: populates the symbol
        # table, assigns a type, and generates a dynamic assignment at
        # runtime.
        result = try_decl(VarDeclClause, "fee", NotConstantExpr())
        self.assertEqual(
            len(result.runtime_stmts),
            1,
        )
        self.assertEqual(
            type(result.runtime_stmts[0]),
            ExpressionStmt,
        )
        self.assertEqual(
            type(result.runtime_stmts[0].expr),
            AssignExpr,
        )
        self.assertEqual(
            type(result.runtime_stmts[0].expr.lhs),
            SymbolExpr,
        )
        self.assertEqual(
            type(result.runtime_stmts[0].expr.rhs),
            NotConstantExpr,
        )
        symbol = result.symbols.get_symbol("fee")
        self.assertTrue(
            type(symbol) is Symbol
        )
        self.assertFalse(
            symbol.const,
            "Symbol is const but expected var",
        )
        self.assertEqual(
            type(result.data.get_symbol_value(symbol)),
            type(None),
        )
        self.assertEqual(
            symbol.type,
            UInt8,
        )
        self.assertEqual(
            result.runtime_stmts[0].expr.lhs.symbol,
            symbol,
        )

        # Constant declaration with a constant value: populates the symbol
        # table, assigns a value, but generates no assignment at runtime.
        result = try_decl(ConstDeclClause, "bez", ConstantExpr())
        self.assertEqual(
            len(result.runtime_stmts),
            0,
        )
        symbol = result.symbols.get_symbol("bez")
        self.assertTrue(
            type(symbol) is Symbol
        )
        self.assertTrue(
            symbol.const,
            "Symbol is var but expected const",
        )
        self.assertEqual(
            result.data.get_symbol_value(symbol).value,
            1,
        )

        # Constant declaration with a non-constant value: fails!
        self.assertRaises(
            NotConstantError,
            lambda: try_decl(ConstDeclClause, "boz", NotConstantExpr()),
        )

        # Constant declaration with no value: fails!
        self.assertRaises(
            NotConstantError,
            lambda: try_decl(ConstDeclClause, "biz", None),
        )
