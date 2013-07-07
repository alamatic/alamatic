
import plex
from plex import (
    Rep,
    Rep1,
    Range,
    Any,
    AnyBut,
    Eof,
    State,
    Str,
    Opt,
    TEXT,
    IGNORE,
)


class Scanner(plex.Scanner):

    def handle_newline(self, text):
        if self.bracket_count == 0:
            self.begin('indent')
            return 'NEWLINE'

    def handle_indentation(self, text):
        current_level = self.indents[-1]
        new_level = len(text)
        if new_level > 0 and text[-1] == "\n":
            # Blank line, so skip.
            self.produce('NEWLINE', "\n")
            self.begin('')
            return

        if new_level > current_level:
            self.indents.append(new_level)
            self.produce('INDENT', '')
        elif new_level < current_level:
            self.outdent_to(new_level)
        self.begin('')

    def handle_open_bracket(self, text):
        self.bracket_count = self.bracket_count + 1
        return text

    def handle_close_bracket(self, text):
        if self.bracket_count > 0:
            self.bracket_count = self.bracket_count - 1
        return text

    def eof(self):
        # If there is inconsistent bracket nesting then we'll just return
        # a bare EOF token and let the parser deal with it.
        if self.bracket_count == 0:
            # Always end on a newline, so we can just assume that all
            # lines have ends in the parser.
            self.produce("NEWLINE", "\n")
            self.outdent_to(0)
        self.produce("EOF")

    def outdent_to(self, new_level):
        while new_level < self.indents[-1]:
            self.indents.pop()
            self.produce('OUTDENT', '')
        if self.indents[-1] != new_level:
            raise IndentationError(self.position())

    digit = Range("09")
    letter = Range("azAZ")
    decimal_or_octal_number = (
        (
            Rep1(digit) + Opt(
                Str(".") + Rep1(digit)
            )
        ) + Opt(
            Str("E") + Any("+-") + Rep1(digit)
        )
    )
    hex_number = (
        # We actually slurp up all letters even though only a-f are valid
        # here, so that "0xfg" will parse as a single token that we can
        # report an explicit error for, rather than parsing as "0xf", "g"
        # that will probably just manifest as an unexpected token.
        Str("0x") + Rep1(Range("09azAZ"))
    )
    binary_number = (
        # Slurp up all decimal digits even though only 0 and 1 are valid
        # here, because otherwise "0b02" gets parsed as "0b0", "2" and
        # that would cause a confusing error at parse time; this way we
        # can fail when the parser tries to make sense of the whole number
        # and thus emit a sensible error message.
        Str("0b") + Rep1(digit)
    )

    string_literal = (
        Str('"') + Rep(
            (Str("\\") + (
                # Not all of these escapes are valid, but we'll handle that
                # at parsing time so we can show a nice error message rather
                # than just a token mismatch.
                Any("abcdefghijklmnopqrstuvwxyz\\\"")
            )) | AnyBut("\\\"")
        ) + Str('"')
    )

    ident = (
        (letter | Str("_")) + Rep(letter | Str("_") | digit)
    )

    punct = (
        Any("|&^=<>*/%~+-:,") |
        Str("==") |
        Str("!=") |
        Str("<=") |
        Str(">=")
    )

    lexicon = plex.Lexicon([
        (decimal_or_octal_number | hex_number | binary_number, 'NUMBER'),
        (string_literal, 'STRINGLIT'),
        (ident, 'IDENT'),
        (Any("({["), handle_open_bracket),
        (Any(")}]"), handle_close_bracket),
        ((Str("\n") | Eof), handle_newline),
        (punct, TEXT),
        (Rep1(Str(' ')), IGNORE),
        State('indent', [
            (Rep(Str(" ")) + Opt(Str("\n")), handle_indentation),
        ]),
    ])

    def __init__(self, stream, name=None):
        plex.Scanner.__init__(self, self.lexicon, stream=stream, name=name)

        self.seen_one_indent = False
        self.indents = [0]
        self.bracket_count = 0
        self.begin('indent')
        self.peeked = None

    def read(self):
        result = self.peek()
        self.peeked = None
        return result

    def peek(self):
        if self.peeked is None:
            self.peeked = plex.Scanner.read(self)
            # Skip Plex's generated "EOF" token (where the type is None)
            # since we have our own explicit EOF token.
            if self.peeked[0] is None:
                self.peeked = plex.Scanner.read(self)
        return self.peeked

    def next_is_punct(self, symbol):
        token = self.peek()
        return (token[0] == symbol and token[1] == symbol)

    def next_is_keyword(self, name):
        token = self.peek()
        return (token[0] == "IDENT" and token[1] == name)

    def next_is_newline(self):
        return (self.peek()[0] == "NEWLINE")

    def next_is_indent(self):
        return (self.peek()[0] == "INDENT")

    def next_is_outdent(self):
        return (self.peek()[0] == "OUTDENT")

    def next_is_eof(self):
        return (self.peek()[0] == "EOF")

    def require_punct(self, symbol):
        if not self.next_is_punct(symbol):
            raise UnexpectedTokenError(
                "Expected %r but got %r" % (
                    symbol, self.token_display_name(self.peek())
                ),
                self.position(),
            )
        return self.read()

    def require_keyword(self, name):
        if not self.next_is_keyword(name):
            raise UnexpectedTokenError(
                "Expected %r but got %r" % (
                    name, self.token_display_name(self.peek())
                ),
                self.position(),
            )
        return self.read()

    def require_indent(self):
        if not self.next_is_indent():
            raise UnexpectedTokenError(
                "Expected indent but got %r" % (
                    self.token_display_name(self.peek())
                ),
                self.position(),
            )
        return self.read()

    def require_outdent(self):
        if not self.next_is_outdent():
            raise UnexpectedTokenError(
                "Expected outdent but got %r" % (
                    self.token_display_name(self.peek())
                ),
                self.position(),
            )
        return self.read()

    def require_newline(self):
        if not self.next_is_newline():
            raise UnexpectedTokenError(
                "Expected newline but got %r" % (
                    self.token_display_name(self.peek())
                ),
                self.position(),
            )
        return self.read()

    def token_display_name(self, token):
        if token[0] == "NEWLINE":
            return "newline"
        elif token[0] == "INDENT":
            return "indent"
        elif token[0] == "OUTDENT":
            return "outdent"
        elif token[0] == "EOF":
            return "end of file"
        else:
            return token[1]


class IndentationError(Exception):
    def __init__(self, position):
        Exception.__init__(
            self, "Inconsistent indentation at %s line %i" % (
                position[0], position[1],
            )
        )
        self.position = position


class UnexpectedTokenError(Exception):
    def __init__(self, message, position):
        Exception.__init__(
            self, message,
        )
        self.position = position
