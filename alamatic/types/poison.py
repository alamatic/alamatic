
from alamatic.types.base import Type
import alamatic.diagnostics as diag
import llvm.core


__all__ = ["Poison"]


# Doesn't really matter what this type is, since we'll never actually
# produce a final program containing poisons... just want this here to
# complete the interface.
llvm_type = llvm.core.Type.struct([])


class PoisonType(Type):
    """
    A special type used to propagate an error state.

    When analysis reveals that a given operation is in error, it is considered
    to return the poison value, which is the single value of this type.

    When operations receive the poison value as an operand they automatically
    themselves yield the poison value, thus causing the poison to spread to
    all operations that depend on the errored operation.

    When the poison value or type is encountered during post-analysis checking
    it suppresses diagnostics relating to the poisoned operations, which is
    intended to avoid producing a sea of downstream diagnostics that would
    usually obscure the original error.

    There is no way to explicitly access the poison value or type within the
    language, since it is just an implementation detail of the analysis step.
    """

    def __init__(self):
        self.llvm_type = llvm_type

    def repr_for_data(self, data):
        return "Poison"


Poison = PoisonType()(llvm.core.Constant.undef(llvm_type))
