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
// to the same routine as this builder's own basic block. If our basic block
// belongs to a loop then the new block will belong to the same loop as
// part of its body.
func (b *Builder) NewBasicBlock() *BasicBlock {
	newBlock := b.Block.Routine.NewBasicBlock()

	if b.Block.Loop != nil {
		newBlock.Loop = b.Block.Loop
		b.Block.Loop.Body[newBlock] = true
	}

	return newBlock
}

// NewLoop creates a new Loop belonging to the same routine as this builder's
// basic block and then returns the new loop's header block. If our
// basic block itself belongs to a loop then that loop will be the new
// loop's parent.
//
// This is similar to NewBasicBlock except it also creates a new loop
// context. This should be used when lowering loops from the source language
// so that the loop tree can be produced along with the control flow graph.
func (b *Builder) NewLoop() *BasicBlock {
	var loop *Loop
	if b.Block.Loop != nil {
		loop = b.Block.Loop.NewChild()
	} else {
		loop = b.Block.Routine.NewLoop()
	}
	return loop.Header
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
