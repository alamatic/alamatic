package ast

import (
	"github.com/alamatic/alamatic/ir"
)

type Expression interface {
	ASTNode

	BuildIR(*Scope, *ir.Builder) ir.Value
}
