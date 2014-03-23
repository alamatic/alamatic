
from alamatic.util import overloadable
from alamatic.intermediate import *
from alamatic.types import *


__all__ = [
    "CBackend",
]


class CBackend(object):

    @classmethod
    def generate_code(cls, program, writer, start=None):
        self = cls()
        self.writer = writer
        self.program = program
        if start is None:
            start = program
        self.generate(start)

    @overloadable
    def generate(self, what):
        raise Exception(
            "generate not implemented for %r" % type(what)
        )

    @generate.overload(Program)
    def generate(self, program):
        self.writer.writeln("#include <stdint.h>")
        self.writer.writeln()

        # Forward-declare all the units first, to simplify matters.
        for unit in program.functions:
            self.generate(unit, forward_decl=True)

        self.writer.writeln()

        # Now generate the actual unit bodies.
        for unit in program.functions:
            self.generate(unit)
            self.writer.writeln()

    @generate.overload(Unit)
    def generate(self, unit, forward_decl=False):
        # FIXME: Return type should go in here, once we have such a concept.
        # FIXME: Parameter declarations should go in here, once they're done.
        self.writer.write("void %s()" % unit.codegen_name)
        if forward_decl:
            self.writer.writeln(";")
        else:
            with self.writer.braces():
                for block in unit.graph.blocks:
                    if block.label:
                        self.generate(block.label)
                    for instruction in block.operation_instructions:
                        self.generate(instruction)
                    self.generate(block.terminator)

    # Generation of intermediate code elements

    @generate.overload(Label)
    def generate(self, label):
        self.writer.writeln("%s: ;" % label.codegen_name)

    @generate.overload(OperationInstruction)
    def generate(self, instruction):
        self.generate(instruction.target)
        self.writer.write(" = ")
        self.generate(instruction.operation)
        self.writer.writeln(";")

    @generate.overload(JumpInstruction)
    def generate(self, instruction):
        self.writer.writeln("goto %s;" % instruction.label.codegen_name)

    @generate.overload(JumpIfFalseInstruction)
    def generate(self, instruction):
        self.writer.write("if (! ")
        self.generate(instruction.cond)
        self.writer.writeln(") goto %s;" % instruction.label.codegen_name)

    @generate.overload(JumpNeverInstruction)
    def generate(self, instruction):
        # this one's a no-op... we just fall through
        pass

    # Generation of intermediate code operations

    @generate.overload(CopyOperation)
    def generate(self, operation):
        self.generate(operation.operand)

    @generate.overload(BinaryOperation)
    def generate(self, operation):
        self.generate(operation.lhs)
        # FIXME: Need to generate real C operators here, rather than just
        # inserting our internal operation name.
        self.writer.write(" %s " % operation.operator)
        self.generate(operation.rhs)

    # Generation of intermediate code operands

    @generate.overload(SymbolOperand)
    def generate(self, operand):
        self.writer.write(operand.symbol.codegen_name)

    @generate.overload(ConstantOperand)
    def generate(self, operand):
        operand.value.generate_c_code(None, self.writer)
