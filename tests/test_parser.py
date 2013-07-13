
import unittest
import inspect
from alamatic.compiler import CompileState
from alamatic.compilelogging import ERROR
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
        state = CompileState()
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
            ("ExpressionStatement", (), [expected]),
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
        state = CompileState()
        module = parse_module(
            state,
            StringIO(inp),
            caller[3],
            "%s:%i" % (caller[3], caller[2]),
        )
        got_positions = []
        for line in state.log_lines:
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
                ("PassStatement", (), []),
            ]
        )

    def test_loop_control_statements(self):
        self.assertAst(
            "break\ncontinue",
            [
                ("BreakStatement", (), []),
                ("ContinueStatement", (), []),
            ]
        )

    def test_expression_statement(self):
        self.assertAst(
            "baz",
            [
                ("ExpressionStatement", (), [
                    ('SymbolExpression', ('baz',), []),
                ]),
            ]
        )

    def test_number_expressions(self):
        # Decimal integers
        self.assertExprAst(
            "1",
            ("IntegerLiteralExpression", (1,), []),
        )
        self.assertExprAst(
            "92",
            ("IntegerLiteralExpression", (92,), []),
        )
        # Hex integers
        self.assertExprAst(
            "0x1",
            ("IntegerLiteralExpression", (1,), []),
        )
        self.assertExprAst(
            "0xff",
            ("IntegerLiteralExpression", (255,), []),
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
            ("IntegerLiteralExpression", (1,), []),
        )
        self.assertExprAst(
            "010",
            ("IntegerLiteralExpression", (8,), []),
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
            ("IntegerLiteralExpression", (1,), []),
        )
        self.assertExprAst(
            "0b10",
            ("IntegerLiteralExpression", (2,), []),
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
            ("FloatLiteralExpression", (1.0,), []),
        )
        self.assertExprAst(
            "92.2",
            ("FloatLiteralExpression", (92.2,), []),
        )
        self.assertExprAst(
            "1.0E+2",
            ("FloatLiteralExpression", (100.0,), []),
        )
        self.assertExprAst(
            "1.0E-1",
            ("FloatLiteralExpression", (0.1,), []),
        )
