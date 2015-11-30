package ast

import (
	"github.com/alamatic/alamatic/diag"
)

type Error struct {
	baseASTNode
	Error diag.Diagnostic
}
