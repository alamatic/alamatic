package tokenizer

import (
	"github.com/alamatic/alamatic/diag"
)

type Token struct {
	Kind  TokenKind
	Bytes []byte
	diag.SourceLocation
}

func (t *Token) SourceRange() *diag.SourceRange {
	return &diag.SourceRange{
		t.SourceLocation,
		diag.SourceLocation{
			t.Filename,
			t.Line,
			t.Column + len(t.Bytes),
		},
	}
}
