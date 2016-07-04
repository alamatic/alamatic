package ast

import (
	"github.com/alamatic/alamatic/diag"
	"github.com/alamatic/alamatic/ir"
)

type ContinueStmt struct {
	SourceRange *diag.SourceRange
}

func (s *ContinueStmt) Params() []interface{} {
	return []interface{}{}
}

func (s *ContinueStmt) ChildNodes() []ASTNode {
	return []ASTNode{}
}

func (s *ContinueStmt) BuildIR(scope *Scope, builder *ir.Builder) {
	builder.Jump(scope.ContinueBlock)
}
