
from alamatic.ast import *
from alamatic.types import *
from alamatic.intermediate import *
from alamatic.testutil import *
from alamatic.codegen import CodeWriter


class TestBuilding(LanguageTestCase):

    def test_replace_operands(self):
        target = DummyOperand("target")
        operand = DummyOperand("operand")
        op = CopyOperation(
            target,
            operand,
        )
        self.assertEqual(
            get_operation_replaceable_operands(op),
            {target, operand},
        )


class TestCodegen(LanguageTestCase):

    def test_generate(self):
        op = CopyOperation(
            DummyOperand("target"),
            DummyOperand("operand"),
        )
        self.assertEqual(
            generate_c_for_operation(op),
            "DUMMY(target) = DUMMY(operand)",
        )
