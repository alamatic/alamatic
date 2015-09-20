package tokenizer

import (
    "github.com/alamatic/alamatic/diagnostics"
)

type Token struct {
    Kind TokenKind
    Bytes []byte
    diagnostics.SourceLocation
}

func (t *Token) SourceRange() *diagnostics.SourceRange {
     return &diagnostics.SourceRange{
         t.SourceLocation,
         diagnostics.SourceLocation{
             t.Filename,
             t.Line,
             t.Column + len(t.Bytes),
         },
     }
}
