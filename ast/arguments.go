package ast

type Arguments struct {
	PositionalExprs []Expression
	NamedExprs      map[string]Expression
}

func (n *Arguments) Params() []interface{} {
	ret := make([]interface{}, 0, len(n.PositionalExprs)+len(n.NamedExprs))
	for i, _ := range n.PositionalExprs {
		ret = append(ret, i)
	}
	for k, _ := range n.NamedExprs {
		ret = append(ret, k)
	}
	return ret
}

func (n *Arguments) ChildNodes() []ASTNode {
	ret := make([]ASTNode, 0, len(n.PositionalExprs)+len(n.NamedExprs))
	for _, e := range n.PositionalExprs {
		ret = append(ret, e)
	}
	for _, e := range n.NamedExprs {
		ret = append(ret, e)
	}
	return ret
}
