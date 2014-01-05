
from alamatic.util import LinkedList
from collections import defaultdict


class BasicBlock(object):
    """
    Represents a series of IR operations with only one entry point and one
    exit point.

    A basic block is what results from slicing up a sequence of IR elements
    on labels and jump operations. Each slice becomes a basic block.

    Most attributes of basic blocks return correct results only once the
    construction of the related :py:class:`ControlFlowGraph` is complete,
    since they rely on contextual information that is maintained within
    the graph object.
    """

    def __init__(self, cfg, label, operations, terminator, next_block):
        from alamatic.intermediate import JumpNeverInstruction
        if terminator is None:
            terminator = JumpNeverInstruction()

        self._cfg = cfg
        self.seq_id = cfg._allocate_block_sequence_id()
        self._label = label
        self._operations = operations
        self._terminator = terminator
        self._next_block = next_block

    @property
    def cfg(self):
        return self._cfg

    @property
    def label(self):
        return self._label

    @property
    def operations(self):
        return self._operations

    @property
    def terminator(self):
        # TODO: Allow this to be assigned, after which we will need to
        # update the predecessor map and the dominator map inside the CFG.
        return self._terminator

    @property
    def next_block(self):
        return self._next_block

    @property
    def successors(self):
        ret = set()
        ret.update(
            self.jump_successors
        )
        fall_through = self.fall_through_successor
        if fall_through is not None:
            ret.add(fall_through)
        return frozenset(ret)

    @property
    def fall_through_successor(self):
        if self.terminator.can_fall_through:
            # self.next_block might still be None if this is the exit block.
            return self.next_block
        else:
            return None

    @property
    def jump_successors(self):
        return set(
            self._cfg.get_block_by_label(label)
            for label in self.terminator.jump_targets
        )

    @property
    def predecessors(self):
        return self._cfg._get_predecessors_for_block(self)

    @property
    def dominators(self):
        return self._cfg._get_dominators_for_block(self)

    @property
    def closest_loop(self):
        return self._cfg._get_closest_loop_for_block(self)

    @property
    def is_loop_header(self):
        # A block is a loop header if it dominates any of its own
        # predecessors.
        for pred_block in self.predecessors:
            if self in pred_block.dominators:
                return True
        return False


class Loop(object):

    def __init__(
        self,
        cfg,
        preheader_block,
        header_block,
        body_blocks,
        parent_loop=None
    ):
        self._cfg = cfg
        self._preheader_block = preheader_block
        self._header_block = header_block
        self._body_blocks = body_blocks
        self._parent_loop = parent_loop

    @property
    def cfg(self):
        return self._cfg

    @property
    def preheader_block(self):
        return self._preheader_block

    @property
    def header_block(self):
        return self._header_block

    @property
    def body_blocks(self):
        return self._body_blocks

    @property
    def blocks(self):
        return set([
            self.preheader_block,
            self.header_block,
        ]).update(self.body_blocks)

    @property
    def parent_loop(self):
        return self._parent_loop

    @property
    def child_loops(self):
        return self._cfg._get_child_loops_for_loop(self)


