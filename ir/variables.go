package ir

type loadVarInst struct {
	mnemonic "loadvar"

	VarIndex int
}

type storeVarInst struct {
	mnemonic "storevar"

	VarIndex int
	Value    Value
}
