
def serialize_ast(out_stream, root_node, indent=0):
    out_stream.write(("    " * indent) + "%s%r\n" % (
        type(root_node).__name__,
        tuple(root_node.params),
    ))
    for child_node in root_node.child_nodes:
        serialize_ast(out_stream, child_node, indent + 1)
