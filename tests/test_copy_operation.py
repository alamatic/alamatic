
from alamatic.ast import *
from alamatic.types import *
from alamatic.intermediate import *
from alamatic.testutil import *
from alamatic.codegen import CodeWriter


class TestBuilding(LanguageTestCase):

    def test_replace_operands(self):
        operand = DummyOperand("operand")
        op = CopyOperation(
            operand,
        )
        self.assertEqual(
            get_operation_replaceable_operands(op),
            {operand},
        )


class TestCodegen(LanguageTestCase):

    def test_generate(self):
        op = CopyOperation(
            DummyOperand("operand"),
        )
        self.assertEqual(
            generate_c_for_operation(op),
            "DUMMY(operand)",
        )
