package ir

// Load is an instruction and value that loads the value stored in a given
// memory location and returns it.
type Load struct {
	register
	srcRange

	Source Value
}

func (i *Load) Mnemonic() string { return "load" }

func (i *Load) Operands(target []Value) []Value {
	return append(target, i.Source)
}

type Store struct {
	instruction
	srcRange

	Value  Value
	Target Value
}

func (i *Store) Mnemonic() string { return "store" }

func (i *Store) Operands(target []Value) []Value {
	target = append(target, i.Value)
	target = append(target, i.Target)
	return target
}
