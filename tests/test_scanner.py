
import unittest
from StringIO import StringIO
from alamatic.compiler import CompileState
from alamatic.scanner import Scanner, IndentationError, UnexpectedTokenError
from plex.errors import UnrecognizedInput


NEWLINE = ('NEWLINE', '\n')
INDENT = ('INDENT', 4)
OUTDENT = ('OUTDENT', '')


def NUMBER(val):
    return ('NUMBER', str(val))


def STRINGLIT(val):
    return ('STRINGLIT', str(val))


def IDENT(val):
    return ('IDENT', str(val))


def PUNCT(val):
    return (str(val), str(val))


class TestScanner(unittest.TestCase):

    def assertTokens(self, inp, expected_tokens, expression_only=False):
        state = CompileState()
        stream = StringIO(inp)
        scanner = Scanner(state, stream, expression_only=expression_only)
        got_tokens = []
        while True:
            got_token = scanner.read()
            if got_token[0] != "EOF":
                got_tokens.append(got_token)
            else:
                break
        self.assertEqual(
            got_tokens,
            expected_tokens,
        )

    def assertScanError(self, inp, errtype, line, char):
        state = CompileState()
        stream = StringIO(inp)
        scanner = Scanner(state, stream)
        try:
            while True:
                got_token = scanner.read()
                if got_token[0] == "EOF":
                    break
        except errtype, ex:
            if ex.position[1] != line or ex.position[2] != char:
                self.fail(
                    "Expected %s at line %i char %i, but got that error "
                    "at line %i char %i" % (
                        errtype.__name__, line, char,
                        ex.position[1], ex.position[2],
                    )
                )
            else:
                return
        self.fail(
            "Expected %s at line %i char %i, but got no error at all" % (
                errtype.__name__, line, char,
            ),
        )

    def assertTokenError(self, inp, line, char):
        self.assertScanError(inp, UnrecognizedInput, line, char)

    def assertIndentError(self, inp, line, char):
        self.assertScanError(inp, IndentationError, line, char)

    def test_indentation(self):
        self.assertTokens(
            "1\n"
            "    2\n"
            "\n"
            "    3\n"
            "\n"  # blank line during indent
            "        4\n"
            "            5\n"
            "\n"  # blank line during outdent
            "    6",
            [
                NUMBER(1),
                NEWLINE,
                INDENT,
                NUMBER(2),
                NEWLINE,
                NEWLINE,
                NUMBER(3),
                NEWLINE,
                NEWLINE,
                INDENT,
                NUMBER(4),
                NEWLINE,
                INDENT,
                NUMBER(5),
                NEWLINE,
                NEWLINE,
                OUTDENT,
                OUTDENT,
                NUMBER(6),
                NEWLINE,
                OUTDENT,
            ]
        )
        # Initial spaces surface as an indent too
        # (which will ultimately fail in the parser, since indent can't
        #  begin a statement or expression)
        self.assertTokens(
            "    1",
            [
                INDENT,
                NUMBER(1),
                NEWLINE,
                OUTDENT,
            ]
        )
        # Inconsistent outdenting is an error
        self.assertIndentError(
            "    1\n"
            "  2",
            2, 0,
        )
        # Indentation and newlines are ignored inside brackets
        self.assertTokens(
            "(\n    1)\n[\n    1]\n{\n    1}\n    (",
            [
                PUNCT('('),
                NUMBER(1),
                PUNCT(')'),
                NEWLINE,
                PUNCT('['),
                NUMBER(1),
                PUNCT(']'),
                NEWLINE,
                PUNCT('{'),
                NUMBER(1),
                PUNCT('}'),
                NEWLINE,
                INDENT,
                # We shouldn't see closing indent or newline
                # if we end with a bracket open.
                PUNCT('('),
            ]
        )
        # An empty string still yields a virtual newline.
        self.assertTokens("", [NEWLINE])
        self.assertTokens("    ", [INDENT, NEWLINE, OUTDENT])

    def test_numbers(self):
        # Decimal
        self.assertTokens(
            "0 1 2 3 4 5 6 7 8 9 10 92 1.1 1.12 1E+3 1E-4 1.2E+3 1.2E-2",
            [
                NUMBER("0"),
                NUMBER("1"),
                NUMBER("2"),
                NUMBER("3"),
                NUMBER("4"),
                NUMBER("5"),
                NUMBER("6"),
                NUMBER("7"),
                NUMBER("8"),
                NUMBER("9"),
                NUMBER("10"),
                NUMBER("92"),
                NUMBER("1.1"),
                NUMBER("1.12"),
                NUMBER("1E+3"),
                NUMBER("1E-4"),
                NUMBER("1.2E+3"),
                NUMBER("1.2E-2"),
                NEWLINE,
            ]
        )
        # Octal
        self.assertTokens(
            "01 02 03 04 05 06 07 012 076",
            [
                NUMBER("01"),
                NUMBER("02"),
                NUMBER("03"),
                NUMBER("04"),
                NUMBER("05"),
                NUMBER("06"),
                NUMBER("07"),
                NUMBER("012"),
                NUMBER("076"),
                NEWLINE,
            ]
        )
        # Hexadecimal
        self.assertTokens(
            "0x1 0x2 0x3 0x4 0x5 0x6 0x7 0x8 0x9 0xa 0xb 0xc 0xd 0xe 0xf "
            "0xA 0xB 0xC 0xD 0xE 0xF 0x1A 0xA3 0x00 0xFF 0xblah",
            [
                NUMBER("0x1"),
                NUMBER("0x2"),
                NUMBER("0x3"),
                NUMBER("0x4"),
                NUMBER("0x5"),
                NUMBER("0x6"),
                NUMBER("0x7"),
                NUMBER("0x8"),
                NUMBER("0x9"),
                NUMBER("0xa"),
                NUMBER("0xb"),
                NUMBER("0xc"),
                NUMBER("0xd"),
                NUMBER("0xe"),
                NUMBER("0xf"),
                NUMBER("0xA"),
                NUMBER("0xB"),
                NUMBER("0xC"),
                NUMBER("0xD"),
                NUMBER("0xE"),
                NUMBER("0xF"),
                NUMBER("0x1A"),
                NUMBER("0xA3"),
                NUMBER("0x00"),
                NUMBER("0xFF"),
                NUMBER("0xblah"),
                NEWLINE,
            ]
        )
        # Binary
        self.assertTokens(
            "0x00000000 0x00000001 0x11111111 0x0 0x1 0x00 0x11 0x35 0x99",
            [
                NUMBER("0x00000000"),
                NUMBER("0x00000001"),
                NUMBER("0x11111111"),
                NUMBER("0x0"),
                NUMBER("0x1"),
                NUMBER("0x00"),
                NUMBER("0x11"),
                NUMBER("0x35"),
                NUMBER("0x99"),
                NEWLINE,
            ]
        )

        self.assertTokens("12af", [
            NUMBER("12"),
            IDENT("af"),
            NEWLINE,
        ])
        self.assertTokens("0b11af", [
            NUMBER("0b11"),
            IDENT("af"),
            NEWLINE,
        ])

    def test_stringlit(self):
        self.assertTokens(
            " ".join([
                '"abc"',
                '""',
                r'"\n"',
                r'"\r"',
                r'"\t"',
                r'"\e"',
                r'"\""',
                r'"\x12"',
                r'"\xab"',
                r'"\xAB"',
                r'"\xaB"',
                r'"\x"',
                r'"\q"',
                r'"\a"',
            ]),
            [
                STRINGLIT('"abc"'),
                STRINGLIT('""'),
                STRINGLIT(r'"\n"'),
                STRINGLIT(r'"\r"'),
                STRINGLIT(r'"\t"'),
                STRINGLIT(r'"\e"'),
                STRINGLIT(r'"\""'),
                STRINGLIT(r'"\x12"'),
                STRINGLIT(r'"\xab"'),
                STRINGLIT(r'"\xAB"'),
                STRINGLIT(r'"\xaB"'),
                STRINGLIT(r'"\x"'),
                STRINGLIT(r'"\q"'),
                STRINGLIT(r'"\a"'),
                NEWLINE,
            ]
        )

    def test_ident(self):
        self.assertTokens(
            "abc a123 ab1b _foo _1234 foo_bar ABC aBc Abc",
            [
                IDENT("abc"),
                IDENT("a123"),
                IDENT("ab1b"),
                IDENT("_foo"),
                IDENT("_1234"),
                IDENT("foo_bar"),
                IDENT("ABC"),
                IDENT("aBc"),
                IDENT("Abc"),
                NEWLINE,
            ]
        )

    def test_punct(self):
        self.assertTokens(
            "| & ^ = < > * / % ~ + - : , == != <= >=",
            [
                PUNCT("|"),
                PUNCT("&"),
                PUNCT("^"),
                PUNCT("="),
                PUNCT("<"),
                PUNCT(">"),
                PUNCT("*"),
                PUNCT("/"),
                PUNCT("%"),
                PUNCT("~"),
                PUNCT("+"),
                PUNCT("-"),
                PUNCT(":"),
                PUNCT(","),
                PUNCT("=="),
                PUNCT("!="),
                PUNCT("<="),
                PUNCT(">="),
                NEWLINE,
            ]
        )

    def test_realistic(self):
        self.assertTokens(
            "\n"
            "if foo == 2:\n"
            "    baz(\"foo is 2!\")\n"
            "else:\n"
            "    bar(\n"
            "        12.3E+2,\n"
            "        0xef,\n"
            "        True,\n"
            "    )",
            [
                NEWLINE,
                IDENT("if"),
                IDENT("foo"),
                PUNCT("=="),
                NUMBER("2"),
                PUNCT(":"),
                NEWLINE,
                INDENT,
                IDENT("baz"),
                PUNCT("("),
                STRINGLIT('"foo is 2!"'),
                PUNCT(")"),
                NEWLINE,
                OUTDENT,
                IDENT("else"),
                PUNCT(":"),
                NEWLINE,
                INDENT,
                IDENT("bar"),
                PUNCT("("),
                NUMBER("12.3E+2"),
                PUNCT(","),
                NUMBER("0xef"),
                PUNCT(","),
                IDENT("True"),
                PUNCT(","),
                PUNCT(")"),
                NEWLINE,
                OUTDENT,
            ]
        )

    def test_expression_only(self):
        self.assertTokens(
            "\n"
            "a = (2 + 3)\n"
            "     * 5\n",
            [
                IDENT("a"),
                PUNCT("="),
                PUNCT("("),
                NUMBER("2"),
                PUNCT("+"),
                NUMBER("3"),
                PUNCT(")"),
                PUNCT("*"),
                NUMBER("5"),
            ],
            expression_only=True,
        )

        # Make sure extra closing brackets don't allow us to
        # "escape" back into non-expression scanning land
        self.assertTokens(
            "):\n"
            "    a",
            [
                PUNCT(")"),
                PUNCT(":"),
                IDENT("a"),
            ],
            expression_only=True,
        )

    def test_parser_interface(self):
        inp = "    if a == b"
        stream = StringIO(inp)
        state = CompileState()
        scanner = Scanner(state, stream)

        # indent
        self.assertEqual(scanner.peek(), INDENT)
        self.assertTrue(scanner.next_is_indent())
        self.assertEqual(scanner.read(), INDENT)

        # if
        self.assertEqual(scanner.peek(), IDENT("if"))
        self.assertTrue(scanner.next_is_keyword("if"))
        self.assertFalse(scanner.next_is_keyword("else"))
        self.assertFalse(scanner.next_is_punct("if"))
        self.assertEqual(scanner.require_keyword("if"), IDENT("if"))
        self.assertRaises(
            UnexpectedTokenError,
            lambda: scanner.require_newline(),
        )
        self.assertRaises(
            UnexpectedTokenError,
            lambda: scanner.require_indent(),
        )
        self.assertRaises(
            UnexpectedTokenError,
            lambda: scanner.require_outdent(),
        )

        # a
        self.assertEqual(scanner.peek(), IDENT("a"))
        self.assertEqual(scanner.read(), IDENT("a"))
        self.assertRaises(
            UnexpectedTokenError,
            lambda: scanner.require_keyword("if"),
        )

        # ==
        self.assertEqual(scanner.peek(), PUNCT("=="))
        self.assertFalse(scanner.next_is_keyword("=="))
        self.assertTrue(scanner.next_is_punct("=="))
        self.assertFalse(scanner.next_is_punct("="))
        self.assertEqual(scanner.require_punct("=="), PUNCT("=="))

        # b
        self.assertEqual(scanner.peek(), IDENT("b"))
        self.assertFalse(scanner.next_is_newline())
        self.assertFalse(scanner.next_is_indent())
        self.assertFalse(scanner.next_is_outdent())
        self.assertEqual(scanner.read(), IDENT("b"))

        # implied newline
        self.assertEqual(scanner.peek(), NEWLINE)
        self.assertTrue(scanner.next_is_newline())
        self.assertFalse(scanner.next_is_outdent())
        self.assertEqual(scanner.require_newline(), NEWLINE)

        # outdent
        self.assertEqual(scanner.peek(), OUTDENT)
        self.assertTrue(scanner.next_is_outdent())
        self.assertEqual(scanner.read(), OUTDENT)

        # eof
        self.assertEqual(scanner.peek(), ('EOF', ''))
        self.assertTrue(scanner.next_is_eof())
        self.assertFalse(scanner.next_is_newline())
        self.assertFalse(scanner.next_is_indent())
        self.assertFalse(scanner.next_is_outdent())
        self.assertFalse(scanner.next_is_punct("="))
        self.assertFalse(scanner.next_is_keyword("else"))
        self.assertEqual(scanner.read(), ('EOF', ''))
