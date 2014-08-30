
import unittest
import mock
from alamatic.preprocessor.typeinfer import (
    TypeInferer,
    TypeTable,
    TypeContext,
)


def make_mock_type(name, *type_args):
    ret = mock.Mock(name=name)
    ret.type_args = tuple(type_args)
    ret.value_args = tuple()
    ret.cons.impls = ()
    return ret


class TestTypeTable(unittest.TestCase):

    def test_add_new(self):
        table = TypeTable()
        mock_type = make_mock_type("type")
        mock_symbol = mock.Mock(name="symbol")
        table.add(mock_symbol, mock_type)
        self.assertEqual(
            dict(table._symbol_types),
            {
                mock_symbol: mock_type,
            }
        )
        self.assertEqual(
            dict(table._equivalences),
            {}
        )

    def test_add_unified_new(self):
        table = TypeTable()
        mock_symbol = mock.Mock(name="symbol")
        mock_type_1 = make_mock_type(name="type_1")
        mock_type_2 = make_mock_type(name="type_2")
        mock_type_3 = make_mock_type(name="type_3")
        mock_type_1.unify = lambda x: mock_type_3
        table.add(mock_symbol, mock_type_1)
        table.add(mock_symbol, mock_type_2)
        self.assertEqual(
            dict(table._symbol_types),
            {
                mock_symbol: mock_type_3,
            }
        )
        self.assertEqual(
            dict(table._equivalences),
            {
                mock_type_1: mock_type_3,
                mock_type_2: mock_type_3,
            }
        )

    def test_add_unified_first(self):
        table = TypeTable()
        mock_symbol = mock.Mock(name="symbol")
        mock_type_1 = make_mock_type(name="type_1")
        mock_type_2 = make_mock_type(name="type_2")
        mock_type_1.unify = lambda x: mock_type_1
        table.add(mock_symbol, mock_type_1)
        table.add(mock_symbol, mock_type_2)
        self.assertEqual(
            dict(table._symbol_types),
            {
                mock_symbol: mock_type_1,
            }
        )
        self.assertEqual(
            dict(table._equivalences),
            {
                mock_type_2: mock_type_1,
            }
        )

    def test_add_unified_second(self):
        table = TypeTable()
        mock_symbol = mock.Mock(name="symbol")
        mock_type_1 = make_mock_type(name="type_1")
        mock_type_2 = make_mock_type(name="type_2")
        mock_type_1.unify = lambda x: mock_type_2
        table.add(mock_symbol, mock_type_1)
        table.add(mock_symbol, mock_type_2)
        self.assertEqual(
            dict(table._symbol_types),
            {
                mock_symbol: mock_type_2,
            }
        )
        self.assertEqual(
            dict(table._equivalences),
            {
                mock_type_1: mock_type_2,
            }
        )

    def test_equivalent_flattening(self):
        table = TypeTable()
        mock_symbol_1 = mock.Mock(name="symbol_1")
        mock_symbol_2 = mock.Mock(name="symbol_2")
        mock_type_1 = make_mock_type(name="type_1")
        mock_type_2 = make_mock_type(name="type_2")
        mock_type_1.unify = lambda x: mock_type_1
        table.add(mock_symbol_1, mock_type_2)
        table.add(mock_symbol_2, mock_type_1)
        table.add(mock_symbol_2, mock_type_2)
        self.assertEqual(
            dict(table._symbol_types),
            {
                mock_symbol_1: mock_type_2,
                mock_symbol_2: mock_type_1,
            }
        )
        self.assertEqual(
            dict(table._equivalences),
            {
                mock_type_2: mock_type_1,
            }
        )

        # Accessing the entry for mock_symbol_1 automatically flattens it
        self.assertEqual(
            table[mock_symbol_1],
            mock_type_1,
        )

        # .. so now the mapping is updated.
        self.assertEqual(
            dict(table._symbol_types),
            {
                mock_symbol_1: mock_type_1,
                mock_symbol_2: mock_type_1,
            }
        )

    def test_recursive_equivalent_flattening(self):
        table = TypeTable()
        mock_symbol_1 = mock.Mock(name="symbol_1")
        mock_type_1 = make_mock_type(name="type_1")
        mock_type_2 = make_mock_type(name="type_2")
        mock_outer_type = make_mock_type("outer_type", mock_type_1)
        table.add(mock_symbol_1, mock_outer_type)
        table._equivalences[mock_type_1] = mock_type_2
        self.assertEqual(
            table[mock_symbol_1].type_args,
            (mock_type_2,),
        )

    def test_unknown_symbol(self):
        table = TypeTable()
        mock_symbol = mock.Mock(name="symbol")

        self.assertEqual(
            dict(table._symbol_types),
            {}
        )

        # Accessing the same unknown symbol twice returns the same type
        # instance.
        self.assertEqual(
            table[mock_symbol],
            table[mock_symbol],
        )

    def test_equality(self):
        table_1 = TypeTable()
        table_2 = TypeTable()
        mock_symbol = mock.Mock(name="symbol")
        mock_type = make_mock_type(name="type")
        table_1.add(mock_symbol, mock_type)
        table_2.add(mock_symbol, mock_type)

        self.assertEqual(
            table_1,
            table_2,
        )

    def test_merge(self):
        table_1 = TypeTable()
        table_2 = TypeTable()

        mock_symbol_1 = mock.Mock(name="symbol_1")
        mock_symbol_2 = mock.Mock(name="symbol_2")
        mock_symbol_3 = mock.Mock(name="symbol_3")
        mock_type_1 = make_mock_type(name="type_1")
        mock_type_2 = make_mock_type(name="type_2")
        mock_type_3 = make_mock_type(name="type_3")

        mock_type_1.unify.return_value = mock_type_1

        table_1.add(mock_symbol_1, mock_type_1)
        table_1.add(mock_symbol_2, mock_type_1)
        table_2.add(mock_symbol_2, mock_type_2)
        table_2.add(mock_symbol_3, mock_type_3)

        table_1.merge(table_2)

        mock_type_1.unify.assert_called_with(
            mock_type_2,
        )

        self.assertEqual(
            table_1[mock_symbol_1],
            mock_type_1,
        )
        self.assertEqual(
            table_1[mock_symbol_2],
            mock_type_1,
        )
        self.assertEqual(
            table_1[mock_symbol_3],
            mock_type_3,
        )

    def test_iterate(self):
        table = TypeTable()

        mock_symbol_1 = mock.Mock(name="symbol_1")
        mock_symbol_2 = mock.Mock(name="symbol_2")
        mock_symbol_3 = mock.Mock(name="symbol_3")
        mock_type_1 = make_mock_type(name="type_1")
        mock_type_2 = make_mock_type(name="type_2")
        mock_type_3 = make_mock_type(name="type_3")

        table.add(mock_symbol_1, mock_type_1)
        table.add(mock_symbol_2, mock_type_2)
        table.add(mock_symbol_3, mock_type_3)

        self.assertEqual(
            set(table),
            set(
                [
                    mock_symbol_1,
                    mock_symbol_2,
                    mock_symbol_3,
                ]
            )
        )
        self.assertEqual(
            set(table),
            set(
                [
                    mock_symbol_1,
                    mock_symbol_2,
                    mock_symbol_3,
                ]
            )
        )
        self.assertEqual(
            set(table.itervalues()),
            set(
                [
                    mock_type_1,
                    mock_type_2,
                    mock_type_3,
                ]
            )
        )
        self.assertEqual(
            set(table.iteritems()),
            set(
                [
                    (mock_symbol_1, mock_type_1),
                    (mock_symbol_2, mock_type_2),
                    (mock_symbol_3, mock_type_3),
                ]
            )
        )


