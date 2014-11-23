
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


class DiagnosticInstr(Instruction):
    """
    Special instruction type that will, when encountered during the check
    phase, cause the driver to emit a diagnostic and possibly, depending on
    the concrete instruction type, fail compilation.
    """

    def __init__(self, diagnostic):
        self.diagnostic = diagnostic

    @property
    def args(self):
        yield self.diagnostic


class TerminatorInstr(Instruction):
    is_terminator = True

    @property
    def successor_blocks(self):
        if False:
            yield None


class OperationInstr(Instruction):
    is_operation = True


class ReturnInstr(TerminatorInstr):
    pass


class UnconditionalJumpInstr(TerminatorInstr):

    def __init__(self, target_block):
        self.target_block = target_block

    @property
    def args(self):
        yield self.target_block

    @property
    def successor_blocks(self):
        yield self.target_block


class ConditionalJumpInstr(TerminatorInstr):

    def __init__(self, cond_value, true_block, false_block):
        self.cond_value = cond_value
        self.true_block = true_block
        self.false_block = false_block

    @property
    def args(self):
        yield self.cond_value
        yield self.true_block
        yield self.false_block

    @property
    def successor_blocks(self):
        yield self.true_block
        yield self.false_block


class SwitchInstr(TerminatorInstr):
    pass


class MemoryLoadInstr(Instruction):
    is_operation = True

    def __init__(self, location, target):
        self.location = location
        self.target = target

    @property
    def args(self):
        yield self.location
        yield self.target


class MemoryStoreInstr(Instruction):

    def __init__(self, location, source):
        self.location = location
        self.source = source

    @property
    def args(self):
        yield self.source
        yield self.location


class LoadAttributeInstr(MemoryLoadInstr):
    is_operation = True


class StoreAttributeInstr(MemoryStoreInstr):
    pass


class StoreItemInstr(MemoryStoreInstr):
    pass


class BinaryInstr(OperationInstr):
    def __init__(self, target, lhs, rhs):
        self.target = target
        self.lhs = lhs
        self.rhs = rhs

    @property
    def args(self):
        yield self.lhs
        yield self.rhs
        yield self.target


class UnaryInstr(OperationInstr):
    pass


class SelectInstr(OperationInstr):
    pass


class CallInstr(OperationInstr):
    pass


class PoisonInstr(OperationInstr):

    def __init__(self, target):
        self.target = target

    @property
    def args(self):
        yield self.target
