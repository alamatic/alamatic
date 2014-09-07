
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
        module = llvm_module_for_program(program)

    print str(module)

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
