package ast

import (
	"reflect"
	"testing"
)

// Some helper structs to describe desired tree structures in tests.
//
// Used like this:
//
// &nodeSpec{
//     "StatementBlock",     // Node type name
//     []interface{}{},      // Node params
//     []*nodeSpec{          // Child nodes
//         "PassStmt",
//         []interface{}{},
//         []*node{},
//     }
// }

type nodeSpec struct {
	TypeName   string
	Params     []interface{}
	ChildNodes []*nodeSpec
}

func makeNodeSpec(node ASTNode) *nodeSpec {
	nodeType := reflect.TypeOf(node).Elem()
	childNodes := node.ChildNodes()
	ret := &nodeSpec{
		TypeName:   nodeType.Name(),
		Params:     node.Params(),
		ChildNodes: make([]*nodeSpec, len(childNodes)),
	}

	for i, childNode := range childNodes {
		ret.ChildNodes[i] = makeNodeSpec(childNode)
	}

	return ret
}

type stubNode struct {
	params     []interface{}
	childNodes []ASTNode
}

func (n *stubNode) Params() []interface{} {
	return n.params
}

func (n *stubNode) ChildNodes() []ASTNode {
	return n.childNodes
}

func TestMakeNodeSpec(t *testing.T) {
	input := &stubNode{
		params: []interface{}{1, 2, "hi"},
		childNodes: []ASTNode{
			&stubNode{
				params:     []interface{}{},
				childNodes: []ASTNode{},
			},
			&stubNode{
				params: []interface{}{true},
				childNodes: []ASTNode{
					&stubNode{
						params:     []interface{}{},
						childNodes: []ASTNode{},
					},
				},
			},
		},
	}
	expected := &nodeSpec{
		"stubNode",
		[]interface{}{1, 2, "hi"},
		[]*nodeSpec{
			&nodeSpec{
				"stubNode",
				[]interface{}{},
				[]*nodeSpec{},
			},
			&nodeSpec{
				"stubNode",
				[]interface{}{true},
				[]*nodeSpec{
					&nodeSpec{
						"stubNode",
						[]interface{}{},
						[]*nodeSpec{},
					},
				},
			},
		},
	}
	got := makeNodeSpec(input)
	if !reflect.DeepEqual(expected, got) {
		t.Errorf("Constructed node spec does not match.\n\t got: %#v\n\twant: %#v", got, expected)
	}
}
