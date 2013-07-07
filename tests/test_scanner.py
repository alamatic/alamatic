
import unittest
from StringIO import StringIO
from alamatic.scanner import Scanner, IndentationError
from plex.errors import UnrecognizedInput


NEWLINE = ('NEWLINE', '\n')
INDENT = ('INDENT', '')
OUTDENT = ('OUTDENT', '')
def INTEGER(val):
    return ('INTEGER', str(val))
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
                if got_token[0] == None:
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
                INTEGER(1),
                NEWLINE,
                INDENT,
                INTEGER(2),
                NEWLINE,
                NEWLINE,
                INTEGER(3),
                NEWLINE,
                INDENT,
                INTEGER(4),
                NEWLINE,
                INDENT,
                INTEGER(5),
                NEWLINE,
                OUTDENT,
                OUTDENT,
                INTEGER(6),
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
                INTEGER(1),
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
                INTEGER(1),
                LIT(')'),
                NEWLINE,
                LIT('['),
                INTEGER(1),
                LIT(']'),
                NEWLINE,
                LIT('{'),
                INTEGER(1),
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
