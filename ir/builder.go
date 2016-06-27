package ir

import (
	"fmt"
)

type Builder struct {
	Block *BasicBlock
}

func (b *Builder) append(instr Instruction) Value {
	if b.Block.Terminator != nil {
		// Should never happen
		panic(fmt.Errorf("can't append instruction: block already terminated"))
	}
	if term, ok := instr.(Terminator); ok {
		b.Block.Terminator = term
	} else {
		b.Block.Instructions = append(b.Block.Instructions, instr)
	}
	return instr
}

// NewBasicBlock creates and returns a new, empty BasicBlock that belongs
// to the same routine as this builder's own basic block.
func (b *Builder) NewBasicBlock() *BasicBlock {
	return b.Block.Routine.NewBasicBlock()
}

func (b *Builder) Branch(cond Value, trueTarget, falseTarget *BasicBlock) Value {
	return b.append(&Branch{
		Cond:        cond,
		TrueTarget:  trueTarget,
		FalseTarget: falseTarget,
	})
}

func (b *Builder) Equals(lhs Value, rhs Value) Value {
	return b.append(&BinaryOp{
		OpCode: EqualsOp,
		LHS:    lhs,
		RHS:    rhs,
	})
}

func (b *Builder) Jump(target *BasicBlock) Value {
	return b.append(&Jump{target})
}

func (b *Builder) Not(operand Value) Value {
	return b.append(&UnaryOp{
		OpCode:  NotOp,
		Operand: operand,
	})
}

func (b *Builder) Return(result Value) Value {
	return b.append(&Return{result})
}
