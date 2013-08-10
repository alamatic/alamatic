
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
from StringIO import StringIO


class TestParser(unittest.TestCase):

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

    def parse_stmts(self, inp):
        caller = inspect.stack()[1]
        state = CompileState()
        module = parse_module(
            state,
            StringIO(inp),
            caller[3],
            "%s:%i" % (caller[3], caller[2]),
        )
        return module.stmts

    def assertAst(self, inp, expected):
        caller = inspect.stack()[1]
        log_handler = LoggingCompileLogHandler()
        state = CompileState(log_handler=log_handler)
        module = parse_module(
            state,
            StringIO(inp),
            caller[3],
            "%s:%i" % (caller[3], caller[2]),
        )
        got = self.ast_comparison_list(module.block)
        self.assertTrue(state.error_count == 0, "Errors during parse")
        self.assertEqual(got, expected)

    def assertExprAst(self, inp, expected, allow_assign=False):
        caller = inspect.stack()[1]
        log_handler = LoggingCompileLogHandler()
        state = CompileState(log_handler=log_handler)
        expr = parse_expression(
            state,
            StringIO(inp),
            "%s:%i" % (caller[3], caller[2]),
            allow_assign=allow_assign
        )
        import logging
        got = self.ast_comparison_node(expr)
        self.assertTrue(
            state.error_count == 0,
            "Errors during parse (see error log)",
        )
        self.assertEqual(got, expected)

    def ast_comparison_list(self, root):
        ret = []
        if root is not None:
            for node in root.child_nodes:
                ret.append(self.ast_comparison_node(node))
        return ret

    def ast_comparison_node(self, node):
        if node is None:
            return None
        return (
            type(node).__name__,
            tuple(node.params),
            self.ast_comparison_list(node),
        )

    def assertErrorsInStmts(self, inp, positions):
        caller = inspect.stack()[1]
        in_memory_log_handler = InMemoryCompileLogHandler()
        logging_log_handler = LoggingCompileLogHandler()
        log_handler = MultiCompileLogHandler((
            in_memory_log_handler,
            logging_log_handler,
        ))
        state = CompileState(log_handler=log_handler)
        module = parse_module(
            state,
            StringIO(inp),
            caller[3],
            "%s:%i" % (caller[3], caller[2]),
        )
        got_positions = []
        for line in in_memory_log_handler.lines:
            if line.level == ERROR:
                for position in line.positions_mentioned:
                    got_positions.append((position[1], position[2]))

        self.assertEqual(got_positions, positions)

    def assertErrorsInExpr(self, inp, positions, allow_assign=False):
        caller = inspect.stack()[1]
        in_memory_log_handler = InMemoryCompileLogHandler()
        logging_log_handler = LoggingCompileLogHandler()
        log_handler = MultiCompileLogHandler((
            in_memory_log_handler,
            logging_log_handler,
        ))
        state = CompileState(log_handler=log_handler)
        expr = parse_expression(
            state,
            StringIO(inp),
            "%s:%i" % (caller[3], caller[2]),
            allow_assign=allow_assign,
        )
        got_positions = []
        for line in in_memory_log_handler.lines:
            if line.level == ERROR:
                for position in line.positions_mentioned:
                    got_positions.append((position[1], position[2]))

        self.assertEqual(got_positions, positions)

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
        self.assertAst(
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
        self.assertAst(
            "break\ncontinue",
            [
                ("BreakStmt", (), []),
                ("ContinueStmt", (), []),
            ]
        )

    def test_expression_statement(self):
        self.assertAst(
            "baz",
            [
                ("ExpressionStmt", (), [
                    ('SymbolExpr', ('baz',), []),
                ]),
            ]
        )

    def test_return_statement(self):
        # with expression
        self.assertAst(
            "return 1",
            [
                ("ReturnStmt", (), [
                    ('IntegerLiteralExpr', (1,), []),
                ]),
            ]
        )
        # without expression
        self.assertAst(
            "return",
            [
                ("ReturnStmt", (), []),
            ]
        )

    def test_if_statement(self):
        self.assertAst(
            'if 1:\n'
            '    pass',
            [
                ("IfStmt", (), [
                    ("IfClause", (), [
                        ('IntegerLiteralExpr', (1,), []),
                        ('StatementBlock', (), [
                            ('PassStmt', (), []),
                        ]),
                    ]),
                ]),
            ]
        )
        self.assertAst(
            'if 1:\n'
            '    pass\n'
            'else:\n'
            '    pass',
            [
                ("IfStmt", (), [
                    ("IfClause", (), [
                        ('IntegerLiteralExpr', (1,), []),
                        ('StatementBlock', (), [
                            ('PassStmt', (), []),
                        ]),
                    ]),
                    ("ElseClause", (), [
                        ('StatementBlock', (), [
                            ('PassStmt', (), []),
                        ]),
                    ]),
                ]),
            ]
        )
        self.assertAst(
            'if 1:\n'
            '    pass\n'
            'elif 2:\n'
            '    pass\n'
            'elif 3:\n'
            '    pass',
            [
                ("IfStmt", (), [
                    ("IfClause", (), [
                        ('IntegerLiteralExpr', (1,), []),
                        ('StatementBlock', (), [
                            ('PassStmt', (), []),
                        ]),
                    ]),
                    ("IfClause", (), [
                        ('IntegerLiteralExpr', (2,), []),
                        ('StatementBlock', (), [
                            ('PassStmt', (), []),
                        ]),
                    ]),
                    ("IfClause", (), [
                        ('IntegerLiteralExpr', (3,), []),
                        ('StatementBlock', (), [
                            ('PassStmt', (), []),
                        ]),
                    ]),
                ]),
            ]
        )
        self.assertAst(
            'if 1:\n'
            '    pass\n'
            'elif 2:\n'
            '    pass\n'
            'elif 3:\n'
            '    pass\n'
            'else:\n'
            '    pass',
            [
                ("IfStmt", (), [
                    ("IfClause", (), [
                        ('IntegerLiteralExpr', (1,), []),
                        ('StatementBlock', (), [
                            ('PassStmt', (), []),
                        ]),
                    ]),
                    ("IfClause", (), [
                        ('IntegerLiteralExpr', (2,), []),
                        ('StatementBlock', (), [
                            ('PassStmt', (), []),
                        ]),
                    ]),
                    ("IfClause", (), [
                        ('IntegerLiteralExpr', (3,), []),
                        ('StatementBlock', (), [
                            ('PassStmt', (), []),
                        ]),
                    ]),
                    ("ElseClause", (), [
                        ('StatementBlock', (), [
                            ('PassStmt', (), []),
                        ]),
                    ]),
                ]),
            ]
        )

    def test_while_statement(self):
        self.assertAst(
            'while 1:\n'
            '    pass\n'
            '    pass',
            [
                ("WhileStmt", (), [
                    ('IntegerLiteralExpr', (1,), []),
                    ('StatementBlock', (), [
                        ('PassStmt', (), []),
                        ('PassStmt', (), []),
                    ]),
                ]),
            ]
        )

    def test_for_statement(self):
        self.assertAst(
            'for i in 1:\n'
            '    pass\n'
            '    pass',
            [
                ("ForStmt", (), [
                    ('SymbolExpr', ("i",), []),
                    ('IntegerLiteralExpr', (1,), []),
                    ('StatementBlock', (), [
                        ('PassStmt', (), []),
                        ('PassStmt', (), []),
                    ]),
                ]),
            ]
        )
        self.assertAst(
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
        self.assertAst(
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
        self.assertAst(
            'var i',
            [
                ('DataDeclStmt', (), [
                    ('VarDeclClause', ('i',), []),
                ]),
            ]
        )
        self.assertAst(
            'var i = 1',
            [
                ('DataDeclStmt', (), [
                    ('VarDeclClause', ('i',), []),
                    ('IntegerLiteralExpr', (1,), []),
                ]),
            ]
        )
        self.assertAst(
            'const i',
            [
                ('DataDeclStmt', (), [
                    ('ConstDeclClause', ('i',), []),
                ]),
            ]
        )
        self.assertAst(
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
        self.assertAst(
            'func doot(a, b as foo):\n'
            '    pass',
            [
                ('FuncDeclStmt', (), [
                    ('FuncDeclClause', ('doot',), [
                        ('ParamDeclClause', ('a',), []),
                        ('ParamDeclClause', ('b',), [
                            ('SymbolExpr', ('foo',), []),
                        ]),
                    ]),
                    ('StatementBlock', (), [
                        ('PassStmt', (), []),
                    ]),
                ]),
            ]
        )

    def test_symbol_expression(self):
        self.assertExprAst(
            "baz",
            ("SymbolExpr", ('baz',), []),
        )

    def test_paren_expression(self):
        # Parentheses just affect precedence during parsing... they
        # don't actually show up explicitly as nodes in the parse tree.
        self.assertExprAst(
            "(1)",
            ('IntegerLiteralExpr', (1,), []),
        )
        self.assertExprAst(
            "((1))",
            ('IntegerLiteralExpr', (1,), []),
        )

    def test_number_expressions(self):
        # Decimal integers
        self.assertExprAst(
            "1",
            ("IntegerLiteralExpr", (1,), []),
        )
        self.assertExprAst(
            "0",
            ("IntegerLiteralExpr", (0,), []),
        )
        self.assertExprAst(
            "92",
            ("IntegerLiteralExpr", (92,), []),
        )
        # Hex integers
        self.assertExprAst(
            "0x1",
            ("IntegerLiteralExpr", (1,), []),
        )
        self.assertExprAst(
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
        self.assertExprAst(
            "01",
            ("IntegerLiteralExpr", (1,), []),
        )
        self.assertExprAst(
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
        self.assertExprAst(
            "0b1",
            ("IntegerLiteralExpr", (1,), []),
        )
        self.assertExprAst(
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
        self.assertExprAst(
            "1.0",
            ("FloatLiteralExpr", (1.0,), []),
        )
        self.assertExprAst(
            "92.2",
            ("FloatLiteralExpr", (92.2,), []),
        )
        self.assertExprAst(
            "1.0E+2",
            ("FloatLiteralExpr", (100.0,), []),
        )
        self.assertExprAst(
            "1.0E-1",
            ("FloatLiteralExpr", (0.1,), []),
        )

    def test_assign_expressions(self):
        for operator in ("=", "+=", "-=", "*=", "/=", "|=", "&="):
            self.assertExprAst(
                "a %s 1" % operator,
                ('AssignExpr', (operator,), [
                    ('SymbolExpr', ('a',), []),
                    ('IntegerLiteralExpr', (1,), []),
                ]),
                allow_assign=True,
            )
        # But chaining is not allowed
        self.assertErrorsInExpr(
            "a = b = 1",
            [
                (1, 6),
            ],
            allow_assign=True,
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
        self.assertExprAst(
            "a or b and c",
            ('LogicalOrExpr', ('or',), [
                ('SymbolExpr', ('a',), []),
                ('LogicalAndExpr', ('and',), [
                    ('SymbolExpr', ('b',), []),
                    ('SymbolExpr', ('c',), []),
                ]),
            ]),
        )
        self.assertExprAst(
            "a and b or c",
            ('LogicalOrExpr', ('or',), [
                ('LogicalAndExpr', ('and',), [
                    ('SymbolExpr', ('a',), []),
                    ('SymbolExpr', ('b',), []),
                ]),
                ('SymbolExpr', ('c',), []),
            ]),
        )


# We generate an additional test function for each binary and unary
# operator. These always follow the same pattern, so it's silly to hand-write
# each of them, but we want to keep each one in its own test function
# so we can see the status of each one in the test result report.

def make_binary_op_func(operator, class_name):
    def func(self):
        self.assertExprAst(
            "a %s b" % operator,
            (class_name, (operator,), [
                ('SymbolExpr', ('a',), []),
                ('SymbolExpr', ('b',), []),
            ]),
        )
        self.assertExprAst(
            "a %s b %s c" % (operator, operator),
            (class_name, (operator,), [
                ('SymbolExpr', ('a',), []),
                (class_name, (operator,), [
                    ('SymbolExpr', ('b',), []),
                    ('SymbolExpr', ('c',), []),
                ]),
            ]),
        )
    func.__name__ = "test_binary_" + operator + "_expression"
    return func


def make_unary_prefix_op_func(operator, class_name):
    def func(self):
        self.assertExprAst(
            "%s a" % operator,
            (class_name, (operator,), [
                ('SymbolExpr', ('a',), []),
            ]),
        )
        self.assertExprAst(
            "%s %s a" % (operator, operator),
            (class_name, (operator,), [
                (class_name, (operator,), [
                    ('SymbolExpr', ('a',), []),
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