class ControlFlowGraph(object):

    def __init__(self, elems):
        self.last_block_sequence_id = 0

        entry_block, exit_block, blocks_by_label = _split_elems_into_blocks(
            elems, self,
        )
        self._entry_block = entry_block
        self._exit_block = exit_block
        self._blocks_by_label = blocks_by_label

        # After this point we're initialized enough that we can call
        # into the 'blocks' property to traverse a flattened block graph.
        # We'll traverse this set of blocks a few times here, so we'll
        # cache the result to avoid repeating this graph traversal since
        # we know we're not going to reshape the graph during this process.
        initial_blocks = list(self.blocks)

        # Initialize the predecessor map. This will get maintained piecemeal
        # on subsequent changes to any block's terminator.
        self._block_predecessors = _create_initial_predecessor_map_for_blocks(
            initial_blocks,
        )

        # After this point we're initialized enough that we can use the
        # 'predecessors' property on our block objects.

        # Initialize the dominator map. Currently we recompute this each time
        # we update the predecessor map, though it would be nice to support
        # partial updates of this map later.
        self._block_dominators = _create_dominator_map_for_blocks(
            initial_blocks,
        )

        # After this point we're initialized enough that we can use the
        # 'dominators' property on our block objects.

        # Initialize the loop information. Currently we are unable to update
        # this information as the graph changes, but that will be necessary
        # later in order to support loop unrolling and constant propagation.
        root_loops, child_loops, closest_loops = _create_loop_tree_for_blocks(
            initial_blocks,
        )
        self._root_loops = root_loops
        self._child_loops = child_loops
        self._closest_loops = closest_loops

        # TODO: Need to add preheader blocks to all of the loops before we can
        # support loop unrolling, but we can't do that until we support
        # partial updates of the loop information.

    @property
    def entry_block(self):
        return self._entry_block

    @property
    def exit_block(self):
        return self._exit_block

    @property
    def blocks(self):
        """
        Iterable providing a linear traversal of this graph's blocks.

        Guarantees that chains of "fall through" blocks will be
        returned together and jumps will be returned in a deterministic
        fashion based on the order in which the blocks were instantiated
        into the graph. Unreachable blocks will not be included.
        """
        for block in _flatten_block_graph(self.entry_block):
            yield block

    @property
    def root_loops(self):
        return frozenset(self._root_loops)

    def get_block_by_label(self, label):
        return self._blocks_by_label[label]

    def _get_predecessors_for_block(self, block):
        return frozenset(self._block_predecessors[block])

    def _get_dominators_for_block(self, block):
        return frozenset(self._block_dominators[block])

    def _get_closest_loop_for_block(self, block):
        return self._closest_loops[block]

    def _get_child_loops_for_loop(self, loop):
        return frozenset(self._child_loops[loop])

    def _allocate_block_sequence_id(self):
        # Block sequence ids are just incrementing integers that
        # allow us to keep track of the order of instantiation of
        # basic blocks so that we can provide a stable (but otherwise
        # largely meaningless) ordering of them when needed.
        self.last_block_sequence_id += 1
        return self.last_block_sequence_id


def _split_elems_into_blocks(elems, cfg):
    from alamatic.intermediate import (
        Label,
        JumpInstruction,
    )
    exit_block = BasicBlock(
        cfg=cfg,
        label=None,
        operations=[],
        terminator=None,
        next_block=None,
    )
    entry_block = BasicBlock(
        cfg=cfg,
        label=None,
        operations=[],
        terminator=None,
        next_block=exit_block,
    )
    blocks_by_label = {}

    class BasicBlockBuilder(object):
        def __init__(self):
            self.reset()
            self.previous = entry_block

        def reset(self):
            self.operations = []
            self.label = None
            self.terminator = None

        def commit(self):
            new = BasicBlock(
                cfg=cfg,
                label=self.label,
                operations=self.operations,
                terminator=self.terminator,
                # all blocks start off pointing at the exit block but a
                # subsequent commit will update this, ensuring that only
                # the final body block falls through to the exit block.
                next_block=exit_block,
            )
            if self.label is not None:
                blocks_by_label[self.label] = new
            # We use the internal _next_block attribute directly here because
            # we do basic block splitting before we've done
            # predecessor/dominator analysis and so the side-effects of the
            # public property setter are undesirable.
            self.previous._next_block = new
            self.reset()
            self.previous = new

    builder = BasicBlockBuilder()

    for elem in elems:
        if isinstance(elem, Label):
            builder.commit()
            builder.label = elem
        elif isinstance(elem, JumpInstruction):
            builder.terminator = elem
            builder.commit()
        else:
            builder.operations.append(elem)

    # Need to commit one more time to finish the final block
    builder.commit()

    return (entry_block, exit_block, blocks_by_label)


def _flatten_block_graph(entry_block):
    # Keep track of what we've already seen so we won't return the
    # same block twice if there's a loop or diamond.
    blocks_seen = set()
    # Keep track of blocks that are targets of jumps we've encountered,
    # so we can be sure to include them, and do so in a sensible order.
    # Unreachable blocks will never get added to this stack, and so will
    # be skipped in this traversal.
    jump_target_stack = []

    current_block = entry_block
    while current_block is not None:

        # If there is a loop or diamond in the graph then we'll enqueue
        # the same jump target twice, so we'll just skip it then.
        if current_block not in blocks_seen:
            yield current_block

        blocks_seen.add(current_block)

        jump_target_stack.extend(
            sorted(
                [
                    x for x in current_block.jump_successors
                    if x not in blocks_seen
                ],
                key=lambda x: x.seq_id,
                reverse=True,
            )
        )

        current_block = current_block.fall_through_successor

        # If our block can't fall through anywhere, then process an item
        # from our jump target stack instead.
        if current_block is None and len(jump_target_stack) > 0:
            current_block = jump_target_stack.pop()


