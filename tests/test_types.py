
import unittest
import mock
from alamatic.types import *


class TestTypes(unittest.TestCase):

    def testTypeConstructorSingletons(self):
        cons = TypeConstructor()
        type_1 = cons(1)
        type_2 = cons(2)
        type_1_again = cons(1)

        self.assertTrue(
            type_1 is type_1_again
        )
        self.assertTrue(
            type_1 is not type_2
        )

    def testTypeUnifyCallbacks(self):
        cons = TypeConstructor()
        type_1 = cons(1)
        type_2 = cons(2)

        self.assertTrue(
            type_1 is not type_2
        )

        callback = mock.Mock()

        type_1.on_unify(callback)
        type_1._notify_unify(type_2)

        callback.assert_called_with(type_2)

    # FIXME: There's currently a recursion bug in here.
    @unittest.expectedFailure
    def testRecursiveUnify(self):
        nullary_cons_1 = TypeConstructor()
        nullary_cons_2 = TypeConstructor()
        nullary_cons_3 = TypeConstructor()
        binary_cons = TypeConstructor()
        inner_1 = nullary_cons_1()
        inner_2 = nullary_cons_2()
        inner_3 = nullary_cons_3()

        outer_1 = binary_cons(inner_1, inner_3)
        outer_2 = binary_cons(inner_2, inner_3)
        outer_3 = binary_cons(inner_3, inner_3)

        callback = mock.Mock()

        outer_1.on_unify(callback)
        inner_1._notify_unify(inner_2)

        callback.assert_called_with(outer_2)

        inner_2._notify_unify(inner_3)

        callback.assert_called_with(outer_3)
