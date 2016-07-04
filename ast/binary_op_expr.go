package ast

import (
	"github.com/alamatic/alamatic/diag"
	"github.com/alamatic/alamatic/ir"
)

type BinaryOpType string

const AssignOp BinaryOpType = "="
const AddAssignOp BinaryOpType = "+="
const SubtractAssignOp BinaryOpType = "-="
const MultiplyAssignOp BinaryOpType = "*="
const DivideAssignOp BinaryOpType = "/="
const UnionAssignOp BinaryOpType = "|="
const IntersectionAssignOp BinaryOpType = "&="
const OrOp BinaryOpType = "or"
const AndOp BinaryOpType = "and"
const IsOp BinaryOpType = "is"
const IsNotOp BinaryOpType = "is not"
const LessThanOp BinaryOpType = "<"
const LessThanEqualOp BinaryOpType = "<="
const GreaterThanOp BinaryOpType = ">"
const GreaterThanEqualOp BinaryOpType = ">="
const NotEqualOp BinaryOpType = "!="
const EqualOp BinaryOpType = "=="
const UnionOp BinaryOpType = "|"
const IntersectionOp BinaryOpType = "&"
const ShiftLeftOp BinaryOpType = "<<"
const ShiftRightOp BinaryOpType = ">>"
const AddOp BinaryOpType = "+"
const SubtractOp BinaryOpType = "-"
const MultiplyOp BinaryOpType = "*"
const DivideOp BinaryOpType = "/"
const ModuloOp BinaryOpType = "%"

type BinaryOpExpr struct {
	baseASTNode

	LHS      Expression
	RHS      Expression
	Operator BinaryOpType

	SourceRange         *diag.SourceRange
	OperatorSourceRange *diag.SourceRange
}

func (s *BinaryOpExpr) BuildIR(scope *Scope, b *ir.Builder) ir.Value {
	// TODO: Implement
	return nil
}
