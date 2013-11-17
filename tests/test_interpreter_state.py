
import unittest
from alamatic.interpreter import (
    interpreter,
    SymbolTable,
    Registry,
    Symbol,
    CallFrame,
    UnknownSymbolError,
    IncompatibleTypesError,
    SymbolNotInitializedError,
    SymbolValueAmbiguousError,
    ReturnTypeAmbiguousError,
    ReturnValueNotKnownError,
    ReturnValueAmbiguousError
)
from alamatic.testutil import DummyType


class TestInterpreterState(unittest.TestCase):

    def test_symbol_table(self):
        with Registry() as root_registry:
            sym = Symbol(DummyType)
            root_table = SymbolTable()
            child_table = root_table.create_child()
            child_child_table = child_table.create_child()

            a_sym_1 = root_table.create_symbol("a", DummyType)
            a_sym_2 = child_child_table.create_symbol("a", DummyType)
            b_sym = child_table.create_symbol("b", DummyType)
            c_sym = root_table.create_symbol("c", DummyType)

            self.assertEqual(
                root_table.get_symbol("a"),
                child_table.get_symbol("a"),
            )
            self.assertEqual(
                child_table.get_symbol("a"),
                a_sym_1,
            )
            self.assertNotEqual(
                root_table.get_symbol("a"),
                child_child_table.get_symbol("a"),
            )
            self.assertEqual(
                child_child_table.get_symbol("a"),
                a_sym_2,
            )

            self.assertEqual(
                child_table.get_symbol("b"),
                b_sym,
            )
            self.assertEqual(
                child_child_table.get_symbol("b"),
                b_sym,
            )
            self.assertRaises(
                UnknownSymbolError,
                lambda: root_table.get_symbol("b")
            )

            self.assertEqual(
                root_table.get_symbol("c"),
                child_child_table.get_symbol("c"),
            )
            self.assertEqual(
                root_table.get_symbol("c"),
                child_table.get_symbol("c"),
            )
            self.assertEqual(
                root_table.get_symbol("c"),
                c_sym,
            )

    def test_registry(self):
        import datafork
        from mock import MagicMock

        mock_finalize = MagicMock('finalize')
        mock_merge = MagicMock('merge')

        with Registry() as root_registry:
            root_state = root_registry.data_state
            self.assertEqual(type(root_state), datafork.Root)

            root_state.finalize_data = mock_finalize
            root_state.merge_children = mock_merge

            child_registry = root_registry.create_child()
            with child_registry as returned_child_registry:
                child_state = child_registry.data_state
                self.assertEqual(child_registry, returned_child_registry)
                self.assertEqual(type(child_state), datafork.State)
                self.assertEqual(child_state.root, root_state)

            root_registry.merge_children([child_registry])

        mock_merge.assert_called_with(
            [child_registry.data_state],
            or_none=False,
        )
        mock_finalize.assert_called_with()

    def test_combination(self):
        # This test simulates a realistic combined use of symbol tables
        # and data states together, approximating the machinations of
        # the interpreter executing a program.

        root_registry = Registry()
        root_table = SymbolTable()

        with root_registry:
            with root_table:
                interpreter.declare_and_init("a", 1)
                interpreter.declare_and_init("b", 32)
                interpreter.declare_and_init("c", 54)
                interpreter.declare_and_init("d", 89)

                self.assertEqual(
                    interpreter.retrieve("a"),
                    1,
                )
                self.assertEqual(
                    interpreter.retrieve("b"),
                    32,
                )
                self.assertEqual(
                    interpreter.retrieve("c"),
                    54,
                )
                self.assertEqual(
                    interpreter.retrieve("d"),
                    89,
                )

                # Delayed initialization
                interpreter.declare('k')
                self.assertFalse(
                    interpreter.is_definitely_initialized('k'),
                )
                self.assertRaises(
                    SymbolNotInitializedError,
                    lambda: interpreter.retrieve('k')
                )
                interpreter.assign('k', 78, position=('a', 1))
                self.assertTrue(
                    interpreter.is_definitely_initialized('k'),
                )
                self.assertEqual(
                    interpreter.retrieve('k'),
                    78,
                )
                self.assertEqual(
                    interpreter.get_type('k'),
                    int,
                )

                # this table stands in for the members of some object whose
                # class is declared in the module. It doesn't inherit the root
                # table because class members are a separate namespace.
                class_table = SymbolTable()

                with class_table:
                    interpreter.declare_and_init("baz", 2)

                # if we encounter an if statement whose expression can't be
                # evaluated at compile time, we must in fact execute both the
                # if clause and the else clause, with a separated data state
                # for each because their execution contexts are separate.
                # Also, control flow blocks create new scopes, so each clause
                # gets its own symbol table too.
                if_registry = interpreter.child_registry()
                else_registry = interpreter.child_registry()
                with if_registry:
                    with interpreter.child_symbol_table() as if_table:
                        interpreter.assign("a", 3, position=("if", 1, 0))
                        interpreter.assign("b", 19)
                        interpreter.declare_and_init("c", 109)
                        interpreter.mark_symbol_used_at_runtime(
                            interpreter.get_symbol("a"),
                            ("if", 0, 0),
                        )
                        self.assertEqual(
                            interpreter.retrieve("a"),
                            3,
                        )
                        self.assertEqual(
                            interpreter.retrieve("b"),
                            19,
                        )
                        self.assertEqual(
                            interpreter.retrieve("c"),
                            109,
                        )
                    # After popping the child table we should be back
                    # to the original symbol for "c".
                    self.assertEqual(
                        interpreter.retrieve("c"),
                        54,
                    )
                # And after popping the child state we should be back
                # to the original values.
                self.assertEqual(
                    interpreter.retrieve("a"),
                    1,
                )
                self.assertEqual(
                    interpreter.retrieve("b"),
                    32,
                )
                self.assertEqual(
                    interpreter.get_runtime_usage_position(
                        interpreter.get_symbol("a"),
                    ),
                    None,
                )

                with interpreter.child_symbol_table() as else_table:
                    with else_registry:
                        interpreter.assign("a", 4, position=("else", 2, 0))
                        interpreter.assign("b", 19)
                        self.assertEqual(
                            interpreter.retrieve("a"),
                            4,
                        )
                        interpreter.mark_symbol_used_at_runtime(
                            interpreter.get_symbol("a"),
                            ("else", 0, 0),
                        )
                        self.assertEqual(
                            interpreter.retrieve("b"),
                            19,
                        )
                    # After popping the child state we should be back
                    # to the original values.
                    self.assertEqual(
                        interpreter.retrieve("a"),
                        1,
                    )
                    self.assertEqual(
                        interpreter.retrieve("b"),
                        32,
                    )

                root_registry.merge_children(
                    [
                        if_registry,
                        else_registry,
                    ]
                )

                # And now the root state has the updated values of "a"
                # and "b", with "a" being unknown because its value
                # differed in each clause.
                self.assertRaises(
                    SymbolValueAmbiguousError,
                    lambda: interpreter.retrieve("a"),
                )
                try:
                    interpreter.retrieve("a")
                except SymbolValueAmbiguousError, ex:
                    self.assertEqual(
                        list(sorted(ex.conflict.possibilities)),
                        [
                            (3, set([('if', 1, 0)])),
                            (4, set([('else', 2, 0)])),
                        ],
                    )
                else:
                    raise Exception("Didn't raise SymbolValueAmbiguousError?")
                self.assertEqual(
                    interpreter.retrieve("b"),
                    19,
                )
                self.assertEqual(
                    interpreter.retrieve("c"),
                    54,
                )
                self.assertEqual(
                    interpreter.retrieve("d"),
                    89,
                )
                self.assertEqual(
                    interpreter.get_runtime_usage_position(
                        interpreter.get_symbol("a"),
                    ),
                    ('else', 0, 0),
                )


