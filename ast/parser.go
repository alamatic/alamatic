package ast

import (
	"fmt"
	"math/big"

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

func ParseExpr(c <-chan tokenizer.Token) Expression {
	peeker := tokenizer.NewPeeker(c)
	parser := &parser{peeker}
	expr := parser.ParseExpression(false)
	return expr
}

func ParseExprStmt(c <-chan tokenizer.Token) *ExprStmt {
	peeker := tokenizer.NewPeeker(c)
	parser := &parser{peeker}
	expr := parser.ParseExpression(true)
	return &ExprStmt{
		Expression: expr,
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
		token := peeker.Read()
		tokenRange := token.SourceRange()

		// FIXME: Emit a diagnostic statement and then seek on to the next
		// statement and try to keep parsing.
		// For now, we just panic.
		panic("invalid indented block at " + token.String())

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
	if next.String() != ":" {
		return parseErr()
	}
	peeker.Read()

	next = peeker.Peek()
	if next.Kind != tokenizer.NewLine {
		return parseErr()
	}
	peeker.Read()

	next = peeker.Peek()
	if next.Kind != tokenizer.Indent {
		return parseErr()
	}
	peeker.Read()

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
	var parsers []expressionParser
	if allowAssign {
		parsers = expressionParsers
	} else {
		// Skip the first element, which is the assignment operators
		parsers = expressionParsers[1:]
	}

	return parsers[0].Parse(p, parsers[1:])
}

func (p *parser) requireStatementEOL(s Statement) Statement {
	next := p.peeker.Peek()
	if next.Kind != tokenizer.NewLine {
		// TODO: Try to seek to the beginning of the next statement
		// so we can attempt to parse the rest of the file.
		p.peeker.Read()
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

var expressionParsers = []expressionParser{
	&binaryOpParser{
		Operators: []BinaryOpType{
			AssignOp,
			AddAssignOp,
			SubtractAssignOp,
			MultiplyAssignOp,
			DivideAssignOp,
			UnionAssignOp,
			IntersectionAssignOp,
		},
		ChainAllowed: false,
	},
	&binaryOpParser{
		Operators: []BinaryOpType{
			OrOp,
		},
		ChainAllowed: true,
	},
	&binaryOpParser{
		Operators: []BinaryOpType{
			AndOp,
		},
		ChainAllowed: true,
	},
	&binaryOpParser{
		Operators: []BinaryOpType{
			IsOp, // implies IsNotOp due to a special case in binaryOpParser
			LessThanOp,
			LessThanEqualOp,
			GreaterThanOp,
			GreaterThanEqualOp,
			NotEqualOp,
			EqualOp,
		},
		ChainAllowed: true,
	},
	&binaryOpParser{
		Operators: []BinaryOpType{
			UnionOp,
		},
		ChainAllowed: true,
	},
	&binaryOpParser{
		Operators: []BinaryOpType{
			IntersectionOp,
		},
		ChainAllowed: true,
	},
	&binaryOpParser{
		Operators: []BinaryOpType{
			ShiftLeftOp,
			ShiftRightOp,
		},
		ChainAllowed: true,
	},
	&binaryOpParser{
		Operators: []BinaryOpType{
			AddOp,
			SubtractOp,
		},
		ChainAllowed: true,
	},
	&binaryOpParser{
		Operators: []BinaryOpType{
			MultiplyOp,
			DivideOp,
			ModuloOp,
		},
		ChainAllowed: true,
	},

	// factorExprParser expects to be the last item in this list
	&factorExprParser{},
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
	peeker := p.peeker
	fullRange := peeker.RangeBuilder()
	makeOperatorRange := peeker.RangeBuilder()

	// Must always have at least one remaining parser because
	// a unary operator can't be a terminal expression.
	nextParser := remain[0]

	next := peeker.Peek()
	opType := UnaryOpType(next.String())
	match := false
	for _, allowedOpType := range pp.Operators {
		if opType == allowedOpType {
			match = true
			break
		}
	}

	if !match {
		return nextParser.Parse(p, remain[1:])
	}

	peeker.Read()
	operatorRange := makeOperatorRange()

	// We call ourselves recursively here so we can chain,
	// like "not not a". Even though this isn't super useful,
	// it ought to work for consistency's sake.
	operand := pp.Parse(p, remain)

	return &UnaryOpExpr{
		Operand:             operand,
		Operator:            opType,
		SourceRange:         fullRange(),
		OperatorSourceRange: operatorRange,
	}
}

type factorExprParser struct {
}

func (pp *factorExprParser) Parse(p *parser, remain []expressionParser) Expression {
	peeker := p.peeker
	fullRange := peeker.RangeBuilder()

	if len(remain) != 0 {
		// Should never happen, because factor expressions must be
		// last in the expression parser list.
		panic("factorExprParser must be terminal")
	}

	next := peeker.Peek()

	var expr Expression

	switch {
	case next.String() == "(":
		peeker.Read()
		expr = p.ParseExpression(false)
		close := peeker.Read()
		if close.String() != ")" {
			// FIXME: Should generate a diagnostic node instead
			panic("invalid expression close")
		}
	case next.Kind == tokenizer.DecNumLit || next.Kind == tokenizer.HexNumLit || next.Kind == tokenizer.BinNumLit || next.Kind == tokenizer.OctNumLit:
		token := peeker.Read()
		// FIXME: This can't actually parse octal literals
		val, _, err := big.ParseFloat(token.String(), 0, 0, big.ToZero)

		// FIXME: We should handle this by returning a diagnostic node,
		// since the tokenizer doesn't actually validate that the numbers
		// are valid. (We want to handle it here in the parser because we
		// can generate a better error message in here.)
		if err != nil {
			panic("invalid number token")
		}

		expr = &LiteralNumberExpr{
			Value:       val,
			SourceRange: fullRange(),
		}
	case next.Kind == tokenizer.StringLit:
		panic("string literal parsing not yet implemented")
	case next.String() == "true":
		peeker.Read()
		expr = &LiteralBoolExpr{
			Value:       true,
			SourceRange: fullRange(),
		}
	case next.String() == "false":
		peeker.Read()
		expr = &LiteralBoolExpr{
			Value:       false,
			SourceRange: fullRange(),
		}
	case next.String() == "null":
		peeker.Read()
		expr = &LiteralNullExpr{
			SourceRange: fullRange(),
		}
	case next.Kind == tokenizer.Ident:
		identToken := peeker.Read()
		expr = &SymbolExpr{
			Name:        identToken.String(),
			SourceRange: fullRange(),
		}
	default:
		// FIXME: Should generate a diagnostic node instead
		panic(fmt.Sprintf("invalid factor %#v %#v", next.String(), next.SourceRange()))
	}

	// Calls, subscripts and attribute access can be chained to
	// expressions indefinitely.
	/*for {
			next := peeker.Peek()

			switch next.String() {
			case "(":
				peeker.Read()
				args := p.ParseArguments(")")
			}
	        // etc
		}*/

	return expr
}
