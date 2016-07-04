package ast

import (
	"github.com/alamatic/alamatic/diag"
	"github.com/alamatic/alamatic/ir"
)

type PassStmt struct {
	baseASTNode

	SourceRange *diag.SourceRange
}

func (s *PassStmt) BuildIR(*Scope, *ir.Builder) {
	// Nothing to do for the "pass" statement, since it's
	// just a syntax artifact to make indentation line up while
	// doing absolutely nothing.
}