def _create_initial_predecessor_map_for_blocks(blocks):
    # Given an iterable of basic blocks, produce a new mapping from each block
    # object to a set of its predecessor blocks.
    predecessors = defaultdict(lambda: set())
    for current_block in blocks:
        for successor_block in current_block.successors:
            predecessors[successor_block].add(current_block)
    return predecessors


def _create_dominator_map_for_blocks(blocks):
    # Given an iterable of blocks that belong to a control flow graph that
    # already has its predecessor map populated, produce a new mapping from
    # each block object to a set of its dominator blocks.

    dominators = defaultdict(lambda: set())

    # We start by saying that every block except the entry block is
    # dominated by the full set of blocks. We will then progressively
    # remove items from these lists until the structure stabilizes.
    for block in blocks:
        current_dominators = dominators[block]
        if block is block.cfg.entry_block:
            current_dominators.add(block)
        else:
            current_dominators.update(blocks)

    current_dominators = None

    # Now we'll just keep passing over the list and eliminating incorrect
    # edges until we managed to do one pass without changing anything.
    changes = True
    while changes:
        changes = False
        for block in blocks[1:]:
            new_dominators = set()
            prev_dominators = dominators[block]
            for pred in block.predecessors:
                pred_dominators = dominators[pred]
                if len(new_dominators) > 0:
                    new_dominators.intersection_update(
                        pred_dominators,
                    )
                else:
                    new_dominators.update(
                        pred_dominators,
                    )
            new_dominators.add(block)
            if new_dominators != prev_dominators:
                dominators[block] = new_dominators
                changes = True

    return dominators


def _create_loop_tree_for_blocks(blocks):
    # Given an iterable of blocks that belong to a control flow graph that
    # already has its predecessor and dominator maps populated, produce a
    # tree structure of all of the loops indicated in the blocks and return a
    # tuple containing:
    # - a set of the root loops from the tree
    # - a mapping from each loop to a set of its child loops
    # - a mapping from each block to its closest loop, if any
    root_loops = set()
    child_loops = defaultdict(lambda: set())
    closest_loops = defaultdict(lambda: None)

    for header_block in blocks:

        # It might not actually be a header, since we're visiting every block.
        if not header_block.is_loop_header:
            continue

        parent_loop = closest_loops[header_block]
        body_blocks = set()

        for pred_block in header_block.predecessors:
            if header_block not in pred_block.dominators:
                continue

            local_body_blocks = set([pred_block, header_block])
            block_stack = [pred_block]
            while len(block_stack) > 0:
                current_block = block_stack.pop()
                for current_block_pred in current_block.predecessors:
                    if current_block_pred not in local_body_blocks:
                        local_body_blocks.add(current_block_pred)
                        block_stack.append(current_block_pred)

            body_blocks.update(local_body_blocks)

        # We don't actually want the header block in our set of body blocks.
        body_blocks.discard(header_block)

        loop = Loop(
            cfg=header_block.cfg,
            preheader_block=None,  # must be created and populated by a
                                   # separate pass, since we can't modify the
                                   # graph here.
            header_block=header_block,
            body_blocks=body_blocks,
            parent_loop=parent_loop,
        )

        # Update our idea of the "closest loop" of each block we just
        # added. Due to the guaranteed block traversal order we know we'll
        # always visit parent blocks before their child blocks, so it's
        # safe to assign these here and assume that some body blocks will get
        # updated on a subsequent iteration if we encounter a nested block.
        closest_loops[header_block] = loop
        for body_block in body_blocks:
            closest_loops[body_block] = loop

        if parent_loop is None:
            root_loops.add(loop)
        else:
            child_loops[parent_loop].add(loop)

    return (root_loops, child_loops, closest_loops)


def build_control_flow_graph(elems):
    return ControlFlowGraph(elems)
