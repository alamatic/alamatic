
import unittest
import mock
from alamatic.types import *


class TestTypes(unittest.TestCase):

    def testTypeConstructorNoArgs(self):
        cons = TypeConstructor()
        new_type = cons()

        self.assertEqual(
            new_type.cons,
            cons,
        )

    def testSimpleUnifyKnownUnknown(self):
        cons = TypeConstructor()
        bound_type = cons()

        var_1 = TypeVariable()
        var_2 = TypeVariable()

        var_1.type = bound_type

        unified_var = unified_type_variable(var_1, var_2)

        self.assertTrue(
            unified_var.type is bound_type
        )

    def testNestedUnifyKnownUnknown(self):
        collection_cons = TypeConstructor()
        simple_cons = TypeConstructor()

        inner_type = simple_cons()

        inner_var_1 = TypeVariable()
        inner_var_2 = TypeVariable()

        collection_type_1 = collection_cons(inner_var_1)
        collection_type_2 = collection_cons(inner_var_2)

        inner_var_1.type = inner_type

        outer_var_1 = TypeVariable()
        outer_var_2 = TypeVariable()

        outer_var_1.type = collection_type_1
        outer_var_2.type = collection_type_2

        unified_var = unified_type_variable(outer_var_1, outer_var_2)

        self.assertEqual(
            unified_var.type.cons,
            collection_cons,
        )
        self.assertEqual(
            len(unified_var.type.args),
            1,
        )
        self.assertEqual(
            unified_var.type.args[0].type,
            inner_type,
        )
