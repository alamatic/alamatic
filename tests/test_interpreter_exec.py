
import unittest
from alamatic.ast import *
from alamatic.types import *
from alamatic.testutil import *


class TestInterpreterExec(unittest.TestCase):

    assertCodegenTree = testcase_assertCodegenTree
    assertDataResult = testcase_assertDataResult

    def test_make_runtime_program(self):
        from alamatic.interpreter import (
            make_runtime_program,
            Registry,
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
                state_stuff["registry"] = interpreter.registry
                return dummy_block

        module = Module((1, 0, "test.ala"), "test", MockBlock())

        state = CompileState()
        runtime_program = make_runtime_program(state, module)
        self.assertEqual(
            runtime_program.entry_point_function.runtime_block,
            dummy_block,
        )
        self.assertEqual(
            type(state_stuff["symbols"]),
            SymbolTable,
        )
        self.assertEqual(
            type(state_stuff["registry"]),
            Registry,
        )

    def test_decl_stmt(self):
        from alamatic.interpreter import (
            Symbol,
            NotConstantError,
            SymbolValueNotKnownError,
        )

        class ConstantExpr(Expression):

            def __init__(self):
                pass

            def evaluate(self):
                return ValueExpr(None, UInt8(1))

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

        def make_decl(decl_type, name, expr):
            decl = decl_type(
                None,
                name,
            )
            decl_stmt = DataDeclStmt(
                ('test', 1, 0),
                decl,
                expr,
            )
            return decl_stmt

        def try_decl(decl_type, name, expr):
            decl_stmt = make_decl(decl_type, name, expr)
            runtime_stmts = []
            ret = Result()
            with interpreter_context() as context:
                ret.registry = context.registry
                ret.symbols = context.symbols
                decl_stmt.execute(runtime_stmts)
            ret.runtime_stmts = runtime_stmts
            return ret

        # Var declaration with no value: populates the symbol table but leaves
        # the symbol uninitialized.
        def try_var_decl_with_no_value():
            with interpreter_context() as context:
                decl_stmt = make_decl(VarDeclClause, "baz", None)
                runtime_stmts = []
                result = Result()
                result.registry = context.registry
                result.symbols = context.symbols
                decl_stmt.execute(runtime_stmts)
                result.runtime_stmts = runtime_stmts

                self.assertEqual(
                    len(result.runtime_stmts),
                    0,
                )
                symbol = result.symbols.get_symbol("baz")
                self.assertFalse(
                    symbol.const,
                    "Symbol is const but expected var",
                )
                self.assertFalse(
                    symbol.is_definitely_initialized,
                    "Symbol is initialized but it shouldn't be"
                )
                self.assertEqual(
                    symbol.decl_name,
                    'baz',
                )
                self.assertEqual(
                    symbol.decl_position,
                    ('test', 1, 0),
                )
        # The function should raise because it's illegal to exit a
        # symbol table without initializing all of its symbols.
        self.assertRaises(
            SymbolNotInitializedError,
            try_var_decl_with_no_value,
        )

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
        self.assertEqual(
            symbol.decl_name,
            'baz',
        )
        # These two are testing internal state rather than public interface,
        # since we don't directly expose these things at this point. Instead,
        # these positions are used when formulating error messages.
        self.assertEqual(
            symbol.init_position,
            ('test', 1, 0),
        )
        self.assertEqual(
            symbol.assign_position,
            ('test', 1, 0),
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
        self.assertRaises(
            SymbolValueNotKnownError,
            lambda: symbol.get_value(),
        )
        self.assertEqual(
            symbol.get_type(),
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
            symbol.get_value().value,
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
