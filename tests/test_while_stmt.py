
from alamatic.ast import *
from alamatic.types import *
from alamatic.testutil import *


class TestParse(LanguageTestCase):

    def test_simple(self):
        self.assertStmtParseTree(
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


class TestExec(LanguageTestCase):

    def test_cond_known_false(self):
        # cond known false at compile time
        self.assertCodegenTree(
            WhileStmt(
                None,
                DummyBooleanConstantExpr(False),
                StatementBlock([
                    DummyStmtRuntime("block")
                ]),
            ),
            [],
        )
        self.assertDataResult(
            {
                "a": DummyType(1),
            },
            WhileStmt(
                None,
                DummyBooleanConstantExpr(False),
                StatementBlock([
                    DummyAssignStmt("a", DummyType(2))
                ]),
            ),
            {
                "a": DummyType(1),
            },
        )

    def test_cond_known_first_true_then_false(self):
        # cond known at compile time, starts true and becomes false
        self.assertCodegenTree(
            [
                DummyDataDeclStmt("a", DummyType(0)),
                WhileStmt(
                    None,
                    DummyLessThanTestExpr("a", 3),
                    StatementBlock([
                        DummyIncrementStmt("a"),
                    ]),
                ),
            ],
            [],
        )
        self.assertCodegenTree(
            [
                DummyDataDeclStmt("a", DummyType(0)),
                WhileStmt(
                    None,
                    DummyLessThanTestExpr("a", 3),
                    StatementBlock([
                        DummyIncrementStmt("a"),
                        DummyStmtRuntime("block"),
                    ]),
                ),
            ],
            [
                ('WhileStmt', (), [
                    ('DummyLessThanTestExpr', ('a', 3), []),
                    ('StatementBlock', (), [
                        ('DummyIncrementStmt', ('a', 1), []),
                        ('DummyStmtRuntime', ('block',), []),
                    ]),
                ]),
            ],
        )
        self.assertDataResult(
            {
                "a": DummyType(0),
            },
            WhileStmt(
                None,
                DummyLessThanTestExpr("a", 3),
                StatementBlock([
                    DummyIncrementStmt("a"),
                ]),
            ),
            {
                "a": DummyType(3),
            },
        )

    def test_cond_not_known(self):
        # cond not known at compile time
        self.assertCodegenTree(
            WhileStmt(
                None,
                DummyExprRuntime("cond", Bool),
                StatementBlock([
                    DummyStmtRuntime("block")
                ]),
            ),
            [
                ('WhileStmt', (), [
                    ('DummyExprRuntime', ('cond', Bool), []),
                    ('StatementBlock', (), [
                        ('DummyStmtRuntime', ('block',), []),
                    ]),
                ]),
            ],
        )
        self.assertDataResult(
            {
                "a": DummyType(1),
            },
            WhileStmt(
                None,
                DummyExprRuntime("cond", Bool),
                StatementBlock([
                    DummyAssignStmt("a", DummyType(2))
                ]),
            ),
            {
                # Value of 'a' is now unknown, since we don't know if the
                # while block ran or not.
                "a": None,
            },
        )

    def test_cond_starts_known_then_unknown(self):
        # cond starts off known and then becomes unknown
        self.assertCodegenTree(
            [
                DummyDataDeclStmt("a", DummyType(0)),
                WhileStmt(
                    None,
                    DummyLessThanTestExpr("a", 3),
                    StatementBlock([
                        DummyAssignStmt("a", None),
                    ]),
                ),
            ],
            [
                ('WhileStmt', (), [
                    ('DummyLessThanTestExpr', ('a', 3), []),
                    ('StatementBlock', (), []),
                ])
            ],
        )
        self.assertCodegenTree(
            [
                DummyDataDeclStmt("a", DummyType(0)),
                WhileStmt(
                    None,
                    DummyLessThanTestExpr("a", 3),
                    StatementBlock([
                        DummyStmtRuntime("block"),
                        DummyAssignStmt("a", None),
                    ]),
                ),
            ],
            [
                ('WhileStmt', (), [
                    ('DummyLessThanTestExpr', ('a', 3), []),
                    ('StatementBlock', (), [
                        ('DummyStmtRuntime', ('block',), []),
                    ]),
                ]),
            ],
        )
        self.assertDataResult(
            {
                "a": DummyType(0),
            },
            WhileStmt(
                None,
                DummyLessThanTestExpr("a", 3),
                StatementBlock([
                    DummyAssignStmt("a", None),
                ]),
            ),
            {
                # Value of 'a' is now unknown, since we know the block
                # ran at least once and left it in an unknown state.
                "a": None,
            },
        )

    def test_unknown_test_known_body(self):

        test_stmt = WhileStmt(
            None,
            DummyExprRuntime("cond", Bool),
            StatementBlock([
                DummyIncrementStmt("a"),
                IfStmt(
                    None,
                    [
                        IfClause(
                            None,
                            DummyLessThanTestExpr("a", 10),
                            StatementBlock([]),
                        ),
                        ElseClause(
                            None,
                            StatementBlock([
                                DummyAssignStmt("b", DummyType(True)),
                                DummyStmtRuntime('else'),
                            ]),
                        ),
                    ],
                ),
            ]),
        )

        self.assertDataResult(
            {
                "a": DummyType(0),
                "b": DummyType(False),
            },
            test_stmt,
            {
                "a": None,
                "b": None,
            }
        )

        self.assertCodegenTree(
            [
                DummyDataDeclStmt("a", DummyType(0)),
                DummyDataDeclStmt("b", DummyType(False)),
                test_stmt,
            ],
            [
                ('WhileStmt', (), [
                    ('DummyExprRuntime', ('cond', Bool), []),
                    ('StatementBlock', (), [
                        ('DummyIncrementStmt', ('a', 1), []),
                        ('IfStmt', (), [
                            ('IfClause', (), [
                                ('DummyLessThanTestExpr', ("a", 10), []),
                                ('StatementBlock', (), []),
                            ]),
                            ('ElseClause', (), [
                                ('StatementBlock', (), [
                                    ('DummyStmtRuntime', ('else',), []),
                                ]),
                            ]),
                        ]),
                    ]),
                ]),
            ],
        )

        # We should still be able to evaluate at compile time things that
        # are *not* mutated inside the loop.
        test_stmt_2 = WhileStmt(
            None,
            DummyExprRuntime("cond", Bool),
            StatementBlock([
                DummyIncrementStmt("a"),
                IfStmt(
                    None,
                    [
                        IfClause(
                            None,
                            DummyExprCompileTime('dummy', Bool(True)),
                            StatementBlock([]),
                        ),
                        ElseClause(
                            None,
                            StatementBlock([
                                DummyAssignStmt("b", DummyType(True)),
                                DummyStmtRuntime("else"),
                            ]),
                        ),
                    ],
                ),
            ]),
        )
        self.assertCodegenTree(
            [
                DummyDataDeclStmt("a", DummyType(0)),
                DummyDataDeclStmt("b", DummyType(False)),
                test_stmt_2,
            ],
            [
                ('WhileStmt', (), [
                    ('DummyExprRuntime', ('cond', Bool), []),
                    ('StatementBlock', (), [
                        ('DummyIncrementStmt', ('a', 1), []),
                        ('InlineStatementBlock', (), [
                            ('StatementBlock', (), []),
                        ]),
                    ]),
                ]),
            ],
        )


class TestCodegen(LanguageTestCase):

    def test_simple(self):
        self.assertCCode(
            WhileStmt(
                None,
                DummyExprRuntime("test_expr", Bool),
                DummyStatementBlock([
                    DummyStmtRuntime("body"),
                ]),
            ),
            "while (DUMMY(test_expr)) {\n"
            "  // DUMMY body\n"
            "}\n"
        )
