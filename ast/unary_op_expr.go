package ast

import (
	"github.com/alamatic/alamatic/diag"
	"github.com/alamatic/alamatic/ir"
)

type UnaryOpType string

const NotOp UnaryOpType = "not"
const NegateOp UnaryOpType = "-"
const ComplementOp UnaryOpType = "~"

type UnaryOpExpr struct {
	baseASTNode

	Operand  Expression
	Operator UnaryOpType

	SourceRange         *diag.SourceRange
	OperatorSourceRange *diag.SourceRange
}

func (s *UnaryOpExpr) BuildIR(scope *Scope, b *ir.Builder) ir.Value {
	// TODO: Implement
	return nil
}
