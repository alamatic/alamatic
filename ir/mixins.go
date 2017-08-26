package ir

import (
	"github.com/alamatic/alamatic/diag"
)

// instruction is a mixin embedded in all instructions that provides the
// Block method.
type instruction struct {
	block *BasicBlock
}

func (i *instruction) Block() *BasicBlock {
	return i.block
}

func (i *instruction) Routine() *Routine {
	return i.block.routine
}

// value is a mixin embedded in all values that provides the Referrers method.
type value struct {
	referrers map[Instruction]struct{}
}

func (v *value) Referrers(target []Instruction) []Instruction {
	num := len(v.referrers)
	if cap(target)-len(target) < num {
		// extend target to the needed capacity all at once, rather
		// than potentially allocating multiple times as we append below.
		wantCap := len(target) + (2 * num)
		newTarget := make([]Instruction, len(target), wantCap)
		copy(newTarget, target)
		target = newTarget
	}
	for instr := range v.referrers {
		target = append(target, instr)
	}
	return target
}

// register is a mixin embedded in all nodes that are both values _and_
// instructions, representing an SSA virtual register. It implements most of
// the Value interface.
type register struct {
	instruction
	value
}

// srcRange is a mixin embedded in all nodes to provide their SourceRange
// methods.

type srcRange struct {
	sourceRange *diag.SourceRange
}

func (r *srcRange) SourceRange() *diag.SourceRange {
	return r.sourceRange
}
