package ast

import (
	"github.com/alamatic/alamatic/diag"
	"github.com/alamatic/alamatic/ir"
)

type SymbolExpr struct {
	Name        string
	SourceRange *diag.SourceRange
}

func (s *SymbolExpr) Params() []interface{} {
	return []interface{}{s.Name}
}

func (s *SymbolExpr) ChildNodes() []ASTNode {
	return []ASTNode{}
}

func (s *SymbolExpr) BuildIR(scope *Scope, builder *ir.Builder) ir.Value {
	panic("BuildIR not yet implemented for SymbolExpr")
}
