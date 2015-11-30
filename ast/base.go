package ast

type ASTNode interface {
	Params() []interface{}
	ChildNodes() []ASTNode
}

// baseASTNode can be embedded into a struct to get a default, "empty"
// implementation of ASTNode.
type baseASTNode struct{}

func (n *baseASTNode) Params() []interface{} {
	return []interface{}{}
}

func (n *baseASTNode) ChildNodes() []ASTNode {
	return []ASTNode{}
}
