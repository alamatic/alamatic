
import unittest
import inspect
from alamatic.compiler import CompileState
from alamatic.compilelogging import (
    ERROR,
    LoggingCompileLogHandler,
    InMemoryCompileLogHandler,
    MultiCompileLogHandler,
)
from alamatic.parser import *
from alamatic.ast import *
from alamatic.testutil import *
from StringIO import StringIO


class TestParser(LanguageTestCase):

    assertErrorsInStmts = testcase_assertErrorsInStmts
    assertErrorsInExpr = testcase_assertErrorsInExpr

    binary_operators = (
        # These are in precedence order with lowest first.
        # Blank lines represent actual changes in precedence, so
        # these are grouped to show which operators actually have
        # equal precedence.
        ("or", "LogicalOrExpr"),

        ("and", "LogicalAndExpr"),

        ("is", "ComparisonExpr"),
        ("is not", "ComparisonExpr"),
        ("<", "ComparisonExpr"),
        ("<=", "ComparisonExpr"),
        (">", "ComparisonExpr"),
        (">=", "ComparisonExpr"),
        ("!=", "ComparisonExpr"),
        ("==", "ComparisonExpr"),

        ("|", "BitwiseOrExpr"),

        ("&", "BitwiseAndExpr"),

        ("<<", "ShiftExpr"),
        (">>", "ShiftExpr"),

        ("+", "SumExpr"),
        ("-", "SumExpr"),

        ("*", "MultiplyExpr"),
        ("/", "MultiplyExpr"),
        ("%", "MultiplyExpr"),
    )
    unary_prefix_operators = (
        # These are also in order of increasing precedence and grouped,
        # just like the binary operators above.
        ("not", "LogicalNotExpr"),

        ("+", "SignExpr"),
        ("-", "SignExpr"),
        ("~", "BitwiseNotExpr"),
    )

    def test_basics(self):

        # Empty module
        state = CompileState()
        module = parse_module(
            state,
            StringIO(""),
            "foo",
            "foo.ala",
        )
        self.assertEqual(module.name, "foo")
        self.assertEqual(module.position, ("foo.ala", 1, 0))
        self.assertEqual(module.block.stmts, [])

        # Module with two simple statements
        state = CompileState()
        module = parse_module(
            state,
            StringIO("pass\n\npass"),
            "foo",
            "foo.ala",
        )
        self.assertEqual(len(module.block.stmts), 2)

    def test_error_recovery(self):
        # Simple line skipping: the two lines that start with ==
        # should be skipped after an error is generated.
        self.assertErrorsInStmts(
            "==:\npass\n==",
            [
                (1, 0),
                (3, 0),
            ]
        )

        # Block skipping:
        self.assertErrorsInStmts(
            "==:\n    pass\n    ==\n==",
            [
                (1, 0),
                (4, 0),
            ]
        )

        # Block skipping with elif and else, which should
        # also be skipped.
        self.assertErrorsInStmts(
            "==:\n    pass\n    ==\nelif 1:\n    ==\nelse:\n    ==\n==",
            [
                (1, 0),
                (8, 0),
            ]
        )

    def test_pass_statement(self):
        self.assertStmtParseTree(
            "pass",
            [
                ("PassStmt", (), []),
            ]
        )
        self.assertErrorsInStmts(
            "pass pass",
            [
                (1, 5),
            ]
        )

    def test_loop_control_statements(self):
        self.assertStmtParseTree(
            "break\ncontinue",
            [
                ("BreakStmt", (), []),
                ("ContinueStmt", (), []),
            ]
        )

    def test_return_statement(self):
        # with expression
        self.assertStmtParseTree(
            "return 1",
            [
                ("ReturnStmt", (), [
                    ('IntegerLiteralExpr', (1,), []),
                ]),
            ]
        )
        # without expression
        self.assertStmtParseTree(
            "return",
            [
                ("ReturnStmt", (), []),
            ]
        )

    def test_for_statement(self):
        self.assertStmtParseTree(
            'for i in 1:\n'
            '    pass\n'
            '    pass',
            [
                ("ForStmt", (), [
                    ('SymbolNameExpr', ("i",), []),
                    ('IntegerLiteralExpr', (1,), []),
                    ('StatementBlock', (), [
                        ('PassStmt', (), []),
                        ('PassStmt', (), []),
                    ]),
                ]),
            ]
        )
        self.assertStmtParseTree(
            'for var i in 1:\n'
            '    pass\n'
            '    pass',
            [
                ("ForStmt", (), [
                    ('VarDeclClause', ("i",), []),
                    ('IntegerLiteralExpr', (1,), []),
                    ('StatementBlock', (), [
                        ('PassStmt', (), []),
                        ('PassStmt', (), []),
                    ]),
                ]),
            ]
        )
        self.assertStmtParseTree(
            'for const i in 1:\n'
            '    pass\n'
            '    pass',
            [
                ("ForStmt", (), [
                    ('ConstDeclClause', ("i",), []),
                    ('IntegerLiteralExpr', (1,), []),
                    ('StatementBlock', (), [
                        ('PassStmt', (), []),
                        ('PassStmt', (), []),
                    ]),
                ]),
            ]
        )

    def test_data_decl_statement(self):
        self.assertStmtParseTree(
            'var i',
            [
                ('DataDeclStmt', (), [
                    ('VarDeclClause', ('i',), []),
                ]),
            ]
        )
        self.assertStmtParseTree(
            'var i = 1',
            [
                ('DataDeclStmt', (), [
                    ('VarDeclClause', ('i',), []),
                    ('IntegerLiteralExpr', (1,), []),
                ]),
            ]
        )
        self.assertStmtParseTree(
            'const i',
            [
                ('DataDeclStmt', (), [
                    ('ConstDeclClause', ('i',), []),
                ]),
            ]
        )
        self.assertStmtParseTree(
            'const i = 1',
            [
                ('DataDeclStmt', (), [
                    ('ConstDeclClause', ('i',), []),
                    ('IntegerLiteralExpr', (1,), []),
                ]),
            ]
        )
        self.assertErrorsInStmts(
            "var i 1",
            [
                (1, 6),
            ]
        )
        self.assertErrorsInStmts(
            "var 1",
            [
                (1, 4),
            ]
        )
        self.assertErrorsInStmts(
            "var i = 1 2",
            [
                (1, 10),
            ]
        )

    def test_func_decl_statement(self):
        self.assertStmtParseTree(
            'func doot(a, b as foo):\n'
            '    pass',
            [
                ('FuncDeclStmt', (), [
                    ('FuncDeclClause', ('doot',), [
                        ('ParamDeclClause', ('a',), []),
                        ('ParamDeclClause', ('b',), [
                            ('SymbolNameExpr', ('foo',), []),
                        ]),
                    ]),
                    ('StatementBlock', (), [
                        ('PassStmt', (), []),
                    ]),
                ]),
            ]
        )

    def test_symbol_expression(self):
        self.assertExprParseTree(
            "baz",
            ("SymbolNameExpr", ('baz',), []),
        )

    def test_paren_expression(self):
        # Parentheses just affect precedence during parsing... they
        # don't actually show up explicitly as nodes in the parse tree.
        self.assertExprParseTree(
            "(1)",
            ('IntegerLiteralExpr', (1,), []),
        )
        self.assertExprParseTree(
            "((1))",
            ('IntegerLiteralExpr', (1,), []),
        )

    def test_number_expressions(self):
        # Decimal integers
        self.assertExprParseTree(
            "1",
            ("IntegerLiteralExpr", (1,), []),
        )
        self.assertExprParseTree(
            "0",
            ("IntegerLiteralExpr", (0,), []),
        )
        self.assertExprParseTree(
            "92",
            ("IntegerLiteralExpr", (92,), []),
        )
        # Hex integers
        self.assertExprParseTree(
            "0x1",
            ("IntegerLiteralExpr", (1,), []),
        )
        self.assertExprParseTree(
            "0xff",
            ("IntegerLiteralExpr", (255,), []),
        )
        self.assertErrorsInStmts(
            "0xfg",
            [
                (1, 0),
            ]
        )
        # Octal integers
        self.assertExprParseTree(
            "01",
            ("IntegerLiteralExpr", (1,), []),
        )
        self.assertExprParseTree(
            "010",
            ("IntegerLiteralExpr", (8,), []),
        )
        self.assertErrorsInStmts(
            "08",
            [
                (1, 0),
            ]
        )
        # Binary integers
        self.assertExprParseTree(
            "0b1",
            ("IntegerLiteralExpr", (1,), []),
        )
        self.assertExprParseTree(
            "0b10",
            ("IntegerLiteralExpr", (2,), []),
        )
        self.assertErrorsInStmts(
            "0b02",
            [
                (1, 0),
            ]
        )
        # Decimal floats
        self.assertExprParseTree(
            "1.0",
            ("FloatLiteralExpr", (1.0,), []),
        )
        self.assertExprParseTree(
            "92.2",
            ("FloatLiteralExpr", (92.2,), []),
        )
        self.assertExprParseTree(
            "1.0E+2",
            ("FloatLiteralExpr", (100.0,), []),
        )
        self.assertExprParseTree(
            "1.0E-1",
            ("FloatLiteralExpr", (0.1,), []),
        )

    def test_assign_disallowed(self):
        self.assertErrorsInExpr(
            "a = 1",
            [
                (1, 2),
            ],
            allow_assign=False,
        )

    def test_logical_operator_precedence(self):
        # TODO: Generalize this to test everything in self.binary_operators,
        # assuming that the list is in order of precedence.
        self.assertExprParseTree(
            "a or b and c",
            ('LogicalOrExpr', ('or',), [
                ('SymbolNameExpr', ('a',), []),
                ('LogicalAndExpr', ('and',), [
                    ('SymbolNameExpr', ('b',), []),
                    ('SymbolNameExpr', ('c',), []),
                ]),
            ]),
        )
        self.assertExprParseTree(
            "a and b or c",
            ('LogicalOrExpr', ('or',), [
                ('LogicalAndExpr', ('and',), [
                    ('SymbolNameExpr', ('a',), []),
                    ('SymbolNameExpr', ('b',), []),
                ]),
                ('SymbolNameExpr', ('c',), []),
            ]),
        )


