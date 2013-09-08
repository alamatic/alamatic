
import sys


def alac():
    # For now this is acting as a parse tree vizualization tool, but of
    # course eventually it will be the main compiler frontend.
    from alamatic.parser import parse_module
    from alamatic.compiler import CompileState
    from alamatic.compilelogging import TerminalCompileLogHandler
    from alamatic.interpreter import make_runtime_program
    from alamatic.codegen import generate_c_unit_for_module
    fn = sys.argv[1]
    state = CompileState(log_handler=TerminalCompileLogHandler(
        sys.stderr,
        sys.stdout,
    ))

    module = parse_module(
        state,
        file(fn),
        None,
        fn,
    )
    if state.error_count > 0:
        return 1

    runtime_program = make_runtime_program(state, module)
    if state.error_count > 0:
        return 1

    runtime_program.generate_c_unit(state, sys.stdout)
