
from alamatic.ast import *
from alamatic.types import *
from alamatic.testutil import *
from mock import MagicMock

# parsing is tested inside an auto-generated function in test_parser

# execution is tested inside test_interpreter_exec


class TestCodeGen(LanguageTestCase):

    def test_generate_add(self):
        test_expr = SumExpr(
            None,
            DummyExprRuntime('lhs'),
            '+',
            DummyExprRuntime('rhs'),
        )
        self.assertCCode(
            test_expr,
            "(DUMMY(lhs) + DUMMY(rhs))",
        )

    def test_generate_subtract(self):
        test_expr = SumExpr(
            None,
            DummyExprRuntime('lhs'),
            '-',
            DummyExprRuntime('rhs'),
        )
        self.assertCCode(
            test_expr,
            "(DUMMY(lhs) - DUMMY(rhs))",
        )
