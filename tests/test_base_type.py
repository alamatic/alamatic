
from alamatic.ast import *
from alamatic.types import *
from alamatic.testutil import *


class TestBaseType(LanguageTestCase):

    def test_binary_operation_stubs(self):
        binary_ops = [
            "add",
            "subtract",
            "multiply",
            "divide",
            "modulo",
            "equals",
            "not_equals",
            "is_less_than",
            "is_greater_than",
            "is_less_than_or_equal_to",
            "is_greater_than_or_equal_to",
            "logical_or",
            "logical_and",
            "bitwise_or",
            "bitwise_and",
            "shift_left",
            "shift_right",
        ]

        lhs = DummyExprCompileTime('lhs').evaluate()
        rhs = DummyExprCompileTime('rhs').evaluate()
        source_node = DummyExprCompileTime('source')

        for op_name in binary_ops:
            op_method = getattr(Value, op_name, None)
            self.assertTrue(
                op_method is not None,
                "Value class has %s method" % op_name
            )
            self.assertRaises(
                OperationNotSupportedError,
                lambda: op_method(source_node, lhs, rhs)
            )
