
from alamatic.ast import *
from alamatic.intermediate import *
from alamatic.testutil import *


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
