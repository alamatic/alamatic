
import ctypes

from alamatic.types import (
    TypeImplementation,
    OperationImplementation,
)
from alamatic.intermediate import Unknown


__all__ = [
    "FunctionTemplate",
]


class CallImplementation(OperationImplementation):

    def get_result_type(self, callee, args, kwargs):
        return Unknown

    def build_llvm_value(self, builder, callee, args, kwargs):
        # FIXME: If we ever actually end up calling a FunctionTemplate
        # in native code then there is a bug in the checker, since these
        # should all have been replaced with a concrete function by the
        # preprocessor by the time we get to generating LLVM IR.
        # But for now, while we don't have a fully-functional preprocessor or
        # checker, we will return something here.
        return builder.consts.int(builder.types.int(8), 0xdeadbeef)


class FunctionTemplateImpl(TypeImplementation):

    def __init__(self):
        super(FunctionTemplateImpl, self).__init__("FunctionTemplate")

    def get_llvm_type(self, types):
        # This is standing in for a pointer to a PyObject, since we just
        # consider PyObject to be an opaque structure and so we'll never
        # actually dereference these pointers within generated code.
        return types.pointer(types.int(8))

    def get_llvm_constant(self, builder, value):
        # TRICKERY: We depend on the id() function returning the address
        # of the PyObject representing value, and turn that into an LLVM
        # pointer that will remain valid as long as 'value' stays alive.
        # It will stay alive as long as it's referred to by an operation,
        # This (along with all of the other shenanigans we do with passing
        # Python objects through LLVM) tethers us to the CPython implementation
        # of Python.
        addr = id(value)
        # See how wide an int we need to use to convert to a pointer on
        # this platform. (We only ever deal with function templates at
        # compile time, so this is always the size on the host machine.
        addr_size = ctypes.sizeof(ctypes.POINTER(ctypes.c_int))

        return builder.consts.int(
            builder.types.int(addr_size * 8), addr,
        ).inttoptr(
            self.get_llvm_type(builder.types)
        )

    call = CallImplementation()


FunctionTemplate = FunctionTemplateImpl().make_no_arg_type()
