package tokenizer

type TokenPeeker struct {
	c      <-chan Token
	peeked *Token
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
	p.peeked = nil
	return tok
}