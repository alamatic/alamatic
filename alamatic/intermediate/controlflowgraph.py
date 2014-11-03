
from alamatic.intermediate.basicblock import BasicBlock


class ControlFlowGraph(object):
    def __init__(self):
        self.entry_block = self.create_block()
        self.exit_block = self.create_block()

    def create_block(self):
        return BasicBlock(self)
