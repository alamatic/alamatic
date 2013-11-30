
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
