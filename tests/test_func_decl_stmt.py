
from alamatic.ast import *
from alamatic.types import *
from alamatic.testutil import *


class TestParse(LanguageTestCase):

    def test_simple_parse(self):
        self.assertStmtParseTree(
            'func doot(a, b as foo):\n'
            '    pass',
            [
                ('FuncDeclStmt', (), [
                    ('FuncDeclClause', ('doot',), [
                        ('ParamDeclClause', ('a',), []),
                        ('ParamDeclClause', ('b',), [
                            ('SymbolNameExpr', ('foo',), []),
                        ]),
                    ]),
                    ('StatementBlock', (), [
                        ('PassStmt', (), []),
                    ]),
                ]),
            ]
        )


class TestExec(LanguageTestCase):

    def test_simple_exec(self):
        stmt = FuncDeclStmt(
            None,
            FuncDeclClause(
                None,
                'foo',
                [],  # no params
            ),
            StatementBlock([]),  # no statements
        )

        # Function declarations generate no runtime statements, because
        # function templates don't exist as a runtime concept.
        self.assertCodegenTree(
            stmt,
            [],
        )

        result = execute_stmts(
            stmt,
            {},
        )

        expected_data = {
            "foo": FunctionTemplate(
                stmt,
                result.root_symbols,
            ),
        }

        self.assertEqual(
            result.global_data,
            expected_data,
        )
