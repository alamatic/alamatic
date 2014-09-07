
import llvm.core
from llvm.core import (
    Module as LLVMModule,
    Type as LLVMType,
    Builder as LLVMBuilder,
    Constant as LLVMConstant,
)

from alamatic.intermediate import (
    NamedSymbol,
    TemporarySymbol,
)
from alamatic.context import new_context


__all__ = [
    "module_for_cfg",
]


def llvm_module_for_program(program):
    # FIXME: For no this only generates the code for the entry task
    entry_task = program.entry_task
    graph = entry_task.graph
    symbols = entry_task.symbols
    module = LLVMModule.new("tmpprog")

    func_type = LLVMType.function(LLVMType.void(), [])
    func = module.add_function(func_type, 'tmp')

    preamble = func.append_basic_block("preamble")
    preamble_builder = LLVMBuilder.new(preamble)
    llvm_entry_block = None

    symbol_values = {}

    for symbol in symbols.all_symbols:
        if not symbol.is_temporary:
            symbol_values[symbol] = preamble_builder.alloca(
                symbol.type.impl.get_llvm_type(LLVMType)
            )

    next_anon_block_id = 1

    with new_context(symbol_llvm_values=symbol_values):
        llvm_blocks = {}
        # First allocate all of the blocks so we can easily
        # create branches between them.
        for block in graph.blocks:
            if block.label:
                block_name = block.label.codegen_name
            else:
                block_name = "_anon_%i" % next_anon_block_id
                next_anon_block_id += 1

            llvm_block = func.append_basic_block(block_name)

            if llvm_entry_block is None:
                llvm_entry_block = llvm_block
                preamble_builder.branch(llvm_entry_block)

            llvm_blocks[block] = llvm_block

        for block in graph.blocks:
            llvm_block = llvm_blocks[block]

            llvm_builder = LLVMBuilder.new(llvm_block)
            builder = Builder(llvm_builder)

            for instr in block.operation_instructions:
                operation = instr.operation
                llvm_value = operation.build_llvm_value(builder)
                if llvm_value is None:
                    raise Exception(
                        "%r produced no value" % operation
                    )
                target = instr.target
                llvm_store_ptr = target.build_llvm_store_ptr(builder)
                if llvm_store_ptr is None:
                    # Target is assumed to be a SymbolOperand with a
                    # temporary symbol.
                    symbol_values[target.symbol] = llvm_value
                else:
                    builder.instrs.store(llvm_value, llvm_store_ptr)

            if block is graph.exit_block:
                builder.instrs.ret_void()
            else:
                terminator = block.terminator
                terminator.build_llvm_terminator(
                    builder,
                    (
                        llvm_blocks[block.fall_through_successor]
                        if block.fall_through_successor else None
                    ),
                    {
                        jump_block.label: llvm_blocks[jump_block]
                        for jump_block in block.jump_successors
                    }
                )

    return module


# Extract from llvm.core some useful constants and bucket them inside
# wrapper objects so they don't pollute our global namespace.
def make_llvm_enums():
    tables = {
        "ATTR": ('LLVMAttr', {}),
        "ICMP": ('LLVMICMP', {}),
        "FCMP": ('LLVMFCMP', {}),
        "LINKAGE": ('LLVMLinkage', {}),
        "VISIBILITY": ('LLVMVisibility', {}),
        "CC": ('LLVMCallingConvention', {}),
    }

    for full_name in dir(llvm.core):
        if "_" not in full_name:
            continue

        (prefix, name) = full_name.split("_", 1)

        if prefix in tables:
            tables[prefix][1][name] = getattr(llvm.core, full_name)

    # Now build the enum symbols in our global namespace. Each is
    # defined as a class with the values in its class dict, so they
    # can be accessed e.g. as LLVMAttr.READ_NONE
    symbols = globals()
    for table_def in tables.itervalues():
        symbols[table_def[0]] = type(table_def[0], (object,), table_def[1])


make_llvm_enums()


class Builder(object):
    """
    Very light wrapper around :py:class:`llvm.core.Builder` providing access
    to more LLVM features.

    :py:mod:`alamatic.codegen` should be the only module that directly depends
    on :py:mod:`llvm`. To ensure this, other code interacts with LLVM
    indirectly via this object, making it possible for us to mock out LLVM
    interactions in tests.

    Instances of this class also provide some convenience features to get
    access to the context in which code generation is running, e.g. to register
    globals on the module as a whole.
    """
    types = LLVMType
    consts = LLVMConstant
    attrs = LLVMAttr
    icmps = LLVMICMP
    fcmps = LLVMFCMP
    linkages = LLVMLinkage
    visibilities = LLVMVisibility
    calling_conventions = LLVMCallingConvention

    def __init__(self, llvm_builder):
        self.instrs = llvm_builder

    @property
    def basic_block(self):
        return self.instr.basic_block

    @property
    def function(self):
        return self.basic_block.function

    @property
    def module(self):
        return self.function.module
