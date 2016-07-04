package ast

import (
	"github.com/alamatic/alamatic/diag"
	"github.com/alamatic/alamatic/ir"
)

type BreakStmt struct {
	SourceRange *diag.SourceRange
}

func (s *BreakStmt) Params() []interface{} {
	return []interface{}{}
}

func (s *BreakStmt) ChildNodes() []ASTNode {
	return []ASTNode{}
}

func (s *BreakStmt) BuildIR(scope *Scope, builder *ir.Builder) {
	builder.Jump(scope.BreakBlock)
}
