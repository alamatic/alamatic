
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
