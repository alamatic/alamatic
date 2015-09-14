package ir

type loadVarInst struct {
	mnemonic "load"

	VarIndex int
}

type storeVarInst struct {
	mnemonic "store"

	VarIndex int
	Value    Value
}
