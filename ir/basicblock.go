package ir

type BasicBlock interface {
	Operand

	Successors() []BasicBlock
	Predecessors() []BasicBlock
	FirstInstruction() Instruction
	LastInstruction() Instruction
	Terminator() TerminatorInstruction
}
