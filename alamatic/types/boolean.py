
from alamatic.types import (
    TypeImplementation,
    OperationImplementation,
)

__all__ = [
    "Bool",
]


class BoolImpl(TypeImplementation):

    def __init__(self):
        super(BoolImpl, self).__init__("Bool")

    def get_llvm_type(self, Type):
        return Type.int(1)


# Singleton implementation
impl = BoolImpl()

# Singleton instance
Bool = impl.make_no_arg_type()
