package ast

import (
	"github.com/alamatic/alamatic/diag"
)

type ReturnStmt struct {
	Expression  Expression
	SourceRange diag.SourceRange
}