class TestTypeInferer(unittest.TestCase):

    def test_infer_symbol_lvalue(self):
        inferer = TypeInferer()
        mock_block = mock.Mock(name="block")
        mock_operand = mock.Mock(name="operand")
        mock_symbol = mock.Mock(name="symbol")
        mock_instruction = mock.Mock(name="instruction")
        mock_operation = mock.Mock(name="operation")
        mock_type = make_mock_type(name="type")

        mock_block.operation_instructions = [mock_instruction]
        mock_block.predecessors = []
        mock_instruction.target = mock_operand
        mock_instruction.operation = mock_operation
        mock_operand.symbol = mock_symbol
        mock_operation.get_result_type.return_value = mock_type

        changed = inferer.infer_types_for_block(mock_block)

        self.assertTrue(changed)

        table = inferer.get_inferences_for_block(mock_block)

        self.assertEqual(
            type(table),
            TypeTable,
        )
        self.assertEqual(
            table[mock_symbol],
            mock_type,
        )

    def test_infer_predecessors(self):
        pred_table_1 = TypeTable()
        pred_table_2 = TypeTable()

        mock_block = mock.Mock(name="block")
        mock_pred_block_1 = mock.Mock(name="pred_block_1")
        mock_pred_block_2 = mock.Mock(name="pred_block_2")
        mock_block.operation_instructions = []
        mock_block.predecessors = [
            mock_pred_block_1,
            mock_pred_block_2,
        ]

        mock_symbol_1 = mock.Mock(name="symbol_1")
        mock_symbol_2 = mock.Mock(name="symbol_2")
        mock_type_1 = make_mock_type(name="type_1")
        mock_type_2 = make_mock_type(name="type_2")

        pred_table_1.add(mock_symbol_1, mock_type_1)
        pred_table_2.add(mock_symbol_2, mock_type_2)

        inferer = TypeInferer()
        inferer._block_inferences[mock_pred_block_1] = pred_table_1

        changed = inferer.infer_types_for_block(mock_block)
        self.assertFalse(changed)  # Not changed because predecessors not ready
        self.assertEqual(
            len(list(inferer.get_inferences_for_block(mock_block))),
            0,  # no inferences yet because pred_block_2 isn't ready
        )

        # Make pred_block_2 ready
        inferer._block_inferences[mock_pred_block_2] = pred_table_2

        changed = inferer.infer_types_for_block(mock_block)
        self.assertTrue(changed)
        self.assertEqual(
            # Symbols from both predecessors have been merged.
            dict(inferer.get_inferences_for_block(mock_block).iteritems()),
            {
                mock_symbol_1: mock_type_1,
                mock_symbol_2: mock_type_2,
            }
        )
        self.assertEqual(
            # pred_table_1 left unchanged.
            dict(pred_table_1.iteritems()),
            {
                mock_symbol_1: mock_type_1,
            }
        )
        self.assertEqual(
            # pred_table_2 left unchanged.
            dict(pred_table_2.iteritems()),
            {
                mock_symbol_2: mock_type_2,
            }
        )
