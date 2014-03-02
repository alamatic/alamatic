
from alamatic.types import *
from alamatic.testutil import *
from alamatic.preprocessor.datastate import *

from mock import MagicMock


class TestCallFrame(LanguageTestCase):

    def test_init(self):
        unit = MagicMock()
        unit.symbols = MagicMock()
        unit.symbols.all_symbols = [
            # Normally these would be actual symbol objects but
            # we'll just use strings for the sake of this test,
            # since CalLFrame treats symbols as opaque references.
            "a",
            "b",
            "c",
        ]
        frame = CallFrame(unit)
        self.assertEqual(
            set(frame.symbol_cells.iterkeys()),
            set(["a", "b", "c"])
        )
        self.assertEqual(
            type(frame.get_cell_for_symbol("a")),
            Cell,
        )

    def test_heirarchy(self):
        unit_1 = MagicMock()
        unit_1.symbols = MagicMock()
        unit_1.symbols.all_symbols = [
            # Normally these would be actual symbol objects but
            # we'll just use strings for the sake of this test,
            # since CalLFrame treats symbols as opaque references.
            "a",
        ]
        frame_1 = CallFrame(unit_1)

        unit_2 = MagicMock()
        unit_2.symbols = MagicMock()
        unit_2.symbols.all_symbols = [
            "b",
        ]

        frame_2 = CallFrame(unit_2, parent=frame_1)

        self.assertEqual(
            type(frame_2.get_cell_for_symbol("a")),
            Cell,
        )
        self.assertEqual(
            type(frame_2.get_cell_for_symbol("b")),
            Cell,
        )


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
