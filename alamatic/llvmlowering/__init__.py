
from llvm.core import Module
from alamatic.llvmlowering.function import make_llvm_function


__all__ = [
    "make_llvm_module",
]


def make_llvm_module(entry_func):
    module = Module.new('alamatic_entry')
    llvm_entry_func = make_llvm_function(module, entry_func)

    # TODO: Generate a stub 'main' function that sets up the environment
    # and calls into the entry function.

    return module
