
from alamatic.ast import *
from alamatic.types import *
from alamatic.testutil import *
from mock import MagicMock

# parsing is tested inside an auto-generated function in test_parser


TestOperatorMap = binary_expr_operator_map_case(
    ComparisonExpr,
    {
        '==': 'equals',
        '!=': 'not_equals',
        '<': 'less_than',
        '>': 'greater_than',
        '<=': 'less_than_equal',
        '>=': 'greater_than_equal',
    }
)
