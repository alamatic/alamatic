package ast

import (
	"testing"
)

func TestParseIfStmt(t *testing.T) {
	type testCase struct {
		input    string
		expected *nodeSpec
	}

	cases := []testCase{
		{
			`
if null:
    pass
elif null:
    pass
else:
    pass
`,
			&nodeSpec{
				TypeName: "StatementBlock",
				Params:   []interface{}{},
				ChildNodes: []*nodeSpec{
					{
						TypeName: "IfStmt",
						Params:   []interface{}{},
						ChildNodes: []*nodeSpec{
							{
								TypeName: "IfClause",
								Params:   []interface{}{},
								ChildNodes: []*nodeSpec{
									{
										TypeName:   "LiteralNullExpr",
										Params:     []interface{}{},
										ChildNodes: []*nodeSpec{},
									},
									{
										TypeName: "StatementBlock",
										Params:   []interface{}{},
										ChildNodes: []*nodeSpec{
											{
												TypeName:   "PassStmt",
												Params:     []interface{}{},
												ChildNodes: []*nodeSpec{},
											},
										},
									},
								},
							},
							{
								TypeName: "IfClause",
								Params:   []interface{}{},
								ChildNodes: []*nodeSpec{
									{
										TypeName:   "LiteralNullExpr",
										Params:     []interface{}{},
										ChildNodes: []*nodeSpec{},
									},
									{
										TypeName: "StatementBlock",
										Params:   []interface{}{},
										ChildNodes: []*nodeSpec{
											{
												TypeName:   "PassStmt",
												Params:     []interface{}{},
												ChildNodes: []*nodeSpec{},
											},
										},
									},
								},
							},
							{
								TypeName: "IfClause",
								Params:   []interface{}{},
								ChildNodes: []*nodeSpec{
									{
										TypeName: "StatementBlock",
										Params:   []interface{}{},
										ChildNodes: []*nodeSpec{
											{
												TypeName:   "PassStmt",
												Params:     []interface{}{},
												ChildNodes: []*nodeSpec{},
											},
										},
									},
								},
							},
						},
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
