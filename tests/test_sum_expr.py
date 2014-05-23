
from alamatic.ast import *
from alamatic.intermediate import *
from alamatic.testutil import *

# parsing is tested inside an auto-generated function in test_parser


TestOperatorMap = binary_expr_operator_map_case(
    SumExpr,
    {
        '+': 'add',
        '-': 'subtract',
    }
)
