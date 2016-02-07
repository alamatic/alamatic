package tokenizer

import (
	"github.com/alamatic/alamatic/diag"
)

// TokenPeeker is a wrapper around a Token channel that provides the one token
// of lookahead necessary for parsing Alamatic source code.
type TokenPeeker struct {
	c        <-chan Token
	peeked   *Token
	lastRead *Token
}

func NewPeeker(c <-chan Token) *TokenPeeker {
	return &TokenPeeker{
		c: c,
	}
}

// Peek returns the next token in the token stream, without seeking to the next
// token in the stream.
//
// Peek can be called many times and will retrieve the same token each time,
// until Read is called.
func (p *TokenPeeker) Peek() *Token {
	if p.peeked == nil {
		tok, _ := <-p.c
		p.peeked = &tok
	}
	return p.peeked
}

// Read returns the next token in the token stream and then seeks to the next
// token in the stream.
//
// Successive calls to Read will return successive tokens from the stream,
// until the special empty EOF token is reached.
func (p *TokenPeeker) Read() *Token {
	tok := p.Peek()
	p.lastRead = tok
	p.peeked = nil
	return tok
}

// RangeBuilder is the type of function returned by the TokenPeeker
// RangeBuilder method.
type RangeBuilder func() *diag.SourceRange

// RangeBuilder assists in creating SourceRange objects spanning sequences
// of tokens.
//
// A call to RangeBuilder memorizes the current token's starting location
// and returns a function. The caller may then read more tokens from the
// stream before eventually calling that returned function, which will then
// return a SourceRange from the memorized start point to the end of the
// most recently-read token.
//
// Note that the start point references the next token that hasn't yet been
// read, while the end point references the latest token that was already
// read. The intended usage is for a parsing function to call RangeBuilder
// before it reads or peeks any tokens, and then to call the returned function
// once all of the tokens used by that function have been read.
func (p *TokenPeeker) RangeBuilder() RangeBuilder {
	// Start location is the location of the token we're about to read.
	start := &(p.Peek().SourceLocation)
	return RangeBuilder(func() *diag.SourceRange {
		// End location is the location of the token we most recently read,
		// or the same as the start location if we've not read anything yet.
		end := start
		if p.lastRead != nil {
			end = &p.lastRead.SourceLocation
		}
		return &diag.SourceRange{
			Start: *start,
			End:   *end,
		}
	})
}
