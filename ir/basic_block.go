package ir

// BasicBlock represents a basic block within a routine. That is, a sequence
// of non-control-flow instructions with a single terminator that transfers
// control to other blocks.
type BasicBlock struct {
	routine      *Routine
	instrs       []Instruction
	term         Instruction
	preds, succs []*BasicBlock
}

// Routine returns a pointer to the routine that this basic block belongs to.
func (b *BasicBlock) Routine() *Routine {
	return b.routine
}

// Instructions appends the block's non-terminator instructions to the given
// slice (which may be nil) and returns the result.
func (b *BasicBlock) Instructions(target []Instruction) []Instruction {
	return append(target, b.instrs...)
}

// Terminator returns the block's terminator instruction.
func (b *BasicBlock) Terminator() Instruction {
	return b.term
}

// Predecessors appends the block's predecessors, in order, to the given
// slice (which may be nil) and returns the result.
//
// The order of predecessors is significant for blocks containing phi
// instructions.
func (b *BasicBlock) Predecessors(target []*BasicBlock) []*BasicBlock {
	return append(target, b.preds...)
}

// Successors appends the block's successors, in order, to the given
// slice (which may be nil) and returns the result.
//
// The order of successors is significant for blocks with conditional
// terminators.
func (b *BasicBlock) Successors(target []*BasicBlock) []*BasicBlock {
	return append(target, b.succs...)
}
