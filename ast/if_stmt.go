package ast

import (
	"github.com/alamatic/alamatic/diag"
	"github.com/alamatic/alamatic/ir"
)

type IfStmt struct {
	Clauses []*IfClause

	SourceRange *diag.SourceRange
}

func (s *IfStmt) Params() []interface{} {
	return []interface{}{}
}

func (s *IfStmt) ChildNodes() []ASTNode {
	ret := make([]ASTNode, len(s.Clauses))
	for i, c := range s.Clauses {
		ret[i] = c
	}
	return ret
}

func (s *IfStmt) BuildIR(scope *Scope, builder *ir.Builder) {
	afterBuilder := builder.NewBasicBlock()
	for _, clause := range s.Clauses {
		childScope := scope.NewChild()

		if clause.CondExpr == nil {
			// else clause
			clause.Block.BuildIR(childScope, builder)
			continue
		}

		condValue := clause.CondExpr.BuildIR(scope, builder)
		trueBuilder := builder.NewBasicBlock()
		falseBuilder := builder.NewBasicBlock()
		builder.Branch(condValue, trueBuilder.Block, falseBuilder.Block)
		clause.Block.BuildIR(childScope, trueBuilder)
		trueBuilder.Jump(afterBuilder.Block)
		builder.SwitchBasicBlock(falseBuilder.Block)
	}

	builder.Jump(afterBuilder.Block)
	builder.SwitchBasicBlock(afterBuilder.Block)
}

type IfClause struct {

	// CondExpr is the expression that must return true for the associated
	// block to be executed, nor nil if this is an "else" block.
	CondExpr Expression

	Block *StatementBlock
}

func (s *IfClause) Params() []interface{} {
	return []interface{}{}
}

func (s *IfClause) ChildNodes() []ASTNode {
	if s.CondExpr != nil {
		return []ASTNode{s.CondExpr, s.Block}
	} else {
		return []ASTNode{s.Block}
	}
}
