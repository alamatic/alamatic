
from llvm.core import (
    Module as LLVMModule,
    Type as LLVMType,
    Builder as LLVMBuilder,
)

from alamatic.intermediate import (
    NamedSymbol,
    TemporarySymbol,
)
from alamatic.context import new_context


__all__ = [
    "module_for_cfg",
]


# Temporary interface; will change once we have an abstraction around raw
# control flow graphs, produced by the preprocessor.
def module_for_unit(unit):
    graph = unit.graph
    symbols = unit.symbols
    module = LLVMModule.new("tmp")

    func_type = LLVMType.function(LLVMType.void(), [])
    func = module.add_function(func_type, 'tmp')

    preamble = func.append_basic_block("preamble")
    preamble_builder = LLVMBuilder.new(preamble)
    llvm_entry_block = None

    symbol_values = {}

    for symbol in symbols.all_symbols:
        if not symbol.is_temporary:
            symbol_values[symbol] = preamble_builder.alloca(
                symbol.type.impl.get_llvm_type()
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

            builder = LLVMBuilder.new(llvm_block)

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
                    builder.store(llvm_value, llvm_store_ptr)

            if block is graph.exit_block:
                builder.ret_void()
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
