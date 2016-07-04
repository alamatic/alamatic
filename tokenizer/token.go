package tokenizer

import (
	"github.com/alamatic/alamatic/diag"
)

// Token represents a classified span of bytes from an Alamatic source file.
//
// In a raw token stream produced by the scanner, each byte in the source file
// belongs to exactly one token, and the byte slices are all sub-slices of
// the original source buffer.
//
// In a token stream raised by RaiseRawTokens (returned by Tokenize), some
// bytes in the source buffer are eliminated as insignificant. Further, some
// synthetic tokens are created to represent indented blocks, and the bytes
// for these tokens do not appear in the source buffer at all.
type Token struct {
	Kind  TokenKind
	Bytes []byte
	diag.SourceLocation
	str string
}

// SourceRange returns the range of characters in the source file that are
// classified as belonging to the token.
//
// SourceRange may return strange results when called on synthetic indent
// tokens, though the tokenizer does make some effort to ensure that these
// will act consistently in most cases.
//
// Column numbering starts at 1, but newline characters (which have no explicit
// position in the 2D line/column grid) are considered to be at position zero
// of the new line they create, placing them figuratively "in the margin".
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

// String returns the content of the token as a string.
//
// This differs from string(token.Bytes) only in that it caches the resulting
// string to avoid creating garbage from repeated conversions.
func (t *Token) String() string {
	if len(t.str) != len(t.Bytes) {
		t.str = string(t.Bytes)
	}
	return t.str
}
