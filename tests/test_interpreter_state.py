
import unittest
from alamatic.interpreter import (
    interpreter,
    SymbolTable,
    DataState,
    Symbol,
    Storage,
    CallFrame,
)


class TestInterpreterState(unittest.TestCase):

    def test_symbol_table(self):
        sym = Symbol()
        root_table = SymbolTable()
        child_table = root_table.create_child()
        child_child_table = child_table.create_child()

        a_sym_1 = root_table.create_symbol("a")
        a_sym_2 = child_child_table.create_symbol("a")
        b_sym = child_table.create_symbol("b")
        c_sym = root_table.create_symbol("c")

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
            KeyError,
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

    def test_data_state(self):
        root_state = DataState()
        child_state = root_state.create_child()
        child_child_state = child_state.create_child()

        symbol_a = Symbol()
        symbol_b = Symbol()
        symbol_c = Symbol()

        # For the sake of this test we use Python's native types as our
        # value types. In real use, however, our interpreter has its own
        # tree of types that are instantiated from a specialized metaclass.
        # This object doesn't actually care as long as it can pass the
        # provided value into type()

        # Simple test of one state overriding another.
        root_state.set_symbol_value(symbol_a, 1);
        child_child_state.set_symbol_value(symbol_a, 2)

        self.assertEqual(
            root_state.get_symbol_value(symbol_a),
            1,
        )
        self.assertEqual(
            child_state.get_symbol_value(symbol_a),
            1,
        )
        self.assertEqual(
            child_child_state.get_symbol_value(symbol_a),
            2,
        )

        # The same symbol having a different type in different scopes.
        root_state.set_symbol_value(symbol_b, "hello");
        child_child_state.set_symbol_value(symbol_b, 3)

        self.assertEqual(
            root_state.get_symbol_value(symbol_b),
            "hello",
        )
        self.assertEqual(
            child_state.get_symbol_value(symbol_b),
            "hello",
        )
        self.assertEqual(
            child_child_state.get_symbol_value(symbol_b),
            3,
        )

        # Symbol that isn't present in the top state.
        child_state.set_symbol_value(symbol_c, 32)

        # It is an error to request the value for a symbol that isn't
        # known to the current state, since any code that creates an
        # entry in a symbol table must also make some statement about its
        # value in a data state whose lifetime is greater than or equal
        # to the symbol table itself.
        self.assertRaises(
            KeyError,
            lambda: root_state.get_symbol_value(symbol_c)
        )
        self.assertEqual(
            child_state.get_symbol_value(symbol_c),
            32,
        )
        self.assertEqual(
            child_child_state.get_symbol_value(symbol_c),
            32,
        )

    def test_combination(self):
        # This test simulates a realistic combined use of symbol tables
        # and data states together, approximating the machinations of
        # the interpreter executing a program.

        root_state = DataState()
        root_table = SymbolTable()

        with root_state:
            with root_table:
                interpreter.declare("a", 1)
                interpreter.declare("b", 32)
                interpreter.declare("c", 54)
                interpreter.declare("d", 89)

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

                # this table stands in for the members of some object whose
                # class is declared in the module. It doesn't inherit the root
                # table because class members are a separate namespace.
                class_table = SymbolTable()

                with class_table:
                    interpreter.declare("baz", 2)

                # if we encounter an if statement whose expression can't be
                # evaluated at compile time, we must in fact execute both the
                # if clause and the else clause, with a separated data state
                # for each because their execution contexts are separate.
                # Also, control flow blocks create new scopes, so each clause
                # gets its own symbol table too.
                if_state = interpreter.child_data_state()
                else_state = interpreter.child_data_state()
                with interpreter.child_symbol_table() as if_table:
                    with if_state:
                        interpreter.assign("a", 3)
                        interpreter.assign("b", 19)
                        interpreter.declare("c", 109)
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
                # And after popping the child table we should be back
                # to the original symbol for "c".
                self.assertEqual(
                    interpreter.retrieve("c"),
                    54,
                )
                with interpreter.child_symbol_table() as else_table:
                    with else_state:
                        interpreter.assign("a", 4)
                        interpreter.assign("b", 19)
                        self.assertEqual(
                            interpreter.retrieve("a"),
                            4,
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

                root_state.merge_children(
                    [
                        if_state,
                        else_state,
                    ]
                )

                # And now the root state has the updated values of "a"
                # and "b", with "a" being unknown because its value
                # differed in each clause.
                self.assertEqual(
                    interpreter.retrieve("a"),
                    None,
                )
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

    def test_call_frame(self):
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
