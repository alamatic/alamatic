package ir

import (
	"github.com/alamatic/alamatic/diag"
)

// Node generically represents a node in the SSA graph.
//
// All nodes implement either Value, Instruction, or both. These more-specific
// interfaces should be preferred where appropriate.
type Node interface {
	SourceRange() *diag.SourceRange
	Routine() *Routine

	Operands(target []Value) []Value              // nil for non-Instruction nodes
	Referrers(target []Instruction) []Instruction // nil for non-Value nodes
}

type Value interface {
	// SourceRange returns a region of source code that closely corresponds
	// to this instruction, for use in diagnostics.
	SourceRange() *diag.SourceRange

	// Routine returns the routine that this value belongs to, or nil if
	// the value is a package global.
	Routine() *Routine

	// Referrers appends the instructions that have this value as an operand
	// to the given target (which may be nil) and returns it.
	//
	// Pass a non-nil slice only to avoid further memory allocation by
	// appending to a slice that has spare capacity.
	Referrers(target []Instruction) []Instruction
}

type Instruction interface {
	// Mnemonic returns a short name representing the type of instruction
	// represented. It is primarily for debug output, and so instruction
	// mnemonics are not intended to be part of the main user interface.
	Mnemonic() string

	// SourceRange returns a region of source code that closely corresponds
	// to this instruction, for use in diagnostics.
	SourceRange() *diag.SourceRange

	// Routine returns the routine that this instruction belongs to.
	Routine() *Routine

	// Block returns the basic block that this instruction belongs to.
	Block() *BasicBlock

	// Operands appends the instruction's operands to target (which may be
	// nil) and returns the result.
	//
	// Pass a non-nil slice only to avoid further memory allocation by
	// appending to a slice that has spare capacity.
	Operands(target []Value) []Value
}
