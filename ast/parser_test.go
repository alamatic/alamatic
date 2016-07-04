package ast

import (
	"math/big"
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

func TestParseFactorExprs(t *testing.T) {
	type testCase struct {
		input    string
		expected *nodeSpec
	}

	cases := []testCase{
		{
			// Simple symbol expression
			"a",
			&nodeSpec{
				TypeName:   "SymbolExpr",
				Params:     []interface{}{"a"},
				ChildNodes: []*nodeSpec{},
			},
		},
		{
			"true",
			&nodeSpec{
				TypeName:   "LiteralBoolExpr",
				Params:     []interface{}{true},
				ChildNodes: []*nodeSpec{},
			},
		},
		{
			"false",
			&nodeSpec{
				TypeName:   "LiteralBoolExpr",
				Params:     []interface{}{false},
				ChildNodes: []*nodeSpec{},
			},
		},
		{
			"null",
			&nodeSpec{
				TypeName:   "LiteralNullExpr",
				Params:     []interface{}{},
				ChildNodes: []*nodeSpec{},
			},
		},
		{
			"1",
			&nodeSpec{
				TypeName:   "LiteralNumberExpr",
				Params:     []interface{}{big.NewFloat(1)},
				ChildNodes: []*nodeSpec{},
			},
		},
		{
			"1.5",
			&nodeSpec{
				TypeName:   "LiteralNumberExpr",
				Params:     []interface{}{big.NewFloat(1.5)},
				ChildNodes: []*nodeSpec{},
			},
		},
		{
			"0b0100",
			&nodeSpec{
				TypeName:   "LiteralNumberExpr",
				Params:     []interface{}{big.NewFloat(4)},
				ChildNodes: []*nodeSpec{},
			},
		},
		{
			"0xbeef",
			&nodeSpec{
				TypeName:   "LiteralNumberExpr",
				Params:     []interface{}{big.NewFloat(48879)},
				ChildNodes: []*nodeSpec{},
			},
		},
		{
			// When used in an expression context (vs. a statement context)
			// "continue" is parsed as a variable.
			// (this is not idiomatic, but is allowed.)
			"continue",
			&nodeSpec{
				TypeName:   "SymbolExpr",
				Params:     []interface{}{"continue"},
				ChildNodes: []*nodeSpec{},
			},
		},
	}

	for _, testCase := range cases {
		got := testParseSourceExpr(testCase.input)
		assertNodeSpecEqual(t, got, testCase.expected)
	}
}
