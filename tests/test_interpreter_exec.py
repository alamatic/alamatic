
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
