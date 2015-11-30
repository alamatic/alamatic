package ast

import (
	"github.com/alamatic/alamatic/diag"
	"github.com/alamatic/alamatic/tokenizer"
)

type parser struct {
	peeker *tokenizer.TokenPeeker
}

func ParseModule(c <-chan tokenizer.Token) *Module {
	peeker := tokenizer.NewPeeker(c)
	parser := &parser{peeker}
	sourceRange, block, doc := parser.ParseTopLevel()
	return &Module{
		Block:       block,
		SourceRange: sourceRange,
		Doc:         doc,
	}
}

func (p *parser) ParseTopLevel() (*diag.SourceRange, *StatementBlock, DocString) {
	sourceRange := &diag.SourceRange{
		diag.SourceLocation{
			"placeholder.ala", 1, 1,
		},
		diag.SourceLocation{
			"placeholder.ala", 1, 1,
		},
	}
	return sourceRange, &StatementBlock{
		Statements:  []Statement{},
		SourceRange: sourceRange,
	}, ""
}
