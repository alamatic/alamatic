package tokenizer

type TokenKind int

const (
	Invalid TokenKind = 0
	NewLine TokenKind = iota
	Space   TokenKind = iota
	Comment TokenKind = iota

	OpenBracket TokenKind = iota
	CloseBracket TokenKind = iota
	Punct TokenKind = iota
	Ident TokenKind = iota

	DecNumLit TokenKind = iota
	HexNumLit TokenKind = iota
	BinNumLit TokenKind = iota
	OctNumLit TokenKind = iota
	StringLit TokenKind = iota
)
