
import unittest
from StringIO import StringIO
from alamatic.scanner import Scanner, IndentationError
from plex.errors import UnrecognizedInput


NEWLINE = ('NEWLINE', '\n')
INDENT = ('INDENT', '')
OUTDENT = ('OUTDENT', '')
def NUMBER(val):
    return ('NUMBER', str(val))
def LIT(val):
    return (val, val)


class TestScanner(unittest.TestCase):

    def assertTokens(self, inp, expected_tokens):
        stream = StringIO(inp)
        scanner = Scanner(stream)
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
        stream = StringIO(inp)
        scanner = Scanner(stream)
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
            "        4\n"
            "            5\n"
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
                INDENT,
                NUMBER(4),
                NEWLINE,
                INDENT,
                NUMBER(5),
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
                LIT('('),
                NUMBER(1),
                LIT(')'),
                NEWLINE,
                LIT('['),
                NUMBER(1),
                LIT(']'),
                NEWLINE,
                LIT('{'),
                NUMBER(1),
                LIT('}'),
                NEWLINE,
                INDENT,
                # We shouldn't see closing indent or newline
                # if we end with a bracket open.
                LIT('('),
            ]
        )
        # An empty string still yields a virtual newline.
        self.assertTokens("", [ NEWLINE ])
        self.assertTokens("    ", [ INDENT, NEWLINE, OUTDENT ])

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

        # These will need to become a success condition with two tokens once
        # the scanner supports identifier tokens, but they're errors for now.
        self.assertTokenError("12af", 1, 2)
        self.assertTokenError("0b11af", 1, 4)
