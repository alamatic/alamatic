
from mock import MagicMock
import unittest
from alamatic.intermediate.scope import *


class Variable(Symbol):

    def __init__(self, index, decl_name, decl_range):
        Symbol.__init__(self, decl_name, decl_range)
        self.index = index


class VariableTable(object):

    def __init__(self):
        self.next_index = 1

    def make_variable(self, decl_name, decl_range):
        index = self.next_index
        self.next_index += 1
        return Variable(index, decl_name, decl_range)


class TestScope(unittest.TestCase):

    def test_variables(self):
        table = VariableTable()
        scope = Scope(
            variable_cons=table.make_variable,
            constant_cons=None,
        )
        nonexist = scope.get_symbol("nonexist")
        self.assertEqual(nonexist, None)

        foo = scope.declare_variable("foo", "dummy source range")
        self.assertEqual(foo.index, 1)
        self.assertEqual(foo.decl_name, "foo")
        self.assertEqual(foo.decl_range, "dummy source range")

        foo_2 = scope.get_symbol("foo")
        self.assertEqual(foo, foo_2)

        bar = scope.declare_variable("bar", "dummy source range 2")
        bar_2 = scope.get_symbol("bar")
        self.assertEqual(bar, bar_2)

    def test_scope_tree(self):
        root_table = VariableTable()
        grandchild_table = VariableTable()

        root_scope = Scope(
            variable_cons=root_table.make_variable,
            constant_cons=None,
        )
        child_scope = root_scope.create_child()
        ignored_scope = root_scope.create_child()
        grandchild_scope = child_scope.create_child(
            variable_cons=grandchild_table.make_variable,
        )

        root_scope.declare_variable("foo")
        grandchild_scope.declare_variable("foo")

        root_foo = root_scope.get_symbol("foo")
        child_foo = child_scope.get_symbol("foo")
        grandchild_foo = grandchild_scope.get_symbol("foo")

        self.assertEqual(root_foo.index, 1)
        self.assertEqual(child_foo, root_foo)
        self.assertEqual(grandchild_foo.index, 1)
        self.assertNotEqual(grandchild_foo, root_foo)

        self.assertEqual(
            child_scope.get_local_symbol("foo"),
            None,
        )
