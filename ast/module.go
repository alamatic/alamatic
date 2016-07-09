package ast

import (
	"github.com/alamatic/alamatic/diag"
)

type Module struct {
	baseASTNode

	Block       *StatementBlock
	SourceRange *diag.SourceRange
	Doc         DocString
}

func (n *Module) ChildNodes() []ASTNode {
	return []ASTNode{n.Block}
}
