
import sys


def alac():
    # For now this is acting as a parse tree vizualization tool, but of
    # course eventually it will be the main compiler frontend.
    from alamatic.parser import parse_module
    from alamatic.compiler import CompileState
    from alamatic.compilelogging import TerminalCompileLogHandler
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

    graph = module.get_intermediate_form()
    from StringIO import StringIO
    from alamatic.codegen import CodeWriter
    import json
    print "digraph G {"
    font_bits = "fontname=Courier,fontsize=10.0"
    for block in graph.blocks:
        f = StringIO()
        writer = CodeWriter(f)
        for operation in block.operations:
            operation.generate_c_code(state, writer)

        if block.successor_is_conditional:
            writer.write("\n")
            writer.write("if ")
            block.exit_cond.generate_c_code(state, writer)
            writer.write("...\n")

        label_str = json.dumps(f.getvalue())
        label_str = label_str.replace(r'\n', r'\l')
        styles = []
        if block.is_loop_header:
            styles.append("bold")
        if block is graph.entry_block or block is graph.exit_block:
            styles.append("rounded")
        print '    "block_%x" [label=%s,shape="rect",%s,style="%s"];' % (
            id(block),
            label_str,
            font_bits,
            ",".join(styles),
        )
    for block in graph.blocks:
        source_name = "block_%x" % id(block)
        if block.false_successor is None:
            # it's the exit block, so skip
            continue
        if block.successor_is_conditional:
            true_name = "block_%x" % id(block.true_successor)
            print '    "%s" -> "%s" [label=T, style=dashed];' % (
                source_name,
                true_name,
            )
            false_name = "block_%x" % id(block.false_successor)
            print '    "%s" -> "%s" [label=F, style=dashed];' % (
                source_name,
                false_name,
            )
        else:
            false_name = "block_%x" % id(block.false_successor)
            if block.false_successor.index < block.index:
                # it's a backward jump, creating a loop
                print '    "%s" -> "%s" [style=bold];' % (
                    source_name,
                    false_name,
                )
            else:
                print '    "%s" -> "%s" [style=solid];' % (
                    source_name,
                    false_name,
                )

    def print_loop_graph(loop, indent=0, LR=False):
        indent_spaces = " " * (indent * 4)
        print ""
        print indent_spaces + "    subgraph cluster_loop%x {" % id(loop)
        if LR:
            print indent_spaces + '        graph [rank="LR"];'
        else:
            print indent_spaces + '        graph [rank="TB"];'
        loop_blocks = loop.body_blocks.union(set([loop.header_block]))
        for block in loop_blocks:
            print indent_spaces + '        "block_%x";' % id(block)
        for child_loop in loop.child_loops:
            print_loop_graph(child_loop, indent + 1, not LR)
        print indent_spaces + "    }"

    loops = list(graph.root_loops)
    for loop in loops:
        print_loop_graph(loop)
    for block in graph.blocks:
        for dom in block.dominators:
            source_name = "block_%x" % id(block)
            target_name = "block_%x" % id(dom)
            #print '    "%s" -> "%s" [style=dotted]; // %r -> %r' % (
            #    source_name, target_name, type(block), type(dom)
            #)
    print "}"
    sys.exit(0)

    from alamatic.codegen import CodeWriter
    writer = CodeWriter(sys.stdout)
    for elem in intermediate:
        elem.generate_c_code(state, writer)
