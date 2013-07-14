
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
        got = self.ast_comparison_list(module)
        self.assertEqual(got, expected)

    def assertExprAst(self, inp, expected):
        self.assertAst(inp, [
            ("ExpressionStmt", (), [expected]),
        ])

    def ast_comparison_list(self, root):
        ret = []
        for node in root.child_nodes:
            ret.append((
                type(node).__name__,
                tuple(node.params),
                self.ast_comparison_list(node),
            ))
        return ret

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
                import logging
                logging.debug(repr(line.parts))
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
        self.assertEqual(module.stmts, [])

        # Module with two simple statements
        state = CompileState()
        module = parse_module(
            state,
            StringIO("pass\n\npass"),
            "foo",
            "foo.ala",
        )
        self.assertEqual(len(module.stmts), 2)

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

    def test_pass_statement(self):
        self.assertAst(
            "pass",
            [
                ("PassStmt", (), []),
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
                        ('PassStmt', (), []),
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
                        ('PassStmt', (), []),
                    ]),
                    ("ElseClause", (), [
                        ('PassStmt', (), []),
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
                        ('PassStmt', (), []),
                    ]),
                    ("IfClause", (), [
                        ('IntegerLiteralExpr', (2,), []),
                        ('PassStmt', (), []),
                    ]),
                    ("IfClause", (), [
                        ('IntegerLiteralExpr', (3,), []),
                        ('PassStmt', (), []),
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
                        ('PassStmt', (), []),
                    ]),
                    ("IfClause", (), [
                        ('IntegerLiteralExpr', (2,), []),
                        ('PassStmt', (), []),
                    ]),
                    ("IfClause", (), [
                        ('IntegerLiteralExpr', (3,), []),
                        ('PassStmt', (), []),
                    ]),
                    ("ElseClause", (), [
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
