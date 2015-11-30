package tokenizer

import (
	"github.com/alamatic/alamatic/diag"
)

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

func (p *TokenPeeker) Peek() *Token {
	if p.peeked == nil {
		tok, _ := <-p.c
		p.peeked = &tok
	}
	return p.peeked
}

func (p *TokenPeeker) Read() *Token {
	tok := p.Peek()
	p.lastRead = tok
	p.peeked = nil
	return tok
}

type RangeBuilder func() *diag.SourceRange

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
