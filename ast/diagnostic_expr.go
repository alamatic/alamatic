package ast

import (
	"github.com/alamatic/alamatic/diag"
	"github.com/alamatic/alamatic/ir"
)

type DiagnosticExpr struct {
	baseASTNode
	Diagnostics []*diag.Diagnostic
}

func (s *DiagnosticExpr) BuildIR(scope *Scope, b *ir.Builder) ir.Value {
	return b.Diagnostics(s.Diagnostics)
}
