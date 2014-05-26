
import unittest
import mock
from alamatic.preprocessor.deadcode import *


class TestOptimizeTerminator(unittest.TestCase):

    def test_unoptimizable(self):
        block = mock.MagicMock('block')
        terminator = mock.MagicMock('terminator')
        block.terminator = terminator
        terminator.get_optimal_equivalent = mock.MagicMock()
        block.terminator.get_optimal_equivalent.return_value = block.terminator
        result = optimize_terminator(block)
        self.assertEqual(result, False)
        self.assertTrue(block.terminator is terminator)
        terminator.get_optimal_equivalent.assert_called_with()

    def test_optimizable(self):
        block = mock.MagicMock('block')
        terminator = mock.MagicMock('terminator')
        new_terminator = mock.MagicMock('new_terminator')
        block.terminator = terminator
        terminator.get_optimal_equivalent = mock.MagicMock()
        block.terminator.get_optimal_equivalent.return_value = new_terminator
        result = optimize_terminator(block)
        self.assertEqual(result, True)
        self.assertTrue(block.terminator is new_terminator)
        terminator.get_optimal_equivalent.assert_called_with()
