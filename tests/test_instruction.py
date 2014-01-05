
from alamatic.ast import *
from alamatic.types import *
from alamatic.intermediate import *
from alamatic.testutil import *
from alamatic.codegen import CodeWriter


class TestGenerateC(LanguageTestCase):

    def test_generate_wrapper(self):
        # For instructions we have subclasses actually override
        # _generate_c_code and then we have a standard implementation
        # of generate_c_code that handes the invariant indent, semicolon and
        # newline that all operations require.
        from StringIO import StringIO

        class DummyInstruction(Instruction):
            def _generate_c_code(self, state, writer):
                writer.write("DUMMY")

        dummy = DummyInstruction()
        f = StringIO()
        writer = CodeWriter(f)
        dummy.generate_c_code(None, writer)
        self.assertEqual(
            f.getvalue(),
            "  DUMMY;\n",
        )
