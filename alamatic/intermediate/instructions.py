
from alamatic.intermediate.base import Element


class Instruction(Element):
    def generate_c_code(self, state, writer):
        writer.indent()
        self._generate_c_code(state, writer)
        writer.writeln(";")
        writer.outdent()

    def _generate_c_code(self, state, writer):
        raise Exception(
            "_generate_c_code not implemented for %r" % self
        )


class OperationInstruction(Instruction):

    def __init__(self, target, operation, position=None):
        self.target = target
        self.operation = operation
        self.position = position

    @property
    def params(self):
        yield self.target
        yield self.operation

    def replace_operands(self, replace):
        self.target = replace(self.target)
        self.operation.replace_operands(replace)

    def _generate_c_code(self, state, writer):
        self.target.generate_c_code(state, writer)
        writer.write(' = ')
        self.operation.generate_c_code(state, writer)


class JumpInstruction(Instruction):
    def __init__(self, label, position=None):
        self.label = label
        self.position = position

    @property
    def params(self):
        yield self.label

    def _generate_c_code(self, state, writer):
        writer.write("goto %s" % self.label.codegen_name)

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


class JumpIfFalseInstruction(JumpInstruction):
    def __init__(self, cond, label, position=None):
        self.cond = cond
        self.label = label
        self.position = position

    @property
    def params(self):
        yield self.cond
        yield self.label

    def _generate_c_code(self, state, writer):
        writer.write("if (! ")
        self.cond.generate_c_code(state, writer)
        writer.write(") goto %s" % self.label.codegen_name)

    def replace_operands(self, replace):
        self.cond = replace(self.cond)

    def get_optimal_equivalent(self):
        value = self.cond.constant_value
        if value is True:
            return JumpNeverInstruction()
        elif value is False:
            return JumpInstruction(
                label=self.label,
                position=self.position,
            )
        return self

    @property
    def can_fall_through(self):
        return True

    @property
    def jump_targets(self):
        return set([self.label])


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

    def generate_c_code(self, state, writer):
        # nothing to generate, since this is just a no-op
        pass

    @property
    def can_fall_through(self):
        return True

    @property
    def jump_targets(self):
        return set()


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

    def generate_c_code(self, state, writer):
        # This should never happen since this instruction is only used
        # to terminate unreachable blocks.
        raise Exception(
            "Somehow ended up generating C code for IsolateInstruction"
        )

    @property
    def can_fall_through(self):
        return False

    @property
    def jump_targets(self):
        return set()
