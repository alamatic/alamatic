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
	block, doc := parser.ParseTopLevel()
	return &Module{
		Block:       block,
		SourceRange: block.SourceRange,
		Doc:         doc,
	}
}

func (p *parser) ParseTopLevel() (*StatementBlock, DocString) {
	peeker := p.peeker

	fullRange := peeker.RangeBuilder()

	doc := p.ParseDocComments()

	// To avoid ambiguity, an empty line is always required after a module
	// docstring, so it can be distinguished from a declaration docstring
	// for the file's first declaration.
	var ambiguousModuleDocstringError *diag.Diagnostic
	if doc != "" {
		next := peeker.Peek()
		if next.Kind != tokenizer.NewLine && next.Kind != tokenizer.EOF {
			type ambiguousModuleDocstringDetails struct {
				diag.Message `Empty line required after module docstring`
			}

			ambiguousModuleDocstringError = &diag.Diagnostic{
				Level:       diag.Error,
				Details:     &ambiguousModuleDocstringDetails{},
				SourceRange: next.SourceRange(),
			}
		}
	}

	stmts := p.ParseStatements(func(next *tokenizer.Token) bool {
		// Stop at the end of the file
		return next.Kind == tokenizer.EOF
	})

	if ambiguousModuleDocstringError != nil {
		// Treat the missing blank line as a diagnostic statement at the
		// beginning of the statement list.
		origStmts := stmts
		stmts = make([]Statement, 0, len(origStmts)+1)
		stmts = append(stmts, &DiagnosticStmt{
			Diagnostics: []*diag.Diagnostic{
				ambiguousModuleDocstringError,
			},
		})
		stmts = append(stmts, origStmts...)
	}

	sourceRange := fullRange()

	return &StatementBlock{
		Statements:  stmts,
		SourceRange: sourceRange,
	}, doc
}

func (p *parser) ParseDocComments() DocString {
	return DocString("")
}

func (p *parser) ParseStatements(stop func(*tokenizer.Token) bool) []Statement {
	return []Statement{}
}
