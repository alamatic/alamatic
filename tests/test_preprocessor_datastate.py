
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


class TestCell(LanguageTestCase):

    def test_outlives(self):
        lifetime = MagicMock()
        cell_1 = Cell(lifetime)
        cell_2 = Cell(lifetime)

        lifetime.outlives.return_value = True
        self.assertTrue(
            cell_1.outlives(cell_2)
        )

        lifetime.outlives.assert_called_with(
            lifetime,
        )

        lifetime.outlives.return_value = False
        self.assertFalse(
            cell_1.outlives(cell_2)
        )


class TestDataState(LanguageTestCase):

    def test_assign_symbol_value(self):
        frame = MagicMock()
        frame.get_cell_for_symbol.return_value = "dummy_cell"
        symbol = MagicMock()
        state = DataState(frame)
        value = DummyType(5)
        state.assign_symbol_value(
            symbol,
            value,
            position=('test', 1, 0),
        )
        self.assertEqual(
            state._cell_init_positions["dummy_cell"],
            ('test', 1, 0),
        )
        self.assertEqual(
            state._cell_values["dummy_cell"],
            value,
        )
        frame.get_cell_for_symbol.assert_called_with(
            symbol,
        )

        value = DummyType(4)
        state.assign_symbol_value(
            symbol,
            value,
            position=('test', 2, 0),
        )
        self.assertEqual(
            state._cell_init_positions["dummy_cell"],
            ('test', 1, 0),
        )
        self.assertEqual(
            state._cell_values["dummy_cell"],
            value,
        )

        class DummyType2(DummyType):
            pass

        from alamatic.preprocessor import InappropriateTypeError
        value = DummyType2(6)
        self.assertRaises(
            InappropriateTypeError,
            lambda: state.assign_symbol_value(
                symbol,
                value,
                position=('test', 3, 0),
            )
        )

    def test_retrieve_symbol_value(self):
        frame = MagicMock()
        frame.get_cell_for_symbol.return_value = "dummy_cell"
        symbol = MagicMock()
        symbol.assignable = False
        state = DataState(frame)

        unk = state.retrieve_symbol_value(symbol)
        self.assertEqual(
            unk.apparent_type,
            Unknown,
        )

        frame.get_cell_for_symbol.assert_called_with(
            symbol,
        )

        state._cell_values["dummy_cell"] = DummyType(5)
        known = state.retrieve_symbol_value(symbol)
        self.assertEqual(
            known.apparent_type,
            DummyType,
        )
        self.assertEqual(
            type(known),
            DummyType,
        )
        self.assertEqual(
            known.value,
            5,
        )

        symbol.assignable = True
        known = state.retrieve_symbol_value(symbol)
        self.assertEqual(
            known.apparent_type,
            DummyType,
        )
        self.assertEqual(
            type(known),
            Unknown,
        )

    def test_update_from_predecessors_ready(self):
        frame = MagicMock()
        state = DataState(frame)

        value_1 = MagicMock(name="value_1")
        value_2 = MagicMock(name="value_2")
        value_3 = MagicMock(name="value_3")
        value_4 = MagicMock(name="value_4")

        value_1.merge.return_value = value_4

        dummy_state_1 = MagicMock()
        dummy_state_2 = MagicMock()
        dummy_state_1.ready = True
        dummy_state_2.ready = True
        dummy_state_1._cell_values = {}
        dummy_state_2._cell_values = {}
        dummy_state_1._cell_values["dummy1"] = value_1
        dummy_state_2._cell_values["dummy1"] = value_2
        dummy_state_1._cell_values["dummy2"] = value_3

        state.update_from_predecessors([dummy_state_1, dummy_state_2])

        value_1.merge.assert_called_with(
            value_2,
        )

        self.assertEqual(
            state._cell_values,
            {
                "dummy1": value_4,
                "dummy2": value_3,
            }
        )

    def test_update_from_predecessors_unready(self):
        frame = MagicMock()
        state = DataState(frame)

        dummy_state_1 = MagicMock()
        dummy_state_2 = MagicMock()
        dummy_state_1.ready = True
        dummy_state_2.ready = False
        dummy_state_1._cell_values = {}
        dummy_state_2._cell_values = {}
        dummy_state_1._cell_values["dummy1"] = 1
        dummy_state_2._cell_values["dummy1"] = 2
        dummy_state_1._cell_values["dummy2"] = 3

        state.update_from_predecessors([dummy_state_1, dummy_state_2])

        # All of the cells come back as unknown because state 2 isn't ready.
        self.assertEqual(
            state._cell_values,
            {
                "dummy1": Unknown(),
                "dummy2": Unknown(),
            }
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
