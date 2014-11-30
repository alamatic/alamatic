
from llvm.core import (
    Type as LLVMType,
    Builder as LLVMBuilder,
)


def make_llvm_function(module, function):

    # TODO: Compute a suitable type for the function based on its
    # arguments and return/error types.
    func_type = LLVMType.function(LLVMType.void(), [])
    func_name = "ALA_%08x" % id(function)
    llvm_function = module.add_function(func_type, func_name)

    # TODO: Run the analysis passes to collect information about:
    # - the types of all variables
    # - the types and values of all constants
    # - which blocks can never be reached as a result of constant conditionals
    # - any semantic errors in the program

    setup_block = llvm_function.append_basic_block("setup")
    setup_builder = LLVMBuilder.new(setup_block)

    for variable in function.local_variables:
        # TODO: Use the results of the analysis passes to determine
        # the actual type of each variable.
        var_type = LLVMType.int(8)
        var_ptr = setup_builder.alloca(var_type)

    # TODO: Actually generate the rest of the basic blocks
    # For now, we just terminate the setup block to make sure
    # our IR is valid.
    setup_builder.ret_void()

    return llvm_function
