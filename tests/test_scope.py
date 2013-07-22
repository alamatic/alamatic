
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
