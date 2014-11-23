
from alamatic.intermediate.instructions import instruction_types
from alamatic.intermediate.controlflowgraph import ControlFlowGraph


__all__ = ['Builder']


class BuilderBase(object):

    def __init__(self):
        self.graph = ControlFlowGraph()
        self.entry_block = self.graph.entry_block
        self.exit_block = self.graph.exit_block

        # First we terminate the exit block to ensure nothing
        # inadvertently gets added to it.
        self.current_block = self.exit_block
        self.end(None)

        # Now callers will start by adding to the entry block.
        self.current_block = self.entry_block

    def create_temporary(self):
        pass

    def set_current_block(self, block):
        self.current_block = block

    def create_block(self):
        return self.graph.create_block()


def make_instr_builder(instr_type):
    def instr_builder(self, source_range, **kwargs):
        if self.current_block.terminator is not None:
            raise Exception("Block is terminated; can't add instructions")

        target = None
        if instr_type.is_operation:
            target = self.create_temporary()
            kwargs["target"] = target

        instr = instr_type(**kwargs)
        instr.source_range = source_range

        if instr.is_terminator:
            self.current_block.terminator = instr
        else:
            self.current_block.body_instrs.append(instr)

        return target

    instr_builder.__name__ = instr_type.mnemonic
    return instr_builder


def init():
    builder_dict = {
        instr_type.mnemonic: make_instr_builder(instr_type)
        for instr_type in instruction_types
    }

    global Builder
    Builder = type('Builder', (BuilderBase,), builder_dict)


init()
