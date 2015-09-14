package ir

type Routine interface {
	Operand

	Arguments() []Argument
}

type Argument interface {
	Operand
}

type loadArgInst struct {
	mnemonic "loadarg"

	ArgumentIndex int
}
