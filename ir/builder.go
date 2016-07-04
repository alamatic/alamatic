package ir

import (
	"fmt"

	"github.com/alamatic/alamatic/diag"
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

// NewBasicBlock creates a new, empty BasicBlock that belongs
// to the same routine as this builder's own basic block, and returns
// a builder for it. If our basic block belongs to a loop then the new
// block will belong to the same loop as part of its body.
func (b *Builder) NewBasicBlock() *Builder {
	newBlock := b.Block.Routine.NewBasicBlock()

	if b.Block.Loop != nil {
		newBlock.Loop = b.Block.Loop
		b.Block.Loop.Body[newBlock] = true
	}

	return newBlock.NewBuilder()
}

// SwitchBasicBlock changes this builder to append to a different basic
// block.
//
// This should be used when lowering branching AST nodes such as loops
// to IR, so that once that node has been lowered additional lowering will
// append to the block that follows the branch(es).
func (b *Builder) SwitchBasicBlock(newBlock *BasicBlock) {
	b.Block = newBlock
}

// NewLoop creates a new Loop belonging to the same routine as this builder's
// basic block and then returns a builder for the new loop's header block. If
// our basic block itself belongs to a loop then that loop will be the new
// loop's parent.
//
// This is similar to NewBasicBlock except it also creates a new loop
// context. This should be used when lowering loops from the source language
// so that the loop tree can be produced along with the control flow graph.
func (b *Builder) NewLoop() *Builder {
	var loop *Loop
	if b.Block.Loop != nil {
		loop = b.Block.Loop.NewChild()
	} else {
		loop = b.Block.Routine.NewLoop()
	}
	return loop.Header.NewBuilder()
}

func (b *Builder) Add(lhs, rhs Value) Value {
	return b.append(&BinaryOp{
		OpCode: AddOp,
		LHS:    lhs,
		RHS:    rhs,
	})
}

func (b *Builder) And(lhs, rhs Value) Value {
	return b.append(&BinaryOp{
		OpCode: AndOp,
		LHS:    lhs,
		RHS:    rhs,
	})
}

func (b *Builder) Branch(cond Value, trueTarget, falseTarget *BasicBlock) Value {
	return b.append(&Branch{
		Cond:        cond,
		TrueTarget:  trueTarget,
		FalseTarget: falseTarget,
	})
}

func (b *Builder) Call(
	callee Value,
	posArgs []Value,
	namedArgs map[string]Value,
	posExpanderArg Value,
	namedExpanderArg Value,
) Value {
	return b.append(&CallOp{
		Callee:           callee,
		PosArgs:          posArgs,
		NamedArgs:        namedArgs,
		PosExpanderArg:   posExpanderArg,
		NamedExpanderArg: namedExpanderArg,
	})
}

func (b *Builder) Concat(lhs, rhs Value) Value {
	return b.append(&BinaryOp{
		OpCode: ConcatOp,
		LHS:    lhs,
		RHS:    rhs,
	})
}

func (b *Builder) Convert(value, targetType Value) Value {
	return b.append(&ConvertOp{
		Value: value,
		Type:  targetType,
	})
}

func (b *Builder) Diagnostics(diags []*diag.Diagnostic) Value {
	return b.append(&DiagnosticOp{
		Diagnostics: diags,
	})
}

func (b *Builder) Divide(lhs, rhs Value) Value {
	return b.append(&BinaryOp{
		OpCode: DivideOp,
		LHS:    lhs,
		RHS:    rhs,
	})
}

func (b *Builder) Equals(lhs, rhs Value) Value {
	return b.append(&BinaryOp{
		OpCode: EqualsOp,
		LHS:    lhs,
		RHS:    rhs,
	})
}

func (b *Builder) ExclusiveOr(lhs, rhs Value) Value {
	return b.append(&BinaryOp{
		OpCode: ExclusiveOrOp,
		LHS:    lhs,
		RHS:    rhs,
	})
}

func (b *Builder) GetAttr(container, name Value) Value {
	return b.append(&GetAttrOp{
		Container: container,
		Name:      name,
	})
}

func (b *Builder) GetIndex(container, index Value) Value {
	return b.append(&GetIndexOp{
		Container: container,
		Index:     index,
	})
}

func (b *Builder) GreaterThanEqual(lhs, rhs Value) Value {
	return b.append(&BinaryOp{
		OpCode: GreaterThanEqualOp,
		LHS:    lhs,
		RHS:    rhs,
	})
}

func (b *Builder) GreaterThan(lhs, rhs Value) Value {
	return b.append(&BinaryOp{
		OpCode: GreaterThanOp,
		LHS:    lhs,
		RHS:    rhs,
	})
}

func (b *Builder) Jump(target *BasicBlock) Value {
	return b.append(&Jump{target})
}

func (b *Builder) LessThanEqual(lhs, rhs Value) Value {
	return b.append(&BinaryOp{
		OpCode: LessThanEqualOp,
		LHS:    lhs,
		RHS:    rhs,
	})
}

func (b *Builder) LessThan(lhs, rhs Value) Value {
	return b.append(&BinaryOp{
		OpCode: LessThanOp,
		LHS:    lhs,
		RHS:    rhs,
	})
}

func (b *Builder) Load(location Value) Value {
	return b.append(&LoadOp{
		Location: location,
	})
}

func (b *Builder) Modulo(lhs, rhs Value) Value {
	return b.append(&BinaryOp{
		OpCode: ModuloOp,
		LHS:    lhs,
		RHS:    rhs,
	})
}

func (b *Builder) Multiply(lhs, rhs Value) Value {
	return b.append(&BinaryOp{
		OpCode: MultiplyOp,
		LHS:    lhs,
		RHS:    rhs,
	})
}

func (b *Builder) Not(operand Value) Value {
	return b.append(&UnaryOp{
		OpCode:  NotOp,
		Operand: operand,
	})
}

func (b *Builder) Or(lhs, rhs Value) Value {
	return b.append(&BinaryOp{
		OpCode: OrOp,
		LHS:    lhs,
		RHS:    rhs,
	})
}

func (b *Builder) Return(result Value) Value {
	return b.append(&Return{result})
}

func (b *Builder) Shift(val, shiftAmount Value) Value {
	return b.append(&BinaryOp{
		OpCode: ShiftOp,
		LHS:    val,
		RHS:    shiftAmount,
	})
}

func (b *Builder) Store(value, location Value) Value {
	return b.append(&StoreOp{
		Value:    value,
		Location: location,
	})
}

func (b *Builder) Subtract(lhs, rhs Value) Value {
	return b.append(&BinaryOp{
		OpCode: SubtractOp,
		LHS:    lhs,
		RHS:    rhs,
	})
}
