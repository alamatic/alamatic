
from alamatic.intermediate.base import Element


class Instruction(Element):
    pass


class OperationInstruction(Instruction):

    def __init__(self, target, operation, source_range=None):
        self.target = target
        self.operation = operation
        self.source_range = source_range

    @property
    def params(self):
        yield self.target
        yield self.operation

    def replace_operands(self, replace):
        self.target = replace(self.target)
        self.operation.replace_operands(replace)


class JumpInstruction(Instruction):
    def __init__(self, label, source_range=None):
        self.label = label
        self.source_range = source_range

    @property
    def params(self):
        yield self.label

    def replace_operands(self, replace):
        pass

    def get_optimal_equivalent(self):
        # Must return exactly self if we intend to make no change,
        # since callers will depend on this to recognize if any
        # change has been made.
        return self

    @property
    def can_fall_through(self):
        return False

    @property
    def jump_targets(self):
        return set([self.label])

    def build_llvm_terminator(self, builder, ft_block, label_blocks):
        return builder.instrs.branch(label_blocks[self.label])


class JumpIfFalseInstruction(JumpInstruction):
    def __init__(self, cond, label, source_range=None):
        self.cond = cond
        self.label = label
        self.source_range = source_range

    @property
    def params(self):
        yield self.cond
        yield self.label

    def replace_operands(self, replace):
        self.cond = replace(self.cond)

    def get_optimal_equivalent(self):
        value = self.cond.constant_value
        if value is True:
            return JumpNeverInstruction()
        elif value is False:
            return JumpInstruction(
                label=self.label,
                source_range=self.source_range,
            )
        return self

    @property
    def can_fall_through(self):
        return True

    @property
    def jump_targets(self):
        return set([self.label])

    def build_llvm_terminator(self, builder, ft_block, label_blocks):
        cond_value = self.cond.build_llvm_value(builder)
        return builder.instrs.cbranch(
            cond_value,
            ft_block,
            label_blocks[self.label],
        )


# This is not a "real" operation that should show up during code generation,
# but is used by the code analyzer to ensure that all basic blocks have
# a terminator, even if a particular block does not end with an explicit jump
# in the original IR.
class JumpNeverInstruction(JumpInstruction):
    def __init__(self):
        pass

    @property
    def params(self):
        return []

    @property
    def can_fall_through(self):
        return True

    @property
    def jump_targets(self):
        return set()

    def build_llvm_terminator(self, builder, ft_block, label_blocks):
        return builder.instrs.branch(ft_block)


# This is not a "real" operation that should show up during code generation,
# but is used by the code analyzer when it detects an unreachable basic block,
# to mark that block as having no successors and thus effectively disconnecting
# it from the graph altogether.
class IsolateInstruction(JumpInstruction):

    def __init__(self):
        pass

    @property
    def params(self):
        return []

    @property
    def can_fall_through(self):
        return False

    @property
    def jump_targets(self):
        return set()
