package tokenizer

import (
	"testing"
)

func makeTokenChan(tokens []Token) <-chan Token {
	c := make(chan Token)

	go func() {
		for _, t := range tokens {
			c <- t
		}
	}()

	return c
}

func makeTokenPeeker(tokens []Token) *TokenPeeker {
	return NewPeeker(makeTokenChan(tokens))
}

func TestPeeking(t *testing.T) {
	peeker := makeTokenPeeker([]Token{
		{
			OpenBracket,
			[]byte{'['},
			sloc(1, 1),
		},
		{
			CloseBracket,
			[]byte{']'},
			sloc(1, 2),
		},
	})

	if peeked := peeker.Peek(); peeked.Kind != OpenBracket {
		t.Errorf("Wrong first peeked token type %s; want %s", peeked.Kind, OpenBracket)
	}
	if peeked := peeker.Peek(); peeked.Kind != OpenBracket {
		t.Errorf("Wrong second peeked token type %s; want %s", peeked.Kind, OpenBracket)
	}
	if read := peeker.Read(); read.Kind != OpenBracket {
		t.Errorf("Wrong read token type %s; want %s", read.Kind, OpenBracket)
	}
	if peeked := peeker.Peek(); peeked.Kind != CloseBracket {
		t.Errorf("Wrong third peeked token type %s; want %s", peeked.Kind, CloseBracket)
	}
	if read := peeker.Read(); read.Kind != CloseBracket {
		t.Errorf("Wrong read token type %s; want %s", read.Kind, CloseBracket)
	}
}

func TestRangeBuilder(t *testing.T) {
	peeker := makeTokenPeeker([]Token{
		{
			OpenBracket,
			[]byte{'('},
			sloc(1, 1),
		},
		{
			DecNumLit,
			[]byte{'1'},
			sloc(1, 2),
		},
		{
			Punct,
			[]byte{'+'},
			sloc(1, 3),
		},
		{
			DecNumLit,
			[]byte{'1'},
			sloc(1, 4),
		},
		{
			CloseBracket,
			[]byte{')'},
			sloc(1, 5),
		},
	})

	makeOuterRange := peeker.RangeBuilder()
	if read, want := peeker.Read(), OpenBracket; read.Kind != want {
		t.Errorf("Wrong read token type %s; want %s", read.Kind, want)
	}
	makeInnerRange := peeker.RangeBuilder()
	if read, want := peeker.Read(), DecNumLit; read.Kind != want {
		t.Errorf("Wrong read token type %s; want %s", read.Kind, want)
	}
	if read, want := peeker.Read(), Punct; read.Kind != want {
		t.Errorf("Wrong read token type %s; want %s", read.Kind, want)
	}
	if read, want := peeker.Read(), DecNumLit; read.Kind != want {
		t.Errorf("Wrong read token type %s; want %s", read.Kind, want)
	}
	innerRange := makeInnerRange()
	if read, want := peeker.Read(), CloseBracket; read.Kind != want {
		t.Errorf("Wrong read token type %s; want %s", read.Kind, want)
	}
	outerRange := makeOuterRange()

	if got, want := outerRange.Start.Column, 1; got != want {
		t.Errorf("Wrong outerRange start column %s; want %s", got, want)
	}
	if got, want := outerRange.End.Column, 5; got != want {
		t.Errorf("Wrong outerRange end column %s; want %s", got, want)
	}
	if got, want := innerRange.Start.Column, 2; got != want {
		t.Errorf("Wrong innerRange start column %s; want %s", got, want)
	}
	if got, want := innerRange.End.Column, 4; got != want {
		t.Errorf("Wrong innerRange end column %s; want %s", got, want)
	}
}
