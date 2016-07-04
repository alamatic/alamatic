package ast

import (
	"github.com/alamatic/alamatic/diag"
	"github.com/alamatic/alamatic/ir"
)

type DiagnosticStmt struct {
	baseASTNode
	Diagnostics []*diag.Diagnostic
}

func (s *DiagnosticStmt) BuildIR(scope *Scope, b *ir.Builder) {
	b.Diagnostics(s.Diagnostics)
}
