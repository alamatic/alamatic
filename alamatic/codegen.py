

def generate_c_unit_for_module(state, module, stream):
    writer = CodeWriter(stream)
    writer.writeln("\n#include <stdint.h>\n")
    module.block.generate_decl_c_code(state, writer)
    writer.writeln("")
    writer.write("int main(int argc, char **argv)")
    with writer.braces():
        module.block.generate_body_c_code(state, writer)


class RuntimeProgram(object):
    """
    Represents an entire program ready for code generation.

    This ends up being a flattened view of everything that was generated during
    the interpreter phase, ready all be generated into a single C compilation
    unit.
    """

    def __init__(
        self,
        runtime_functions,
        runtime_types,
        top_level_scopes,
        entry_point_function=None,
    ):
        self.runtime_functions = runtime_functions
        self.runtime_types = runtime_types
        self.top_level_scopes = top_level_scopes
        self.entry_point_function = entry_point_function

        if self.entry_point_function not in self.runtime_functions:
            raise Exception(
                "entry_point_function must be a member of runtime_functions"
            )

    def generate_c_unit(self, state, stream):
        writer = CodeWriter(stream)
        writer.writeln("\n#include <stdint.h>\n")

        for type_ in self.runtime_types:
            type_.generate_c_forward_decl(state, writer)
        for type_ in self.runtime_types:
            type_.generate_c_decl(state, writer)

        writer.writeln("")

        for symbols in self.top_level_scopes:
            symbols.generate_c_decls(state, writer)
            writer.writeln("")

        # generate forward decls for the functions first. Doing this for
        # everything is overkill, but it means we don't have to generate
        # the functions in any particular order.
        for function in self.runtime_functions:
            function.generate_c_forward_decl(state, writer)

        writer.writeln("")

        # now generate the actual function declarations, safe in the knowledge
        # that any possible function they might call has already been declared.
        for function in self.runtime_functions:
            # generate actual functions
            function.generate_c_decl(state, writer)
            writer.writeln("")

        writer.writeln("")

        if self.entry_point_function is not None:
            from alamatic.ast import (
                RuntimeFunctionCallExpr,
                ExpressionList,
            )
            # generate main() as a wrapper around the entry point.
            # FIXME: We should make the arguments available to the
            # entry point function somehow.
            writer.write("int main(int argc, char **argv)")
            with writer.braces():
                call_expr = RuntimeFunctionCallExpr(
                    None,
                    self.entry_point_function,
                    self.entry_point_function.args_type(
                        ExpressionList([]),
                    ),
                )
                call_expr.generate_c_code(state, writer)
                writer.writeln(";")


class CodeWriter(object):

    def __init__(self, stream):
        self.indent_level = 0
        self.stream = stream
        self.at_start_of_line = True

    def indent(self):
        self.indent_level += 1

    def outdent(self):
        self.indent_level -= 1

    def write(self, *strs):
        if self.at_start_of_line:
            self.stream.write("  " * self.indent_level)
        for s in strs:
            self.stream.write(s)
        if len(s) > 0 and s.endswith("\n"):
            self.at_start_of_line = True
        else:
            self.at_start_of_line = False

    def writeln(self, *strs):
        self.write(*strs)
        self.stream.write("\n")
        self.at_start_of_line = True

    def braces(self, trailing_newline=True):
        writer = self

        class Braces(object):

            def __enter__(self):
                if writer.at_start_of_line:
                    writer.writeln("{")
                else:
                    writer.writeln(" {")
                writer.indent()

            def __exit__(*args):
                writer.outdent()
                if trailing_newline:
                    writer.writeln("}")
                else:
                    writer.write("}")

        return Braces()
