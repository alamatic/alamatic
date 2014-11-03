
class Instruction(object):
    is_terminator = False
    is_operation = False
    mnemonic = None
    source_range = None

    @classmethod
    def concrete_type(cls, mnemonic):
        type_dict = {
            "mnemonic": mnemonic
        }
        return type(mnemonic, (cls,), type_dict)

    @property
    def args(self):
        if False:
            yield None

    def __repr__(self):
        if self.is_operation:
            args = list(self.args)
            return "<%s = %s %s>" % (
                args[0],
                self.mnemonic,
                ', '.join(str(x) for x in args[1:]),
            )
        else:
            return "<%s %s>" % (
                self.mnemonic,
                ', '.join(str(x) for x in self.args),
            )


class TerminatorInstr(Instruction):
    is_terminator = True


class OperationInstr(Instruction):
    is_operation = True


class ReturnInstr(TerminatorInstr):
    pass


class UnconditionalJumpInstr(TerminatorInstr):
    pass


class ConditionalJumpInstr(TerminatorInstr):
    pass


class SwitchInstr(TerminatorInstr):
    pass


class MemoryInstr(Instruction):
    pass


class LoadInstr(MemoryInstr):
    is_operation = True


class LoadAttributeInstr(MemoryInstr):
    is_operation = True


class StoreAttributeInstr(MemoryInstr):
    pass


class StoreItemInstr(MemoryInstr):
    pass


class BinaryInstr(OperationInstr):
    def __init__(self, target, lhs, rhs):
        self.target = target
        self.lhs = lhs
        self.rhs = rhs

    @property
    def args(self):
        yield self.target
        yield self.lhs
        yield self.rhs


class UnaryInstr(OperationInstr):
    pass


class SelectInstr(OperationInstr):
    pass


class CallInstr(OperationInstr):
    pass