class TestCallFrame(unittest.TestCase):

    def test_heirarchy(self):
        with Registry() as registry:
            first_frame = CallFrame()
            second_frame = first_frame.create_child()
            third_frame = second_frame.create_child()

            self.assertEqual(
                list(third_frame.trace),
                [
                    third_frame,
                    second_frame,
                    first_frame,
                ]
            )
            self.assertEqual(
                list(second_frame.trace),
                [
                    second_frame,
                    first_frame,
                ]
            )
            self.assertEqual(
                list(first_frame.trace),
                [
                    first_frame,
                ]
            )

    def test_return(self):
        from alamatic.types import Void

        with Registry() as registry:
            frame = CallFrame()

            self.assertFalse(
                frame.returning_early
            )
            self.assertEqual(
                frame.result_type,
                Void,
            )
            self.assertEqual(
                frame.error_type,
                Void,
            )

            frame.return_value(5)

            self.assertTrue(
                frame.returning_early
            )
            self.assertEqual(
                frame.result_type,
                int,
            )
            self.assertEqual(
                frame.result,
                5,
            )
            self.assertEqual(
                frame.error_type,
                Void,
            )

            with frame:
                self.assertTrue(
                    interpreter.returning_early
                )
                self.assertFalse(
                    interpreter.executing_forwards
                )

    def test_fail(self):
        from alamatic.types import Void

        with Registry() as registry:
            frame = CallFrame()

            self.assertFalse(
                frame.returning_early
            )
            self.assertEqual(
                frame.result_type,
                Void,
            )
            self.assertEqual(
                frame.error_type,
                Void,
            )

            frame.fail_with_value(5)

            self.assertTrue(
                frame.returning_early
            )
            self.assertEqual(
                frame.result_type,
                Void,
            )
            self.assertEqual(
                frame.error_value,
                5,
            )
            self.assertEqual(
                frame.error_type,
                int,
            )

            with frame:
                self.assertTrue(
                    interpreter.returning_early
                )
                self.assertFalse(
                    interpreter.executing_forwards
                )
