
from alamatic.ast import *
from alamatic.types import *
from alamatic.intermediate import *
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


class TestIntermediate(LanguageTestCase):

    def test_if(self):
        self.assertIntermediateForm(
            IfStmt(
                None,
                [
                    IfClause(
                        None,
                        DummyExpr("if_expr"),
                        StatementBlock([
                            DummyStmt("if_block"),
                        ]),
                    ),
                ]
            ),
            [
                ('DummyOperation', ['if_expr']),
                ('JumpIfFalseOperation', [
                    ('DummyOperand', ['if_expr']),
                    ('Label', 0),
                ]),
                ('DummyOperation', ['if_block']),
                ('JumpOperation', [
                    ('Label', 1),
                ]),
                # This pair of labels together looks redundant, but at this
                # stage it's important because our interpreter phase depends
                # on all conditional branches having at least one basic
                # block for both true and false, even if one is empty as
                # shown here.
                ('Label', 0),
                ('Label', 1),
            ],
        )

    def test_if_else(self):
        self.assertIntermediateForm(
            IfStmt(
                None,
                [
                    IfClause(
                        None,
                        DummyExpr("if_expr"),
                        StatementBlock([
                            DummyStmt("if_block"),
                        ]),
                    ),
                    ElseClause(
                        None,
                        StatementBlock([
                            DummyStmt("else_block"),
                        ]),
                    ),
                ]
            ),
            [
                ('DummyOperation', ['if_expr']),
                ('JumpIfFalseOperation', [
                    ('DummyOperand', ['if_expr']),
                    ('Label', 0),
                ]),
                ('DummyOperation', ['if_block']),
                ('JumpOperation', [
                    ('Label', 1),
                ]),
                ('Label', 0),
                ('DummyOperation', ['else_block']),
                ('Label', 1),
            ],
        )
