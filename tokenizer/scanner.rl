package tokenizer

import (
    "github.com/alamatic/alamatic/diagnostics"
)

// The goal of the scanner is to apply very simple classifications to
// sequences of bytes in the input. The generated "raw" tokens cover all
// of the bytes in the input, and then the tokenizer will interpret
// the raw token stream to produce the logical token stream, where whitespace
// and comments are removed and indent/outdent tokens are inserted.
%%{
    machine scan;

    letter = [a-zA-Z];

    decimal_number = digit+ ('.' digit+)? ('E' ('+'|'-') digit+)?;
    # We tolerate invalid (out of range) digits/letters in the following
    # patterns because it's easier to generate a nice error for these
    # at a higher layer, rather than them just being classified as invalid
    # tokens.
    hex_number = "0x" [0-9a-zA-Z]+;
    binary_number = "0b" digit+;
    octal_number = "0o" digit+;

    string_escape = /\\./;
    string_literal_char = [^"\\];
    # Unterminated string literal is tolerated here and detected by
    # the consumer of the raw token stream.
    string_literal = '"' (string_literal_char|string_escape)* '"'?;

    identifier = [a-zA-Z_] [a-zA-Z0-9_]*;

    # We allow any combination of these punctuation characters at this
    # layer, constraining down to valid operators in the parser.
    # This means we'll consume invalid sequences like "++" as single
    # tokens here, rather than as a pair of consecutive tokens that
    # would produce an less-helpful error message in the parser.
    punctuation = ([=&^<>*/%~+:,!]| "|" | "." | "-")+;

    open_bracket = "["|"("|"{";
    close_bracket = "]"|")"|"}";

    comment = "#" [^\n]*;

    action inc_nl {
        line++
        lastNewline = p
    }

    main := |*
         decimal_number => { tok(DecNumLit) };
         hex_number => { tok(HexNumLit) };
         binary_number => { tok(BinNumLit) };
         octal_number => { tok(OctNumLit) };
         string_literal => { tok(StringLit) };
         open_bracket => { tok(OpenBracket) };
         close_bracket => { tok(CloseBracket) };
         punctuation => { tok(Punct) };
         identifier => { tok(Ident) };
         "\r"? ("\n" @inc_nl) => { tok(NewLine) };
         [ \t]+ => { tok(Space) };
         comment => { tok(Comment) };
         any => { tok(Invalid) };
    *|;
}%%

%% write data;

func Scan(data []byte, filename string) chan Token {
     cs, p, ts, te, act, pe, eof := 0, 0, 0, 0, 0, len(data), len(data)
     line, lastNewline := 1, -1
     ret := make(chan Token)

     // Lame hack to bypass "declared but not used" in the code generated
     // by ragel.
     nothing := func (interface{}) {}
     nothing(act)

     tok := func (kind TokenKind) {
         column := ts - lastNewline
         ret <- Token{
             kind,
             data[ts:te],
             diagnostics.SourceLocation{
                 filename, line, column,
             },
         }
     }

     %% write init;

     go func() {
     %% write exec;

         close(ret)
     }()

     return ret
}
