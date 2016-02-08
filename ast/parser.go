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
	peeker := p.peeker

	if stop == nil {
		stop = func(t *tokenizer.Token) bool {
			return t.Kind == tokenizer.Outdent
		}
	}

	stmts := make([]Statement, 0, 10)

	for !stop(peeker.Peek()) {
		if peeker.Peek().Kind == tokenizer.BadOutdent {
			badOutdent := peeker.Read()
			err := &diag.Diagnostic{
				Level:       diag.Error,
				Details:     &InconsistentIndentation{},
				SourceRange: badOutdent.SourceRange(),
			}
			stmts = append(stmts, &DiagnosticStmt{
				Diagnostics: []*diag.Diagnostic{
					err,
				},
			})
			// TODO: Try to seek past the current statement
			// so we can recover and parse the rest of the file.
			break
		}
		stmt := p.ParseStatement()
		if stmt != nil {
			stmts = append(stmts, stmt)
		}
	}

	return stmts
}

func (p *parser) ParseStatement() Statement {
	peeker := p.peeker

	fullRange := peeker.RangeBuilder()
	next := peeker.Peek()

	if next.Kind == tokenizer.NewLine {
		// Empty statement, for which we don't bother to create an AST node
		peeker.Read()
		return nil
	}

	if next.Kind == tokenizer.Ident {
		// Some legal identifiers are actually keywords when appearing
		// at the beginning of a statement.
		switch string(next.Bytes) {
		case "pass":
			peeker.Read()
			stmt := &PassStmt{
				SourceRange: fullRange(),
			}
			return p.requireStatementEOL(stmt)

			// TODO: The rest of the statement keywords
		}
	}

	// TODO: Expression statements, ...
	return nil
}

func (p *parser) requireStatementEOL(s Statement) Statement {
	next := p.peeker.Peek()
	if next.Kind != tokenizer.NewLine {
		// TODO: Try to seek to the beginning of the next statement
		// so we can attempt to parse the rest of the file.
		return &DiagnosticStmt{
			Diagnostics: []*diag.Diagnostic{
				&diag.Diagnostic{
					Level:       diag.Error,
					Details:     &NewlineExpected{},
					SourceRange: next.SourceRange(),
				},
			},
		}
	}

	return s
}
