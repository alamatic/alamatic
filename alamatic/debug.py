
from alamatic.util import overloadable
from alamatic.intermediate import BasicBlock
from alamatic.intermediate.operands import Temporary, LiteralValue
from alamatic.intermediate.function import LocalVariable
from alamatic.diagnostics import Diagnostic


class DebugPrinter(object):

    def __init__(self, out_stream):
        self.out_stream = out_stream
        self.basic_block_indices = {}
        self.next_basic_block_index = 0

    def get_basic_block_index(self, block):
        if block not in self.basic_block_indices:
            self.basic_block_indices[block] = self.next_basic_block_index
            self.next_basic_block_index += 1
        return self.basic_block_indices[block]

    def print_ast(self, root_node, indent=0):
        self.out_stream.write(("    " * indent) + "%s%r\n" % (
            type(root_node).__name__,
            tuple(root_node.params),
        ))
        for child_node in root_node.child_nodes:
            self.print_ast(out_stream, child_node, indent + 1)

    @overloadable
    def print_instruction_arg(self, arg):
        self.out_stream.write(repr(arg))

    @print_instruction_arg.overload(BasicBlock)
    def print_basic_block_arg(self, block):
        self.out_stream.write("block%02x" % self.get_basic_block_index(block))

    @print_instruction_arg.overload(Temporary)
    def print_temporary_arg(self, temporary):
        self.out_stream.write("r%02x" % temporary.index)

    @print_instruction_arg.overload(LiteralValue)
    def print_literal_value_arg(self, value_desc):
        self.out_stream.write(repr(value_desc.value))

    @print_instruction_arg.overload(LocalVariable)
    def print_local_variable_arg(self, variable):
        self.out_stream.write(variable.codegen_name)

    @print_instruction_arg.overload(Diagnostic)
    def print_local_variable_arg(self, diagnostic):
        self.out_stream.write(type(diagnostic).__name__)

    def print_instruction(self, instr):
        self.out_stream.write("%s" % (
            instr.mnemonic
        ))
        for arg in instr.args:
            self.out_stream.write(" ")
            self.print_instruction_arg(arg)

    def print_basic_block(self, block, indent=0):
        for instr in block.body_instrs:
            self.out_stream.write("    " * indent)
            self.out_stream.write("\x1b[s")
            self.print_instruction(instr)
            if instr.source_range is not None:
                self.out_stream.write(
                    "\x1b[u\x1b[40C; %s" % instr.source_range.start
                )
            self.out_stream.write("\n")
        if block.terminator is not None:
            self.out_stream.write("    " * indent)
            self.out_stream.write("\x1b[s")
            self.print_instruction(block.terminator)
            if block.terminator.source_range is not None:
                self.out_stream.write(
                    "\x1b[u\x1b[40C; %s" % block.terminator.source_range.start
                )
            self.out_stream.write("\n")

    def print_control_flow_graph(self, graph, indent=0):
        blocks = list(graph.blocks)
        block_indices = {
            block: self.get_basic_block_index(block) for block in blocks
        }

        for block in blocks:
            self.out_stream.write("    " * indent)
            self.out_stream.write("block%02x:\n" % block_indices[block])
            self.print_basic_block(block, indent + 1)
            self.out_stream.write("\n")

    def print_control_flow_graph_as_dot(self, graph):
        from StringIO import StringIO
        self.out_stream.write("digraph G {\n")
        self.out_stream.write("    node [shape=rect,fontname=Courier];\n")
        for block in graph.blocks:
            block_index = self.get_basic_block_index(block)
            orig_stream = self.out_stream
            try:
                self.out_stream = StringIO()
                for instr in list(block.body_instrs) + [block.terminator]:
                    self.print_instruction(instr)
                    self.out_stream.write("\n")
                node_caption = str(self.out_stream.getvalue())
            finally:
                self.out_stream = orig_stream

            node_caption_gv = repr(node_caption).replace('"', "\\\"")
            node_caption_gv = node_caption_gv.replace('\\n', "\\l")
            node_caption_gv = '"' + node_caption_gv[1:-1] + '"'

            self.out_stream.write('    "block%02x" [label=%s];\n' % (
                block_index, node_caption_gv,
            ))

            for i, other_block in enumerate(block.terminator.successor_blocks):
                other_block_index = self.get_basic_block_index(other_block)
                self.out_stream.write(
                    '    "block%02x" -> "block%02x" [label=%i]\n' % (
                        block_index, other_block_index, i,
                    )
                )
        self.out_stream.write("}\n")

    def print_function(self, function):
        self.out_stream.write("function:\n")  # TODO: arguments
        for variable in function.local_variables:
            self.out_stream.write("    LOCAL %s ; for %s at %s\n" % (
                variable.codegen_name,
                variable.decl_name,
                variable.decl_range.start,
            ))

        if len(function.local_variables):
            self.out_stream.write("\n")

        self.print_control_flow_graph(function.graph, 1)
