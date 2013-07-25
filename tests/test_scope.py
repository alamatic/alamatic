
import unittest
from alamatic.scope import SymbolTable, DataState, Symbol, Storage


class TestScope(unittest.TestCase):

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

        # the root table represents the global scope of a module
        root_table = SymbolTable()

        # we start executing the module in a root state
        root_state = DataState()

        # var a = 1
        sym_root_a = root_table.create_symbol("a")
        sym_root_b = root_table.create_symbol("b")
        sym_root_c = root_table.create_symbol("c")
        sym_root_d = root_table.create_symbol("d")
        root_state.set_symbol_value(sym_root_a, 1)
        root_state.set_symbol_value(sym_root_b, 32)
        root_state.set_symbol_value(sym_root_c, 54)
        root_state.set_symbol_value(sym_root_d, 89)

        # this table stands in for the members of some object whose class
        # is declared in the module. It doesn't inherit the root table
        # because class members are a separate namespace.
        class_table = SymbolTable()

        # the class has a member "baz" whose value is 2, and since the
        # object is instantiated at the top-level of the module the values
        # of its members live in the root state.
        sym_class_baz = class_table.create_symbol("baz")
        root_state.set_symbol_value(sym_class_baz, 2)

        # if we encounter an if statement whose expression can't be
        # evaluated at compile time, we must in fact execute both the
        # if clause and the else clause, with a separated data state
        # for each because their execution contexts are separate.
        # Also, control flow blocks create new scopes, so each clause
        # gets its own symbol table too.
        if_table = root_table.create_child()
        if_state = root_state.create_child()
        if_state.set_symbol_value(sym_root_a, 3)
        if_state.set_symbol_value(sym_root_b, 19)
        if_state.clear_symbol_value(sym_root_d)
        else_table = root_table.create_child()
        else_state = root_state.create_child()
        else_state.set_symbol_value(sym_root_a, 4)
        else_state.set_symbol_value(sym_root_b, 19)

        # The above represents the following outcome:
        # - if and else assigned differing values to a
        # - if and else both assigned the same value to b
        # - neither clause touched c
        # - the if clause wrote something to d that can't be determined
        #   until runtime.

        # TODO: Implement a function to diff two states and retain only
        # what they have in common, and another function to absorb the
        # changes from a child state back into a parent, then test the
        # remaining workflow of updating the root state to reflect the
        # common results of the if and else clauses.
