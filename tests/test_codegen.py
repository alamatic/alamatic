
import unittest
from alamatic.ast import *
from alamatic.types import *
from alamatic.testutil import *


class TestCodegen(unittest.TestCase):

    assertCCode = testcase_assertCCode

    def test_if_stmt(self):
        self.assertCCode(
            IfStmt(
                None,
                [
                    IfClause(
                        None,
                        DummyExprRuntime("if_expr", Bool),
                        DummyStatementBlock([
                            DummyStmtRuntime("if_body"),
                        ])
                    ),
                ]
            ),
            "if (DUMMY(if_expr)) {\n"
            "  // DUMMY if_body\n"
            "}\n"
        )
        self.assertCCode(
            IfStmt(
                None,
                [
                    IfClause(
                        None,
                        DummyExprRuntime("if_expr", Bool),
                        DummyStatementBlock([
                            DummyStmtRuntime("if_body"),
                        ])
                    ),
                    IfClause(
                        None,
                        DummyExprRuntime("elif_expr", Bool),
                        DummyStatementBlock([
                            DummyStmtRuntime("elif_body"),
                        ])
                    ),
                ]
            ),
            "if (DUMMY(if_expr)) {\n"
            "  // DUMMY if_body\n"
            "}\n"
            "else if (DUMMY(elif_expr)) {\n"
            "  // DUMMY elif_body\n"
            "}\n"
        )
        self.assertCCode(
            IfStmt(
                None,
                [
                    IfClause(
                        None,
                        DummyExprRuntime("if_expr", Bool),
                        DummyStatementBlock([
                            DummyStmtRuntime("if_body"),
                        ])
                    ),
                    IfClause(
                        None,
                        DummyExprRuntime("elif_expr", Bool),
                        DummyStatementBlock([
                            DummyStmtRuntime("elif_body"),
                        ])
                    ),
                    ElseClause(
                        None,
                        DummyStatementBlock([
                            DummyStmtRuntime("else_body"),
                        ])
                    ),
                ]
            ),
            "if (DUMMY(if_expr)) {\n"
            "  // DUMMY if_body\n"
            "}\n"
            "else if (DUMMY(elif_expr)) {\n"
            "  // DUMMY elif_body\n"
            "}\n"
            "else {\n"
            "  // DUMMY else_body\n"
            "}\n"
        )
        self.assertCCode(
            IfStmt(
                None,
                [
                    IfClause(
                        None,
                        DummyExprRuntime("if_expr", Bool),
                        DummyStatementBlock([
                            DummyStmtRuntime("if_body"),
                        ])
                    ),
                    ElseClause(
                        None,
                        DummyStatementBlock([
                            DummyStmtRuntime("else_body"),
                        ])
                    ),
                ]
            ),
            "if (DUMMY(if_expr)) {\n"
            "  // DUMMY if_body\n"
            "}\n"
            "else {\n"
            "  // DUMMY else_body\n"
            "}\n"
        )
