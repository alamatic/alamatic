
from alamatic.ast import *
from alamatic.types import *
from alamatic.testutil import *

import unittest


class TestBaseType(LanguageTestCase):

    @unittest.skip("needs updating to work with intermediate style")
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

        lhs = DummyExprRuntime('lhs').evaluate()
        rhs = DummyExprRuntime('rhs').evaluate()
        source_node = DummyExprRuntime('source')

        for op_name in binary_ops:
            op_method = getattr(Value, op_name, None)
            self.assertTrue(
                op_method is not None,
                "Value class has %s method" % op_name
            )
            self.assertRaises(
                OperationNotSupportedError,
                lambda: op_method(lhs, rhs, ("test", 1, 0))
            )
