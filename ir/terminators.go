package ir

type TerminatorInstruction interface {
	Instruction
}

type retInst struct {
	mnemonic "ret"

	Value Value
}

type gotoInst struct {
	mnemonic "goto"

	Target BasicBlock
}

type branchInst struct {
	mnemonic "branch"

	gotoInst
	Condition Value
}
