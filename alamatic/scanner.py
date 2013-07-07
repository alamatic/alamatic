
import plex
from plex import (
    Rep,
    Rep1,
    Range,
    Any,
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

    lexicon = plex.Lexicon([
        (Rep1(Range("09")), 'INTEGER'),
        (Any("({["), handle_open_bracket),
        (Any(")}]"), handle_close_bracket),
        ((Str("\n") | Eof), handle_newline),
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

    # plex generates the "None" token representing EOF *before* it runs
    # the eof method (despite assertions in the manual to the contrary)
    # so we just have our own EOF token and ignore the one plex provides.
    def read(self):
        result = plex.Scanner.read(self)
        if result[0] is None:
            result = plex.Scanner.read(self)
        return result


class IndentationError(Exception):
    def __init__(self, position):
        Exception.__init__(
            self, "Inconsistent indentation at %s line %i" % (
                position[0], position[1],
            )
        )
        self.position = position
