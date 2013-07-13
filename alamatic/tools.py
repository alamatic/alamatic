
import sys


def alac():
    # For now this is acting as a parse tree vizualization tool, but of
    # course eventually it will be the main compiler frontend.
    from alamatic.parser import parse_module
    from alamatic.compiler import CompileState
    fn = sys.argv[1]
    state = CompileState()
    module = parse_module(
        state,
        file(fn),
        None,
        fn,
    )
    for row in module.as_tree_rows():
        print row
