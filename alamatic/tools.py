
import sys


def alac():
    # For now this is acting as a parse tree vizualization tool, but of
    # course eventually it will be the main compiler frontend.
    from alamatic.parser import parse_entry_file
    from alamatic.compiler import CompileState
    from alamatic.compiler import prepare_program
    from alamatic.compilelogging import TerminalCompileLogHandler
    from alamatic.codegen import llvm_module_for_program
    fn = sys.argv[1]

    log_handler = TerminalCompileLogHandler(
        sys.stderr,
        sys.stdout,
    )

    state = CompileState(log_handler=log_handler)

    program = prepare_program(state, file(fn), fn)

    log_handler.close()
    if state.error_count > 0:
        return 1

    with program.context():
        llvm_module = llvm_module_for_program(program)

    llvm_module.verify()

    from llvm.ee import ExecutionEngine
    from llvm.passes import PassManager

    print str(llvm_module)

    llvm_pass_manager = PassManager.new()
    llvm_ee = ExecutionEngine.new(llvm_module)

    llvm_pass_manager.add('scalarrepl')
    llvm_pass_manager.add('mem2reg')
    llvm_pass_manager.add('inline')
    llvm_pass_manager.add('ipconstprop')
    llvm_pass_manager.add('loop-simplify')
    llvm_pass_manager.add('lcssa')
    llvm_pass_manager.add('loops')
    llvm_pass_manager.add('basicaa')
    llvm_pass_manager.add('licm')
    llvm_pass_manager.add('loop-reduce')
    llvm_pass_manager.add('instcombine')
    llvm_pass_manager.add('gvn')
    llvm_pass_manager.add('die')
    llvm_pass_manager.add('adce')
    llvm_pass_manager.add('globalopt')
    llvm_pass_manager.add('globaldce')
    llvm_pass_manager.add('simplifycfg')
    llvm_pass_manager.add('sink')
    llvm_pass_manager.add('tailcallelim')
    llvm_pass_manager.add('mergefunc')
    llvm_pass_manager.add('codegenprepare')

    llvm_pass_manager.run(llvm_module)

    output_file = open('out.o', 'w')
    llvm_module.to_native_object(output_file)

    #print_graph(graph)


def print_graph(graph):
    print "\n"
    for block in graph.blocks:
        label = block.label
        instructions = block.operation_instructions
        terminator = block.terminator

        if label:
            print "%r:" % label
        for instruction in instructions:
            print "    %r" % instruction
        print "    %r\n" % terminator
