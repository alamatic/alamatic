package ast

import (
	"github.com/alamatic/alamatic/diag"
	"github.com/alamatic/alamatic/ir"
)

type StatementBlock struct {
	baseASTNode
	Statements  []Statement
	SourceRange *diag.SourceRange
}

func (n *StatementBlock) ChildNodes() []ASTNode {
	ret := make([]ASTNode, len(n.Statements))
	for i, s := range n.Statements {
		ret[i] = ASTNode(s)
	}
	return ret
}

func (n *StatementBlock) BuildIR(scope *Scope, builder *ir.Builder) {
	for _, stmt := range n.Statements {
		if builder.Block.Terminator != nil {
			// If our block has been terminated then we've found
			// some unreachable code.
			// TODO: Flag this as a warning?
			break
		}
		stmt.BuildIR(scope, builder)
	}
}
