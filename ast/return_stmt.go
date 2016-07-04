package ast

import (
	"github.com/alamatic/alamatic/diag"
	"github.com/alamatic/alamatic/ir"
)

type ReturnStmt struct {
	Expression  Expression
	SourceRange *diag.SourceRange
}

func (s *ReturnStmt) Params() []interface{} {
	return []interface{}{}
}

func (s *ReturnStmt) ChildNodes() []ASTNode {
	return []ASTNode{s.Expression}
}

func (s *ReturnStmt) BuildIR(scope *Scope, builder *ir.Builder) {
	retVal := s.Expression.BuildIR(scope, builder)
	builder.Return(retVal)
}
