package ast

import (
	"github.com/alamatic/alamatic/diag"
)

type DiagnosticStmt struct {
	baseASTNode
	Diagnostics []*diag.Diagnostic
}
