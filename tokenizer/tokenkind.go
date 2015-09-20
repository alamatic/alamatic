package tokenizer

type TokenKind int

const (
	Invalid    TokenKind = 0
	EOF        TokenKind = iota
	NewLine    TokenKind = iota
	Space      TokenKind = iota
	Comment    TokenKind = iota
	Indent     TokenKind = iota
	Outdent    TokenKind = iota
	BadOutdent TokenKind = iota

	OpenBracket     TokenKind = iota
	CloseBracket    TokenKind = iota
	MismatchBracket TokenKind = iota
	Punct           TokenKind = iota
	Ident           TokenKind = iota

	DecNumLit TokenKind = iota
	HexNumLit TokenKind = iota
	BinNumLit TokenKind = iota
	OctNumLit TokenKind = iota
	StringLit TokenKind = iota
)
