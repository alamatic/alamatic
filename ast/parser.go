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

func (p *parser) ParseIndentedBlock() *StatementBlock {
	peeker := p.peeker
	fullRange := peeker.RangeBuilder()

	parseErr := func() *StatementBlock {
		tokenRange := peeker.Peek().SourceRange()
		return &StatementBlock{
			Statements: []Statement{
				&DiagnosticStmt{
					Diagnostics: []*diag.Diagnostic{
						{
							Level:       diag.Error,
							Details:     &IndentedBlockExpected{},
							SourceRange: tokenRange,
						},
					},
				},
			},
			SourceRange: tokenRange,
		}
	}

	next := peeker.Peek()
	if next.Kind != tokenizer.Punct || len(next.Bytes) != 1 || next.Bytes[0] != ':' {
		return parseErr()
	}

	next = peeker.Peek()
	if next.Kind != tokenizer.NewLine {
		return parseErr()
	}

	next = peeker.Peek()
	if next.Kind != tokenizer.Indent {
		return parseErr()
	}

	stmts := p.ParseStatements(func(next *tokenizer.Token) bool {
		return next.Kind == tokenizer.Outdent
	})

	// Gobble the remaining outdent
	peeker.Read()

	return &StatementBlock{
		Statements:  stmts,
		SourceRange: fullRange(),
	}
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
		case "break":
			peeker.Read()
			stmt := &BreakStmt{
				SourceRange: fullRange(),
			}
			return p.requireStatementEOL(stmt)
		case "continue":
			peeker.Read()
			stmt := &ContinueStmt{
				SourceRange: fullRange(),
			}
			return p.requireStatementEOL(stmt)
		case "return":
			return p.ParseReturnStmt()
		case "if":
			return p.ParseIfStmt()
		case "while":
			return p.ParseWhileStmt()
		case "for":
			return p.ParseForStmt()
		case "var", "const":
			return p.ParseDataDeclStmt()
		case "func", "proc":
			return p.ParseFuncDecl()
		}
	}

	expr := p.ParseExpression(true)
	stmt := &ExprStmt{
		Expression: expr,
	}
	// FIXME: Generate a diagnostic node if an expression statement
	// has no direct side-effects... that is, if it's not a call
	// or an assignment.
	return p.requireStatementEOL(stmt)
}

func (p *parser) ParseReturnStmt() Statement {
	peeker := p.peeker

	fullRange := peeker.RangeBuilder()

	// Assumed to be called only when the next token is "return"
	peeker.Read()
	var expr Expression
	next := peeker.Peek()
	if next.Kind != tokenizer.NewLine {
		expr = p.ParseExpression(false)
	}
	stmt := &ReturnStmt{
		Expression:  expr,
		SourceRange: fullRange(),
	}
	return p.requireStatementEOL(stmt)
}

func (p *parser) ParseIfStmt() Statement {
	peeker := p.peeker

	fullRange := peeker.RangeBuilder()

	// Assumed to be called only when the next token is "if"
	peeker.Read()

	clauses := make([]*IfClause, 0, 1)

	ifExpr := p.ParseExpression(false)
	ifBlock := p.ParseIndentedBlock()

	clauses = append(clauses, &IfClause{
		CondExpr: ifExpr,
		Block:    ifBlock,
	})

	for {
		next := peeker.Peek()
		if next.Kind != tokenizer.Ident || string(next.Bytes) != "elif" {
			break
		}

		peeker.Read()
		elseIfExpr := p.ParseExpression(false)
		elseIfBlock := p.ParseIndentedBlock()

		clauses = append(clauses, &IfClause{
			CondExpr: elseIfExpr,
			Block:    elseIfBlock,
		})
	}

	if next := peeker.Peek(); next.Kind == tokenizer.Ident && string(next.Bytes) == "else" {
		peeker.Read()
		elseBlock := p.ParseIndentedBlock()

		clauses = append(clauses, &IfClause{
			Block: elseBlock,
		})
	}

	stmt := &IfStmt{
		Clauses:     clauses,
		SourceRange: fullRange(),
	}
	return stmt
}

func (p *parser) ParseWhileStmt() Statement {
	panic("while not implemented")
}

func (p *parser) ParseForStmt() Statement {
	panic("for not implemented")
}

func (p *parser) ParseDataDeclStmt() Statement {
	panic("data decl not implemented")
}

func (p *parser) ParseFuncDecl() Statement {
	panic("func decl not implemented")
}

func (p *parser) ParseExpression(allowAssign bool) Expression {
	if allowAssign {
		return p.ParseExprAssign()
	} else {
		return p.ParseExprLogicalOr()
	}
}

func (p *parser) ParseExprAssign() Expression {
	return &DiagnosticExpr{
		Diagnostics: []*diag.Diagnostic{
			{},
		},
	}
}

func (p *parser) ParseExprLogicalOr() Expression {
	return &DiagnosticExpr{
		Diagnostics: []*diag.Diagnostic{
			{},
		},
	}
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

type expressionParser interface {
	Parse(*parser, []expressionParser) Expression
}

type binaryOpParser struct {
	Operators    []BinaryOpType
	ChainAllowed bool
}

func (pp *binaryOpParser) Parse(p *parser, remain []expressionParser) Expression {
	peeker := p.peeker
	fullRange := peeker.RangeBuilder()

	// Must always have at least one remaining parser because
	// a binary operator can't be a terminal expression.
	nextParser := remain[0]

	lhs := nextParser.Parse(p, remain[1:])

	next := peeker.Peek()
	opType := BinaryOpType(next.String())
	match := false
	for _, allowedOpType := range pp.Operators {
		if opType == allowedOpType {
			match = true
			break
		}
	}

	if !match {
		return lhs
	}

	makeOperatorRange := peeker.RangeBuilder()

	// Eat the operator token, since we've already dealt with it.
	peeker.Read()

	if opType == IsOp {
		// As a special case for the weird two-token "is not" operator,
		// we'll try to eat a "not" right after our "is".
		// NOTE: This assumes that "is not" is always valid in a
		// parser where "is" is valid, which is true for now.
		next := peeker.Peek()
		if next.String() == "not" {
			opType = IsNotOp
			peeker.Read()
		}
	}

	operatorRange := makeOperatorRange()

	var rhs Expression
	if pp.ChainAllowed {
		// Recursively call back into this same parser, so that the
		// same operator can be chained multiple times.
		rhs = pp.Parse(p, remain)
	} else {
		rhs = nextParser.Parse(p, remain[1:])
	}

	return &BinaryOpExpr{
		LHS:      lhs,
		RHS:      rhs,
		Operator: opType,

		SourceRange:         fullRange(),
		OperatorSourceRange: operatorRange,
	}
}

type unaryOpParser struct {
	Operators []UnaryOpType
}

func (pp *unaryOpParser) Parse(p *parser, remain []expressionParser) Expression {
	panic("unary op parser not implemented")
}

type factorExprParser struct {
}

func (pp *factorExprParser) Parse(p *parser, remain []expressionParser) Expression {
	panic("factor op parser not implemented")
}
