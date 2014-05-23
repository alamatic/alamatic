
from alamatic.ast import *
from alamatic.testutil import *
from mock import MagicMock

# parsing is tested inside an auto-generated function in test_parser


TestOperatorMap = binary_expr_operator_map_case(
    ComparisonExpr,
    {
        '==': 'equals',
        '!=': 'not_equals',
        '<': 'is_less_than',
        '>': 'is_greater_than',
        '<=': 'is_less_than_or_equal_to',
        '>=': 'is_greater_than_or_equal_to',
    }
)
