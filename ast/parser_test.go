package ast

import (
	"testing"
)

/*func TestParseIfStmt(t *testing.T) {
	got := testParseSource(`
if true:
    return 1
elif false:
    return 2
else:
    return 3
`)
	t.Logf("%#v\n", got)
}*/

func TestParseLoopCtrlStmts(t *testing.T) {
	type testCase struct {
		input    string
		expected *nodeSpec
	}

	cases := []testCase{
		{
			"continue",
			&nodeSpec{
				TypeName: "StatementBlock",
				Params:   []interface{}{},
				ChildNodes: []*nodeSpec{
					{
						TypeName:   "ContinueStmt",
						Params:     []interface{}{},
						ChildNodes: []*nodeSpec{},
					},
				},
			},
		},
		{
			"break",
			&nodeSpec{
				TypeName: "StatementBlock",
				Params:   []interface{}{},
				ChildNodes: []*nodeSpec{
					{
						TypeName:   "BreakStmt",
						Params:     []interface{}{},
						ChildNodes: []*nodeSpec{},
					},
				},
			},
		},
	}

	for _, testCase := range cases {
		got := testParseSource(testCase.input)
		assertNodeSpecEqual(t, got, testCase.expected)
	}
}
