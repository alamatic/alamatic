package ast

import (
	"math/big"

	"github.com/alamatic/alamatic/diag"
	"github.com/alamatic/alamatic/ir"
)

type LiteralNumberExpr struct {
	Value       *big.Float
	SourceRange *diag.SourceRange
}

func (s *LiteralNumberExpr) Params() []interface{} {
	return []interface{}{s.Value}
}

func (s *LiteralNumberExpr) ChildNodes() []ASTNode {
	return []ASTNode{}
}

func (s *LiteralNumberExpr) BuildIR(scope *Scope, builder *ir.Builder) ir.Value {
	panic("BuildIR not yet implemented for LiteralNumberExpr")
}

type LiteralStringExpr struct {
	Value       string
	SourceRange *diag.SourceRange
}

func (s *LiteralStringExpr) Params() []interface{} {
	return []interface{}{s.Value}
}

func (s *LiteralStringExpr) ChildNodes() []ASTNode {
	return []ASTNode{}
}

func (s *LiteralStringExpr) BuildIR(scope *Scope, builder *ir.Builder) ir.Value {
	panic("BuildIR not yet implemented for LiteralStringExpr")
}

type LiteralBoolExpr struct {
	Value       bool
	SourceRange *diag.SourceRange
}

func (s *LiteralBoolExpr) Params() []interface{} {
	return []interface{}{s.Value}
}

func (s *LiteralBoolExpr) ChildNodes() []ASTNode {
	return []ASTNode{}
}

func (s *LiteralBoolExpr) BuildIR(scope *Scope, builder *ir.Builder) ir.Value {
	panic("BuildIR not yet implemented for LiteralBoolExpr")
}

type LiteralNullExpr struct {
	SourceRange *diag.SourceRange
}

func (s *LiteralNullExpr) Params() []interface{} {
	return []interface{}{}
}

func (s *LiteralNullExpr) ChildNodes() []ASTNode {
	return []ASTNode{}
}

func (s *LiteralNullExpr) BuildIR(scope *Scope, builder *ir.Builder) ir.Value {
	panic("BuildIR not yet implemented for LiteralNullExpr")
}
