
from alamatic.ast import *
from alamatic.types import *
from alamatic.testutil import *


class TestParse(LanguageTestCase):

    def test_just_if(self):
        self.assertStmtParseTree(
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

    def test_if_else(self):
        self.assertStmtParseTree(
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

    def test_if_elif_elif(self):
        self.assertStmtParseTree(
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

    def test_if_elif_else(self):
        self.assertStmtParseTree(
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


class TestExec(LanguageTestCase):

    def test_known_true_no_else(self):

        # if true with no else
        self.assertCodegenTree(
            IfStmt(
                None,
                [
                    IfClause(
                        None,
                        DummyBooleanConstantExpr(True),
                        StatementBlock([
                            DummyStmtRuntime("if")
                        ])
                    ),
                ]
            ),
            [
                ('InlineStatementBlock', (), [
                    ('StatementBlock', (), [
                        ('DummyStmtRuntime', ('if',), []),
                    ]),
                ]),
            ],
        )
        self.assertDataResult(
            {
                "a": DummyType(1),
            },
            IfStmt(
                None,
                [
                    IfClause(
                        None,
                        DummyBooleanConstantExpr(True),
                        StatementBlock([
                            DummyAssignStmt('a', DummyType(2))
                        ])
                    ),
                ]
            ),
            {
                "a": DummyType(2),
            },
        )

    def test_known_false_no_else(self):

        # if false with no else
        self.assertCodegenTree(
            IfStmt(
                None,
                [
                    IfClause(
                        None,
                        DummyBooleanConstantExpr(False),
                        StatementBlock([
                            DummyStmtRuntime("if")
                        ])
                    ),
                ]
            ),
            [],
        )
        self.assertDataResult(
            {
                "a": DummyType(1),
            },
            IfStmt(
                None,
                [
                    IfClause(
                        None,
                        DummyBooleanConstantExpr(False),
                        StatementBlock([
                            DummyAssignStmt('a', DummyType(2))
                        ])
                    ),
                ]
            ),
            {
                "a": DummyType(1),
            },
        )

    def test_known_true_with_else(self):
        # if true with else
        self.assertCodegenTree(
            IfStmt(
                None,
                [
                    IfClause(
                        None,
                        DummyBooleanConstantExpr(True),
                        StatementBlock([
                            DummyStmtRuntime("if")
                        ])
                    ),
                    ElseClause(
                        None,
                        StatementBlock([
                            DummyStmtRuntime("else")
                        ])
                    ),
                ]
            ),
            [
                ('InlineStatementBlock', (), [
                    ('StatementBlock', (), [
                        ('DummyStmtRuntime', ('if',), []),
                    ]),
                ]),
            ],
        )

    def test_known_false_with_else(self):
        # if false with else
        self.assertCodegenTree(
            IfStmt(
                None,
                [
                    IfClause(
                        None,
                        DummyBooleanConstantExpr(False),
                        StatementBlock([
                            DummyStmtRuntime("if")
                        ])
                    ),
                    ElseClause(
                        None,
                        StatementBlock([
                            DummyStmtRuntime("else")
                        ])
                    ),
                ]
            ),
            [
                ('InlineStatementBlock', (), [
                    ('StatementBlock', (), [
                        ('DummyStmtRuntime', ('else',), []),
                    ]),
                ]),
            ],
        )

    def test_not_known(self):
        # if unknown with else
        self.assertCodegenTree(
            IfStmt(
                None,
                [
                    IfClause(
                        None,
                        DummyExprRuntime("cond", Bool),
                        StatementBlock([
                            DummyStmtRuntime("if")
                        ])
                    ),
                    IfClause(
                        None,
                        DummyExprRuntime("cond", Bool),
                        StatementBlock([
                            DummyStmtRuntime("elif")
                        ])
                    ),
                    ElseClause(
                        None,
                        StatementBlock([
                            DummyStmtRuntime("else")
                        ])
                    ),
                ]
            ),
            [
                ('IfStmt', (), [
                    ('IfClause', (), [
                        ('DummyExprRuntime', ('cond', Bool), []),
                        ('StatementBlock', (), [
                            ('DummyStmtRuntime', ('if',), []),
                        ]),
                    ]),
                    ('IfClause', (), [
                        ('DummyExprRuntime', ('cond', Bool), []),
                        ('StatementBlock', (), [
                            ('DummyStmtRuntime', ('elif',), []),
                        ]),
                    ]),
                    ('ElseClause', (), [
                        ('StatementBlock', (), [
                            ('DummyStmtRuntime', ('else',), []),
                        ]),
                    ]),
                ]),
            ],
        )
        self.assertDataResult(
            {
                "a": DummyType(1),
            },
            IfStmt(
                None,
                [
                    IfClause(
                        None,
                        DummyExprRuntime("cond", Bool),
                        StatementBlock([
                            DummyAssignStmt('a', DummyType(2))
                        ])
                    ),
                ]
            ),
            {
                # We don't know the value of 'a' after the if block.
                "a": None,
            },
        )

    def test_elif_true_after_unknown_if(self):
        # elif true after unknown if (emitted as an 'else')
        self.assertCodegenTree(
            IfStmt(
                None,
                [
                    IfClause(
                        None,
                        DummyExprRuntime("cond", Bool),
                        StatementBlock([
                            DummyStmtRuntime("if")
                        ])
                    ),
                    IfClause(
                        None,
                        DummyBooleanConstantExpr(True),
                        StatementBlock([
                            DummyStmtRuntime("elif")
                        ])
                    ),
                    ElseClause(
                        None,
                        StatementBlock([
                            DummyStmtRuntime("else")
                        ])
                    ),
                ]
            ),
            [
                ('IfStmt', (), [
                    ('IfClause', (), [
                        ('DummyExprRuntime', ('cond', Bool), []),
                        ('StatementBlock', (), [
                            ('DummyStmtRuntime', ('if',), []),
                        ]),
                    ]),
                    ('ElseClause', (), [
                        ('StatementBlock', (), [
                            ('DummyStmtRuntime', ('elif',), []),
                        ]),
                    ]),
                ]),
            ],
        )

        # Now we need to test the scope management behavior.
    def test_same_assigns_pass_through(self):
        self.assertDataResult(
            {
                "a": DummyType(1),
            },
            IfStmt(
                None,
                [
                    IfClause(
                        None,
                        DummyExprRuntime("cond", Bool),
                        StatementBlock([
                            DummyAssignStmt('a', DummyType(2))
                        ])
                    ),
                    ElseClause(
                        None,
                        StatementBlock([
                            DummyAssignStmt('a', DummyType(2))
                        ])
                    ),
                ]
            ),
            {
                # Both sides of the if statement produce the same
                # value, so it's guaranteed here.
                "a": DummyType(2),
            },
        )
        self.assertDataResult(
            {
                "a": DummyType(1),
            },
            IfStmt(
                None,
                [
                    IfClause(
                        None,
                        DummyExprRuntime("cond", Bool),
                        StatementBlock([
                            DummyAssignStmt('a', DummyType(2))
                        ])
                    ),
                    IfClause(
                        None,
                        DummyBooleanConstantExpr(True),
                        StatementBlock([
                            DummyAssignStmt('a', DummyType(2))
                        ])
                    ),
                    ElseClause(
                        None,
                        StatementBlock([
                            DummyStmtRuntime("else")
                        ])
                    ),
                ]
            ),
            {
                # if and elif produce the same value, and we know that
                # the else case can never run because the elif is
                # known to be true, so the value is guaranteed.
                "a": DummyType(2),
            },
        )
        self.assertDataResult(
            {
                "a": DummyType(1),
            },
            IfStmt(
                None,
                [
                    IfClause(
                        None,
                        DummyExprRuntime("cond", Bool),
                        StatementBlock([
                            DummyAssignStmt('a', DummyType(2))
                        ])
                    ),
                    IfClause(
                        None,
                        DummyExprRuntime("cond", Bool),
                        StatementBlock([
                            DummyAssignStmt('a', DummyType(2))
                        ])
                    ),
                    ElseClause(
                        None,
                        StatementBlock([
                            DummyStmtRuntime("else")
                        ])
                    ),
                ]
            ),
            {
                # else clause doesn't update the value, and all clauses
                # could be chosen at runtime, so the value is unknown.
                "a": None,
            },
        )


class TestCodegen(LanguageTestCase):

    def test_if(self):
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

    def test_if_elif(self):
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

    def test_if_elif_else(self):
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

    def test_if_else(self):
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
