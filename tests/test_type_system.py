
import unittest
import mock
from alamatic.types.base import *


class TestTypeSystem(unittest.TestCase):

    def test_cons_with_impl(self):
        mock_impl = mock.Mock()
        cons = TypeConstructor(mock_impl)
        self.assertFalse(cons.is_variable)

    def test_cons_without_impl(self):
        cons = TypeConstructor()
        self.assertTrue(cons.is_variable)

    def test_cons_instantiate_singletons(self):
        cons = TypeConstructor()
        no_args = cons.instantiate()
        args_1 = cons.instantiate((no_args,))
        args_2 = cons.instantiate((no_args, no_args))
        self.assertEqual(
            id(cons.instantiate()),
            id(no_args),
        )
        self.assertNotEqual(
            id(cons.instantiate()),
            id(args_1),
        )
        self.assertEqual(
            id(cons.instantiate((no_args,))),
            id(args_1),
        )
        self.assertEqual(
            id(cons.instantiate((no_args, no_args))),
            id(args_2),
        )

    def test_types_hashable(self):
        cons = TypeConstructor()
        no_args = cons.instantiate()
        args_1 = cons.instantiate((no_args,))
        self.assertEqual(
            hash(no_args),
            hash(no_args),
        )
        self.assertEqual(
            hash(args_1),
            hash(args_1),
        )

    def test_value_args(self):
        cons = TypeConstructor()
        value_args_1 = cons.instantiate((), (1,))
        value_args_2 = cons.instantiate((), (2,))

        self.assertNotEqual(
            value_args_1,
            value_args_2,
        )
        # Ensure that value args are included in the hash.
        self.assertNotEqual(
            hash(value_args_1),
            hash(value_args_2),
        )
