
from alamatic.ast import *
from alamatic.intermediate import *
from alamatic.testutil import *


class TestParse(LanguageTestCase):

    def test_parse_break(self):
        self.assertStmtParseTree(
            "break",
            [
                ("BreakStmt", (), []),
            ]
        )

    def test_parse_continue(self):
        self.assertStmtParseTree(
            "continue",
            [
                ("ContinueStmt", (), []),
            ]
        )


class TestIntermediate(LanguageTestCase):

    def test_break(self):
        symbols = SymbolTable()
        symbols.break_label = Label(position=('label', 1, 0))
        symbols.break_label._test_index = 4
        stmt = BreakStmt(position=('break', 1, 0))
        elems = []
        stmt.make_intermediate_form(elems, symbols)
        self.assertEqual(
            element_comparison_nodes(elems),
            [
                ('JumpInstruction', [
                    ('Label', 4),
                ]),
            ],
        )
        self.assertEqual(
            stmt.jump_type_name,
            'break',
        )

    def test_continue(self):
        symbols = SymbolTable()
        symbols.continue_label = Label(position=('label', 1, 0))
        symbols.continue_label._test_index = 5
        stmt = ContinueStmt(position=('continue', 1, 0))
        elems = []
        stmt.make_intermediate_form(elems, symbols)
        self.assertEqual(
            element_comparison_nodes(elems),
            [
                ('JumpInstruction', [
                    ('Label', 5),
                ]),
            ],
        )
        self.assertEqual(
            stmt.jump_type_name,
            'continue',
        )

    def test_outside_loop(self):

        got_symbols = []

        class Dummy(LoopJumpStmt):

            def get_target_label(self, symbols):
                got_symbols.append(symbols)
                return None

            @property
            def jump_type_name(self):
                return 'dummy'

        symbols = SymbolTable()
        stmt = Dummy(position=('dummy', 2, 3))
        elems = []

        self.assertRaises(
            LoopJumpStmt.NotInLoopError,
            lambda: stmt.make_intermediate_form(elems, symbols)
        )
        self.assertEqual(
            len(got_symbols),
            1,
        )
        self.assertEqual(
            got_symbols[0],
            symbols,
        )
