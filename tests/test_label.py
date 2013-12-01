
from alamatic.ast import *
from alamatic.types import *
from alamatic.intermediate import *
from alamatic.testutil import *
from alamatic.codegen import CodeWriter


class TestCodegen(LanguageTestCase):

    def test_codegen_name(self):
        # This is a pretty dumb test since its just a duplicate of
        # the implementation of the function. Oh well.
        label = Label()
        self.assertEqual(
            label.codegen_name,
            "_ALA_%x" % id(label),
        )

    def test_generate_c_code(self):
        label = Label()
        self.assertEqual(
            generate_c_for_elems([label]),
            "%s:\n" % label.codegen_name,
        )

    def test_replace_operands(self):
        replaced = set()
        def replace(operand):
            replaced.add(operand)
            return operand

        label = Label()
        label.replace_operands(replace)
        self.assertEqual(
            replaced,
            set(),
        )
