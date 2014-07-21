
import sys


def alac():
    # For now this is acting as a parse tree vizualization tool, but of
    # course eventually it will be the main compiler frontend.
    from alamatic.parser import parse_module
    from alamatic.compiler import CompileState
    from alamatic.compilelogging import TerminalCompileLogHandler
    from alamatic.preprocessor import preprocess_cfg
    fn = sys.argv[1]

    log_handler = TerminalCompileLogHandler(
        sys.stderr,
        sys.stdout,
    )

    state = CompileState(log_handler=log_handler)

    module = parse_module(
        state,
        file(fn),
        None,
        fn,
    )
    log_handler.close()
    if state.error_count > 0:
        return 1

    unit = module.get_intermediate_form()
    graph = unit.graph

    preprocess_cfg(graph)

    print_graph(graph)


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
