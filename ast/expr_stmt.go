package ast

import (
	"github.com/alamatic/alamatic/ir"
)

type ExprStmt struct {
	Expression Expression
}

func (s *ExprStmt) Params() []interface{} {
	return []interface{}{}
}

func (s *ExprStmt) ChildNodes() []ASTNode {
	return []ASTNode{s.Expression}
}

func (s *ExprStmt) BuildIR(scope *Scope, builder *ir.Builder) {
	s.Expression.BuildIR(scope, builder)
}
