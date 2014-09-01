
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


# Singleton implementation
impl = BoolImpl()

# Singleton instance
Bool = impl.make_no_arg_type()
