
from alamatic.types import *
from alamatic.testutil import *
from alamatic.preprocessor.datastate import *


class TestLifetime(LanguageTestCase):

    def test_allocate_cell(self):
        lifetime = Lifetime()
        cell = lifetime.allocate_cell()
        self.assertEqual(
            type(cell),
            Cell,
        )
        self.assertEqual(
            cell.lifetime,
            lifetime,
        )

    def test_heirarchy(self):
        root_lifetime = Lifetime()
        child_lifetime_1 = Lifetime(root_lifetime)
        child_lifetime_2 = Lifetime(root_lifetime)
        grandchild_lifetime = Lifetime(child_lifetime_1)

        self.assertEqual(
            [
                x.root for x in (
                    root_lifetime,
                    child_lifetime_1,
                    child_lifetime_2,
                    grandchild_lifetime,
                )
            ],
            [
                root_lifetime for x in xrange(0, 4)
            ]
        )
        self.assertEqual(
            child_lifetime_1.parent,
            root_lifetime,
        )
        self.assertTrue(
            root_lifetime.outlives(child_lifetime_1)
        )
        self.assertTrue(
            root_lifetime.outlives(child_lifetime_2)
        )
        self.assertTrue(
            root_lifetime.outlives(grandchild_lifetime)
        )
        self.assertTrue(
            child_lifetime_1.outlives(grandchild_lifetime)
        )
        self.assertFalse(
            root_lifetime.outlives(root_lifetime)
        )
        self.assertFalse(
            child_lifetime_2.outlives(root_lifetime)
        )
        self.assertFalse(
            grandchild_lifetime.outlives(root_lifetime)
        )
