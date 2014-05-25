
import unittest
import mock
from alamatic.intermediate import (
    JumpInstruction,
    JumpIfFalseInstruction,
    JumpNeverInstruction,
    IsolateInstruction,
    Unknown,
)


class TestJumpInstruction(unittest.TestCase):

    def test_get_optimal_equilvalent(self):
        instr = JumpInstruction(
            label=mock.MagicMock('label'),
        )
        result = instr.get_optimal_equivalent()
        self.assertTrue(instr is result)

    def test_relationships(self):
        label = mock.MagicMock('label')
        instr = JumpInstruction(
            label=label,
        )
        self.assertFalse(instr.can_fall_through)
        self.assertEqual(
            instr.jump_targets,
            set([label]),
        )


class TestJumpNeverInstruction(unittest.TestCase):

    def test_relationships(self):
        instr = JumpNeverInstruction()
        self.assertTrue(instr.can_fall_through)
        self.assertEqual(
            instr.jump_targets,
            set([]),
        )


class TestIsolateInstruction(unittest.TestCase):

    def test_relationships(self):
        instr = IsolateInstruction()
        self.assertFalse(instr.can_fall_through)
        self.assertEqual(
            instr.jump_targets,
            set([]),
        )


class TestJumpIfFalseInstruction(unittest.TestCase):

    def test_get_optimal_equilvalent_true(self):
        operand = mock.MagicMock('operand')
        operand.constant_value = True
        instr = JumpIfFalseInstruction(
            cond=operand,
            label=mock.MagicMock('label'),
        )
        result = instr.get_optimal_equivalent()
        self.assertTrue(instr is not result)
        self.assertTrue(isinstance(result, JumpNeverInstruction))

    def test_get_optimal_equilvalent_false(self):
        operand = mock.MagicMock('operand')
        label = mock.MagicMock('label')
        operand.constant_value = False
        instr = JumpIfFalseInstruction(
            cond=operand,
            label=label,
        )
        result = instr.get_optimal_equivalent()
        self.assertTrue(instr is not result)
        self.assertTrue(isinstance(result, JumpInstruction))
        self.assertTrue(result.label is label)

    def test_get_optimal_equilvalent_unknown(self):
        operand = mock.MagicMock('operand')
        label = mock.MagicMock('label')
        operand.constant_value = Unknown
        instr = JumpIfFalseInstruction(
            cond=operand,
            label=mock.MagicMock('label'),
        )
        result = instr.get_optimal_equivalent()
        self.assertTrue(instr is result)

    def test_relationships(self):
        label = mock.MagicMock('label')
        instr = JumpIfFalseInstruction(
            cond=mock.MagicMock('cond'),
            label=label,
        )
        self.assertTrue(instr.can_fall_through)
        self.assertEqual(
            instr.jump_targets,
            set([label]),
        )
