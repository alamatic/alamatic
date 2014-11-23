
from alamatic.intermediate.basicblock import BasicBlock


class ControlFlowGraph(object):
    def __init__(self):
        self.entry_block = self.create_block()
        self.exit_block = self.create_block()

    def create_block(self):
        return BasicBlock(self)

    @property
    def blocks(self):
        """
        Iterable of all blocks reachable from the entry block.
        """
        # Keep track of what we've already emitted so we don't return
        # the same block twice if there's a loop or diamond.
        blocks_emitted = set()

        # Keep track of blocks that are targets of jumps we've encountered
        # so we can emit them in a sensible order.
        block_stack = []

        current_block = self.entry_block
        while True:
            if current_block not in blocks_emitted:
                yield current_block

            blocks_emitted.add(current_block)

            terminator = current_block.terminator
            assert terminator is not None

            block_stack.extend(reversed(list(terminator.successor_blocks)))

            if len(block_stack) > 0:
                current_block = block_stack.pop()
            else:
                break
