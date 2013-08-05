
import unittest
from alamatic.codegen import *
from StringIO import StringIO


class TestCodegenUtils(unittest.TestCase):

    def test_code_writer(self):
        stream = StringIO()
        writer = CodeWriter(stream)

        writer.write("hello ")
        writer.writeln("world")
        writer.indent()
        writer.writeln("foo")
        writer.write("bar ", "boo ")
        writer.write("baz\n")
        writer.write("sometimes")
        with writer.braces():
            writer.writeln("fail")
        with writer.braces():
            with writer.braces():
                writer.writeln("fail")
        writer.outdent()
        writer.writeln("bye")

        result = stream.getvalue()
        print result
        self.assertEqual(
            result,
            "hello world\n"
            "  foo\n"
            "  bar boo baz\n"
            "  sometimes {\n"
            "    fail\n"
            "  }\n"
            "  {\n"
            "    {\n"
            "      fail\n"
            "    }\n"
            "  }\n"
            "bye\n"
        )