# We generate an additional test function for each binary and unary
# operator. These always follow the same pattern, so it's silly to hand-write
# each of them, but we want to keep each one in its own test function
# so we can see the status of each one in the test result report.

def make_binary_op_func(operator, class_name):
    def func(self):
        self.assertExprParseTree(
            "a %s b" % operator,
            (class_name, (operator,), [
                ('SymbolNameExpr', ('a',), []),
                ('SymbolNameExpr', ('b',), []),
            ]),
        )
        self.assertExprParseTree(
            "a %s b %s c" % (operator, operator),
            (class_name, (operator,), [
                ('SymbolNameExpr', ('a',), []),
                (class_name, (operator,), [
                    ('SymbolNameExpr', ('b',), []),
                    ('SymbolNameExpr', ('c',), []),
                ]),
            ]),
        )
    func.__name__ = "test_binary_" + operator + "_expression"
    return func


def make_unary_prefix_op_func(operator, class_name):
    def func(self):
        self.assertExprParseTree(
            "%s a" % operator,
            (class_name, (operator,), [
                ('SymbolNameExpr', ('a',), []),
            ]),
        )
        self.assertExprParseTree(
            "%s %s a" % (operator, operator),
            (class_name, (operator,), [
                (class_name, (operator,), [
                    ('SymbolNameExpr', ('a',), []),
                ]),
            ]),
        )
    func.__name__ = "test_unary_prefix_" + operator + "_expression"
    return func


for op_map in TestParser.binary_operators:
    binary_op_func = make_binary_op_func(op_map[0], op_map[1])
    setattr(TestParser, binary_op_func.__name__, binary_op_func)
    del binary_op_func

for op_map in TestParser.unary_prefix_operators:
    unary_prefix_op_func = make_unary_prefix_op_func(op_map[0], op_map[1])
    setattr(TestParser, unary_prefix_op_func.__name__, unary_prefix_op_func)
    del unary_prefix_op_func
