
from alamatic.types.base import Type
import llvm.core


__all__ = []


class IntegerType(Type):

    def __init__(self, bits, signed):
        self.bits = bits
        self.signed = signed
        self.llvm_type = llvm.core.Type.int(bits)


for bits in (8, 16, 32, 64):
    for signed in (True, False):
        name = "%sInt%i" % (
            "" if signed else "U",
            bits,
        )
        __all__.append(name)
        globals()[name] = IntegerType(bits, signed)
