
from alamatic.ast import *
from alamatic.types import *
from alamatic.intermediate import *
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


class TestIntermediate(LanguageTestCase):

    def test_make(self):
        self.assertIntermediateForm(
            WhileStmt(
                None,
                DummyExpr("test"),
                StatementBlock([]),
            ),
            [
                ('Label', 0),
                ('DummyInstruction', ['test']),
                ('JumpIfFalseInstruction', [
                    ('DummyOperand', ['test']),
                    ('Label', 1),
                ]),
                ('JumpInstruction', [
                    ('Label', 0),
                ]),
                ('Label', 1),
            ],
        )
