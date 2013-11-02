
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
from plex.errors import UnrecognizedInput

from alamatic.compilelogging import CompilerError, pos_link


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
            return

        if new_level > current_level:
            self.indents.append(new_level)
            indent_change = new_level - current_level
            if indent_change != 4:
                position = self.position()
                # report it from the end of the whitespace rather than
                # the start.
                position = (position[0], position[1], indent_change - 1)
                self.state.warn(
                    "Blocks should be indented by 4 spaces, but ",
                    pos_link(position),
                    " indents by ", indent_change,
                )
            self.produce('INDENT', indent_change)
        elif new_level < current_level:
            self.outdent_to(new_level)
        self.begin('')

    def handle_open_bracket(self, text):
        self.bracket_count = self.bracket_count + 1
        return text

    def handle_close_bracket(self, text):
        if self.bracket_count > self.min_bracket_count:
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
        Any("|&^=<>*/%~+-:,.") |
        Str("==") |
        Str("!=") |
        Str("<=") |
        Str(">=") |
        Str("+=") |
        Str("-=") |
        Str("*=") |
        Str("/=") |
        Str("|=") |
        Str("&=") |
        Str("<<") |
        Str(">>")
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

    def __init__(self, state, stream, name=None, expression_only=False):
        plex.Scanner.__init__(self, self.lexicon, stream=stream, name=name)

        self.state = state
        self.seen_one_indent = False
        self.indents = [0]
        if expression_only:
            # For parsing expressions we just pretend there's always
            # one bracket open.
            self.bracket_count = 1
        else:
            self.bracket_count = 0
        self.min_bracket_count = self.bracket_count
        if not expression_only:
            self.begin('indent')
        self.peeked = None
        self.peeking = False

    def read(self):
        result = self.peek()
        self.peeked = None
        return result

    def peek(self):
        if self.peeked is None:
            self.peeking = True
            try:
                self.peeked = plex.Scanner.read(self)
                # Skip Plex's generated "EOF" token (where the type is None)
                # since we have our own explicit EOF token.
                if self.peeked[0] is None:
                    self.peeked = plex.Scanner.read(self)
            except UnrecognizedInput, ex:
                raise UnexpectedTokenError(
                    "Invalid token",
                    " at ", pos_link(self.position())
                )
            finally:
                self.peeking = False
        return self.peeked

    def position(self):
        if not self.peeking:
            self.peek()
        return plex.Scanner.position(self)

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
                "Expected ", symbol,
                " but got ", self.token_display_name(self.peek()),
                " at ", pos_link(self.position()),
            )
        return self.read()

    def require_keyword(self, name):
        if not self.next_is_keyword(name):
            raise UnexpectedTokenError(
                "Expected ", name,
                " but got ", self.token_display_name(self.peek()),
                " at ", pos_link(self.position()),
            )
        return self.read()

    def require_indent(self):
        if not self.next_is_indent():
            raise UnexpectedTokenError(
                "Expected indent but got ",
                self.token_display_name(self.peek()),
                " at ", pos_link(self.position()),
            )
        return self.read()

    def require_outdent(self):
        if not self.next_is_outdent():
            raise UnexpectedTokenError(
                "Expected outdent but got ",
                self.token_display_name(self.peek()),
                " at ", pos_link(self.position()),
            )
        return self.read()

    def require_newline(self):
        if not self.next_is_newline():
            raise UnexpectedTokenError(
                "Expected newline but got %r" % (
                    self.token_display_name(self.peek())
                ),
                " at ", pos_link(self.position()),
            )
        return self.read()

    def require_eof(self):
        if not self.next_is_eof():
            raise UnexpectedTokenError(
                "Expected end of file but got %r" % (
                    self.token_display_name(self.peek())
                ),
                " at ", pos_link(self.position()),
            )
        return self.read()

    def skip_statement(self):
        """
        Attempt to skip the current statement.

        This is used to implement error recovery in the parser. Will
        suck tokens out of the stream until a NEWLINE is encountered,
        and then eat the NEWLINE and return, leaving the scanner in
        a state ready to read the start of the next line.

        If you skip lines then the returned token stream probably
        won't actually make sense, so this should only be used in conjunction
        with logging an error during parse so that we won't actually try to
        execute the program once parsing completes.

        The tokenizer of course has a very limited sense of what "statement"
        means, so this function won't always do something sensible on
        very malformed input.
        """
        # This depends on the fact that the scanner emits a virtual
        # newline just before the EOF, regardless of whether a newline
        # is actually present.
        while self.read()[0] != "NEWLINE":
            pass

        # If the following line introduces an indented block then we're
        # still in the middle of a compound statement, so subsequent parsing
        # would undoubtedly fail on the unexpected indent. To avoid this,
        # we skip the entire block and resume scanning after it.
        # This is not especially efficient, but we don't care because this
        # only occurs in the event of a malformed program.
        if self.next_is_indent():
            indents = 1
            self.read()
            while True:
                t = self.read()
                if t[0] == "INDENT":
                    indents = indents + 1
                elif t[0] == "OUTDENT":
                    indents = indents - 1
                    if indents == 0:
                        break

        # As a further hack, detect if the following "statement" looks like
        # an elif or else block, in which case skip those too or else we'll
        # fail with a confusing error message trying to parse the sub-clause
        # as a statement in its own right.
        if self.next_is_keyword("elif") or self.next_is_keyword("else"):
            # Probably shouldn't do this recursively but it'll only be
            # a problem for if statements with many, many elif clauses.
            self.skip_statement()

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


class IndentationError(CompilerError):
    def __init__(self, position):
        self.position = position
        CompilerError.__init__(
            self, "Inconsistent indentation at ", pos_link(
                position,
                "%s line %i" % (position[0], position[1]),
            )
        )


class UnexpectedTokenError(CompilerError):
    pass
