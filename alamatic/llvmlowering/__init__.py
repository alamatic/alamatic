
from llvm.core import (
    Module as LLVMModule,
    Type as LLVMType,
    Constant as LLVMConstant,
)
from alamatic.llvmlowering.function import make_llvm_function


__all__ = [
    "make_llvm_module",
]


def make_llvm_module(program):
    module = LLVMModule.new('alamatic_entry')
    llvm_entry_func = make_llvm_function(module, program.entry_func)

    for variable in program.global_variables:
        # TODO: Use the results of the analysis passes to determine the
        # actual type of each variable.
        # FIXME: Do we have a chicken-and-egg problem here? Need to
        # generate the global variables before we reference them, but
        # we need to lower all called functions (which may reference the
        # globals) before we can fully analyze the entry function. Will
        # probably need to generate these as we go along rather than waiting
        # until the main LLVM function is lowered.
        var_type = LLVMType.int(8)
        var_ptr = module.add_global_variable(var_type, variable.codegen_name)
        # TODO: Generate constant initializer where possible
        var_ptr.initializer = LLVMConstant.null(var_type)

    # TODO: Generate a stub 'main' function that initializes complex globals
    # and calls into the entry function.

    return module
