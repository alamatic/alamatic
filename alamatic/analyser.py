
from alamatic.util import LinkedList


class BasicBlock(object):

    def __init__(self):
        self.predecessors = set()
        self.dominators = set()
        self.operations = LinkedList()
        self.label = None
        self.index = None
        self.exit_cond = None
        self.true_successor = None
        self.false_successor = None
        self.closest_loop = None

    @property
    def successor_is_conditional(self):
        return self.true_successor is not self.false_successor

    @property
    def is_loop_header(self):
        for pred_block in self.predecessors:
            if pred_block.index > self.index:
                return True
        return False


class Loop(object):

    def __init__(self):
        self.header_block = None
        self.body_blocks = set()
        self.parent_loop = None
        self.child_loops = set()


class ControlFlowGraph(object):

    def __init__(self):
        self.entry_block = None
        self.exit_block = None
        self.blocks = None
        self.blocks_by_label = None
        self.root_loops = None


def build_control_flow_graph(elems):
    from alamatic.intermediate import (
        Label,
        JumpOperation,
        JumpIfFalseOperation,
        ConstantOperand,
    )
    from alamatic.types import (
        Bool,
    )

    blocks_by_label = {}
    blocks = []

    entry_block = BasicBlock()
    exit_block = BasicBlock()

    current = entry_block

    blocks.append(entry_block)

    # Pass 1: split sequence of elements into blocks
    for elem in elems:
        if isinstance(elem, Label):
            current = BasicBlock()
            current.label = elem
            blocks_by_label[elem] = current
            blocks.append(current)
        elif isinstance(elem, JumpOperation):
            if isinstance(elem, JumpIfFalseOperation):
                current.exit_cond = elem.cond
                # for the moment the successor will be a label instance,
                # until we've built the full set of basic blocks and then
                # we'll rewrite it to be a block on the second pass.
                current.false_successor = elem.label
            else:
                current.true_successor = elem.label
                current.false_successor = elem.label
            current = BasicBlock()
            blocks.append(current)
        else:
            current.operations.append(elem)

    blocks.append(exit_block)

    # Pass 2: Assign successors to blocks
    previous = None
    for current in blocks:
        if previous is not None:
            if previous.true_successor is None:
                previous.true_successor = current
            elif isinstance(previous.true_successor, Label):
                # in our first pass above we wrote labels in here but
                # now we know enough to replace them with actual block
                # instances.
                previous.true_successor = blocks_by_label[
                    previous.true_successor
                ]
            if previous.false_successor is None:
                previous.false_successor = current
            elif isinstance(previous.false_successor, Label):
                # in our first pass above we wrote labels in here but
                # now we know enough to replace them with actual block
                # instances.
                previous.false_successor = blocks_by_label[
                    previous.false_successor
                ]
            if previous.true_successor is previous.false_successor:
                previous.exit_cond = ConstantOperand(
                    Bool(True),
                )
        previous = current

    # Pass 3: Assign predecessors
    for block in blocks:
        if block.true_successor is not None:
            block.true_successor.predecessors.add(block)
        if block.false_successor is not None:
            block.false_successor.predecessors.add(block)

    # Pass 4: filter out junk blocks created by jumps immediately followed by
    # labels, so that entry is the only block without a predecessor.
    blocks = [
        x for x in blocks if x is entry_block or len(x.predecessors) > 0
    ]
    for block in blocks:
        block.predecessors.intersection_update(blocks)

    # Pass 5: Assign indices
    for i, block in enumerate(blocks):
        block.index = i

    # Pass 6: Find dominators
    for block in blocks:
        if block is entry_block:
            block.dominators.add(block)
        else:
            block.dominators.update(blocks)
    changes = True
    while changes:
        changes = False
        for block in blocks[1:]:
            doms = set()
            for pred in block.predecessors:
                if len(doms) > 0:
                    doms.intersection_update(pred.dominators)
                else:
                    doms.update(pred.dominators)
            doms.add(block)
            if doms != block.dominators:
                block.dominators = doms
                changes = True

    graph = ControlFlowGraph()
    graph.blocks = blocks
    graph.blocks_by_label = blocks_by_label
    graph.entry_block = entry_block
    graph.exit_block = exit_block

    # Pass 7: Find loops
    graph.root_loops = set()
    for header_block in blocks:
        if header_block.is_loop_header:
            loop = Loop()

            # If this block is already in a loop then we've found
            # a nested loop, so turn the existing loop into the parent loop
            if block.closest_loop is not None:
                loop.parent_loop = block.closest_loop
                block.closest_loop.child_loops.add(loop)

            block.closest_loop = loop
            loop.header_block = header_block

            # For each incoming back edge, find the maximal set of blocks
            # that participate in the loop.
            for pred_block in header_block.predecessors:
                if header_block not in pred_block.dominators:
                    continue
                body_blocks = set([pred_block, header_block])
                stack = [pred_block]
                while len(stack) > 0:
                    current_block = stack.pop()
                    for current_block_pred in current_block.predecessors:
                        if current_block_pred not in body_blocks:
                            body_blocks.add(current_block_pred)
                            stack.append(current_block_pred)
                loop.body_blocks.update(body_blocks)

            if loop.parent_loop is None:
                graph.root_loops.add(loop)

    return graph
