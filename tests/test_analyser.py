
from alamatic.ast import *
from alamatic.types import *
from alamatic.intermediate import *
from alamatic.analyser import *
from alamatic.testutil import *


class TestControlFlowGraph(LanguageTestCase):

    def test_no_split(self):
        elems = [
            DummyOperation("begin"),
            DummyOperation("end"),
        ]
        self.assertControlFlowGraph(
            elems,
            [
                entry_block_comparison_node,
                [
                    None,
                    [
                        ('DummyOperation', ['begin']),
                        ('DummyOperation', ['end']),
                    ],
                    ('JumpNeverOperation', []),
                    (2,)
                ],
                exit_block_comparison_node,
            ],
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
                entry_block_comparison_node,
                [
                    None,
                    [
                        ('DummyOperation', ['begin']),
                    ],
                    ('JumpNeverOperation', []),
                    (2,),
                ],
                [
                    ('Label', []),
                    [
                        ('DummyOperation', ['end']),
                    ],
                    ('JumpNeverOperation', []),
                    (3,),
                ],
                exit_block_comparison_node,
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
                entry_block_comparison_node,
                [
                    None,
                    [
                        ('DummyOperation', ['begin']),
                    ],
                    ('JumpOperation', [
                        ('Label', None),
                    ]),
                    (2,),
                ],
                # the block with "middle" is not visible here
                # because it's unreachable. (It's still present in the
                # underlying data structure, but our graph traversal
                # can't reach it.)
                [
                    ('Label', []),
                    [
                        ('DummyOperation', ['end']),
                    ],
                    ('JumpNeverOperation', []),
                    (3,),
                ],
                exit_block_comparison_node,
            ],
        )

    def test_split_jump_if_false(self):
        from alamatic.types import Bool

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
                entry_block_comparison_node,
                [
                    None,
                    [
                        ('DummyOperation', ['begin']),
                    ],
                    ('JumpIfFalseOperation', [
                        ('ConstantOperand', [
                            ('Bool', (True,)),
                        ]),
                        ('Label', None),
                    ]),
                    (2, 3),
                ],
                [
                    None,
                    [
                        ('DummyOperation', ['middle']),
                    ],
                    ('JumpNeverOperation', []),
                    (3,),
                ],
                [
                    ('Label', []),
                    [
                        ('DummyOperation', ['end']),
                    ],
                    ('JumpNeverOperation', []),
                    (4,),
                ],
                exit_block_comparison_node,
            ],
        )

    def test_predecessor_map(self):
        from alamatic.analyser import (
            _create_initial_predecessor_map_for_blocks,
        )
        dummy_blocks = DummyBasicBlock.create_list(
            [1],
            [2, 3],
            [3],
            [],
        )
        predecessor_map = _create_initial_predecessor_map_for_blocks(
            dummy_blocks,
        )
        simple_map = {}
        for k, v in predecessor_map.iteritems():
            simple_map[k.index] = list(sorted(
                x.index for x in v
            ))
        self.assertEqual(
            simple_map,
            {
                1: [0],
                2: [1],
                3: [1, 2],
            },
        )

    def test_dominator_map_branch(self):
        from alamatic.analyser import (
            _create_dominator_map_for_blocks,
        )
        dummy_blocks = DummyBasicBlock.create_list(
            [1],
            [2, 3],
            [3],
            [],
        )
        dominator_map = _create_dominator_map_for_blocks(
            dummy_blocks,
        )
        simple_map = {}
        for k, v in dominator_map.iteritems():
            simple_map[k.index] = list(sorted(
                x.index for x in v
            ))
        self.assertEqual(
            simple_map,
            {
                0: [0],
                1: [0, 1],
                2: [0, 1, 2],
                3: [0, 1, 3],
            },
        )

    def test_dominator_map_loop(self):
        from alamatic.analyser import (
            _create_dominator_map_for_blocks,
        )
        dummy_blocks = DummyBasicBlock.create_list(
            [1, 2],
            [0],
            [],
        )
        dominator_map = _create_dominator_map_for_blocks(
            dummy_blocks,
        )
        simple_map = {}
        for k, v in dominator_map.iteritems():
            simple_map[k.index] = list(sorted(
                x.index for x in v
            ))
        self.assertEqual(
            simple_map,
            {
                0: [0],
                1: [0, 1],
                2: [0, 2],
            },
        )

    def test_dominator_map_nested_loops(self):
        from alamatic.analyser import (
            _create_dominator_map_for_blocks,
        )
        dummy_blocks = DummyBasicBlock.create_list(
            [1, 4],
            [2, 3],
            [1],
            [0],
            [],
        )
        dominator_map = _create_dominator_map_for_blocks(
            dummy_blocks,
        )
        simple_map = {}
        for k, v in dominator_map.iteritems():
            simple_map[k.index] = list(sorted(
                x.index for x in v
            ))
        self.assertEqual(
            simple_map,
            {
                0: [0],
                1: [0, 1],
                2: [0, 1, 2],
                3: [0, 1, 3],
                4: [0, 4],
            },
        )

    def test_loop_tree_with_no_loops(self):
        from alamatic.analyser import (
            _create_loop_tree_for_blocks,
        )
        dummy_blocks = DummyBasicBlock.create_list(
            [1],
            [2, 3],
            [3],
            [],
        )
        root_loops, child_loops, closest_loops = _create_loop_tree_for_blocks(
            dummy_blocks,
        )
        self.assertEqual(
            root_loops,
            set(),
        )
        self.assertEqual(
            len(child_loops),
            0,
        )
        self.assertEqual(
            len(closest_loops),
            0,
        )

    def test_loop_tree_with_simple_loop(self):
        from alamatic.analyser import (
            _create_loop_tree_for_blocks,
        )
        dummy_blocks = DummyBasicBlock.create_list(
            [1, 2],
            [0],
            [],
        )
        root_loops, child_loops, closest_loops = _create_loop_tree_for_blocks(
            dummy_blocks,
        )
        self.assertEqual(
            len(root_loops),
            1,
        )
        root_loop = list(root_loops)[0]
        self.assertEqual(
            type(root_loop),
            Loop,
        )
        self.assertEqual(
            root_loop.header_block.index, 0,
        )
        self.assertEqual(
            [x.index for x in root_loop.body_blocks],
            [1],
        )

        self.assertEqual(
            len(child_loops),
            0,
        )

        self.assertEqual(
            [closest_loops[block] for block in dummy_blocks],
            [root_loop, root_loop, None],
        )

    def test_loop_tree_with_loop_break(self):
        from alamatic.analyser import (
            _create_loop_tree_for_blocks,
        )
        dummy_blocks = DummyBasicBlock.create_list(
            [1, 3],
            [2, 3],
            [0],
            [],
        )
        root_loops, child_loops, closest_loops = _create_loop_tree_for_blocks(
            dummy_blocks,
        )
        self.assertEqual(
            len(root_loops),
            1,
        )
        root_loop = list(root_loops)[0]
        self.assertEqual(
            root_loop.header_block.index, 0,
        )
        self.assertEqual(
            sorted([x.index for x in root_loop.body_blocks]),
            [1, 2],
        )

        self.assertEqual(
            len(child_loops),
            0,
        )

        self.assertEqual(
            [closest_loops[block] for block in dummy_blocks],
            [root_loop, root_loop, root_loop, None],
        )

    def test_loop_tree_with_loop_continue(self):
        from alamatic.analyser import (
            _create_loop_tree_for_blocks,
        )
        dummy_blocks = DummyBasicBlock.create_list(
            [1, 3],
            [2, 0],
            [0],
            [],
        )
        root_loops, child_loops, closest_loops = _create_loop_tree_for_blocks(
            dummy_blocks,
        )
        self.assertEqual(
            len(root_loops),
            1,
        )
        root_loop = list(root_loops)[0]
        self.assertEqual(
            root_loop.header_block.index, 0,
        )
        self.assertEqual(
            sorted([x.index for x in root_loop.body_blocks]),
            [1, 2],
        )

        self.assertEqual(
            len(child_loops),
            0,
        )

        self.assertEqual(
            [closest_loops[block] for block in dummy_blocks],
            [root_loop, root_loop, root_loop, None],
        )

    def test_loop_tree_with_nested_loops(self):
        from alamatic.analyser import (
            _create_loop_tree_for_blocks,
        )
        dummy_blocks = DummyBasicBlock.create_list(
            [1, 4],
            [2, 3],
            [1],
            [0],
            [],
        )
        root_loops, child_loops, closest_loops = _create_loop_tree_for_blocks(
            dummy_blocks,
        )

        self.assertEqual(
            len(root_loops),
            1,
        )
        root_loop = list(root_loops)[0]
        self.assertEqual(
            root_loop.header_block.index, 0,
        )
        self.assertEqual(
            sorted([x.index for x in root_loop.body_blocks]),
            [1, 2, 3],
        )

        self.assertEqual(
            len(child_loops),
            1,
        )
        self.assertEqual(
            child_loops.keys(),
            [root_loop],
        )
        self.assertEqual(
            len(child_loops[root_loop]),
            1,
        )
        child_loop = list(child_loops[root_loop])[0]

        self.assertEqual(
            child_loop.header_block.index, 1,
        )
        self.assertEqual(
            sorted([x.index for x in child_loop.body_blocks]),
            [2],
        )

        self.assertEqual(
            [closest_loops[block] for block in dummy_blocks],
            [root_loop, child_loop, child_loop, root_loop, None],
        )
