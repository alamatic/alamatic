
from alamatic.types.base import Type
import alamatic.diagnostics as diag
import llvm.core


__all__ = []


class IntegerType(Type):

    def __init__(self, bits, signed):
        self.bits = bits
        self.signed = signed
        self.llvm_type = llvm.core.Type.int(bits)

    def add(self, builder, lhs, rhs, source_range=None):
        if lhs.type is not rhs.type:
            raise diag.InvalidAddOperands(
                lhs_type=lhs.type,
                rhs_type=rhs.type,
                source_range=source_range,
            )

        return self(builder.add(lhs.data, rhs.data))


for bits in (8, 16, 32, 64):
    for signed in (True, False):
        name = "%sInt%i" % (
            "" if signed else "U",
            bits,
        )
        __all__.append(name)
        globals()[name] = IntegerType(bits, signed)
