
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
        if len(strs) == 0:
            return
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
