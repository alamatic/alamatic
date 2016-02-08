package ast

import (
	"github.com/alamatic/alamatic/diag"
)

type PassStmt struct {
	baseASTNode

	SourceRange *diag.SourceRange
}
