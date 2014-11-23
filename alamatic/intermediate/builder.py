
from alamatic.intermediate.instructions import instruction_types
from alamatic.intermediate.controlflowgraph import ControlFlowGraph
import alamatic.intermediate.operands as operands


__all__ = ['Builder']


class BuilderBase(object):

    def __init__(self):
        self.graph = ControlFlowGraph()
        self.entry_block = self.graph.entry_block
        self.exit_block = self.graph.exit_block
        self.next_temporary_index = 0

        # First we terminate the exit block to ensure nothing
        # inadvertently gets added to it.
        self.current_block = self.exit_block
        self.end(None)

        # Now callers will start by adding to the entry block.
        self.current_block = self.entry_block

    def create_literal(self, value, source_range=None):
        return operands.LiteralValue(value, source_range=source_range)

    def create_temporary(self, source_range=None):
        index = self.next_temporary_index
        self.next_temporary_index += 1
        return operands.Temporary(index, source_range=source_range)

    def create_named_constant(self, symbol, source_range=None):
        return operands.NamedConstant(symbol)

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
