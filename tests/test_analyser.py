
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


class TestControlFlowGraph(LanguageTestCase):

    def test_no_split(self):
        elems = [
            DummyOperation("begin"),
            DummyOperation("end"),
        ]
        self.assertControlFlowGraph(
            elems,
            [
                [
                    [
                        ('DummyOperation', ['begin']),
                        ('DummyOperation', ['end']),
                    ],
                    [],
                    [1],
                ],
                [
                    [],
                    [0],
                    [],
                ]
            ],
        )
        self.assertDominatorTree(
            elems,
            [
                [0],
                [0, 1],
            ]
        )

    def test_split_label(self):
        label = Label()
        elems = [
            DummyOperation("begin"),
            label,
            DummyOperation("end"),
        ]
        self.assertControlFlowGraph(
            elems,
            [
                [
                    [
                        ('DummyOperation', ['begin']),
                    ],
                    [],
                    [1],
                ],
                [
                    [
                        ('DummyOperation', ['end']),
                    ],
                    [0],
                    [2],
                ],
                [
                    [],
                    [1],
                    [],
                ]
            ],
        )
        self.assertDominatorTree(
            elems,
            [
                [0],
                [0, 1],
                [0, 1, 2],
            ],
        )

    def test_split_jump(self):
        label = Label()
        elems = [
            DummyOperation("begin"),
            JumpOperation(label),
            DummyOperation("middle"),
            label,
            DummyOperation("end"),
        ]
        self.assertControlFlowGraph(
            elems,
            [
                [
                    [
                        ('DummyOperation', ['begin']),
                    ],
                    [],
                    [1],
                ],
                [
                    [
                        ('DummyOperation', ['end']),
                    ],
                    [0],
                    [2],
                ],
                [
                    [],
                    [1],
                    [],
                ],
            ],
        )
        self.assertDominatorTree(
            elems,
            [
                [0],
                [0, 1],
                [0, 1, 2],
            ],
        )

    def test_split_jump_if_false(self):
        label = Label()
        elems = [
            DummyOperation("begin"),
            JumpIfFalseOperation(
                ConstantOperand(Bool(True)),
                label,
            ),
            DummyOperation("middle"),
            label,
            DummyOperation("end"),
        ]
        self.assertControlFlowGraph(
            elems,
            [
                [
                    [
                        ('DummyOperation', ['begin']),
                    ],
                    [],
                    [1, 2],
                ],
                [
                    [
                        ('DummyOperation', ['middle']),
                    ],
                    [0],
                    [2],
                ],
                [
                    [
                        ('DummyOperation', ['end']),
                    ],
                    [0, 1],
                    [3],
                ],
                [
                    [],
                    [2],
                    [],
                ],
            ],
        )
        self.assertDominatorTree(
            elems,
            [
                [0],
                [0, 1],
                [0, 2],
                [0, 2, 3],
            ],
        )
