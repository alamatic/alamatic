package ast

import (
	"github.com/alamatic/alamatic/diag"
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
