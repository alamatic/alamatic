
from alamatic.ast import *
from alamatic.types import *
from alamatic.testutil import *


class TestWhileStmt(LanguageTestCase):

    def test_parse(self):
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

    def test_exec(self):
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
                ('InlineStatementBlock', (), [
                    ('StatementBlock', (), [
                        ('DummyStmtRuntime', ('block',), []),
                    ]),
                ]),
            ] * 3,
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

        # cond starts of known and then becomes unknown
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
                ('InlineStatementBlock', (), [
                    ('StatementBlock', (), [
                        ('DummyStmtRuntime', ('block',), []),
                    ]),
                ]),
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
