package ast

import (
	"github.com/alamatic/alamatic/ir"
)

type Statement interface {
	ASTNode

	BuildIR(*Scope, *ir.Builder)
}
