package ir

type BasicBlock struct {
	Routine      *Routine
	Instructions []Instruction
	Terminator   Terminator

	// If this block belongs to at least one loop, Loop points to the
	// "deepest" applicable loop in the loop tree.
	Loop *Loop
}

func (b *BasicBlock) NewBuilder() *Builder {
	return &Builder{
		Block: b,
	}
}

func (b *BasicBlock) Successors() []*BasicBlock {
	// A block without a terminator isn't valid in a "final" graph,
	// but we tolerate it so that it's possible to work with
	// incomplete graphs that are still being constructed.
	if b.Terminator != nil {
		return b.Terminator.Successors()
	} else {
		return []*BasicBlock{}
	}
}
