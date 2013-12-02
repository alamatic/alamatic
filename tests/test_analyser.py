
from alamatic.ast import *
from alamatic.types import *
from alamatic.intermediate import *
from alamatic.analyser import *
from alamatic.testutil import *


class TestBasicBlock(LanguageTestCase):

    def test_successor_is_conditional(self):
        a = BasicBlock()
        b = BasicBlock()
        c = BasicBlock()
        a.true_successor = b
        a.false_successor = c
        self.assertTrue(a.successor_is_conditional)
        a.false_successor = b
        self.assertFalse(a.successor_is_conditional)

    def test_is_loop_header(self):
        a = BasicBlock()
        b = BasicBlock()
        c = BasicBlock()
        a.index = 1
        b.index = 2
        c.index = 3
        b.predecessors.add(a)
        b.predecessors.add(c)
        c.predecessors.add(b)
        self.assertFalse(a.is_loop_header)
        self.assertTrue(b.is_loop_header)
        self.assertFalse(a.is_loop_header)
