package ir

type Instruction interface {
	Value

	Mnemonic() string
}

type BinaryOpCode string

const EqualsOp = BinaryOpCode("equals")

type BinaryOp struct {
	OpCode BinaryOpCode
	LHS    Value
	RHS    Value
}

func (i *BinaryOp) Mnemonic() string {
	return string(i.OpCode)
}

func (i *BinaryOp) Arguments() []Value {
	return []Value{i.LHS, i.RHS}
}

type UnaryOpCode string

const NotOp = UnaryOpCode("not")

type UnaryOp struct {
	OpCode  UnaryOpCode
	Operand Value
}

func (i *UnaryOp) Mnemonic() string {
	return string(i.OpCode)
}

func (i *UnaryOp) Arguments() []Value {
	return []Value{i.Operand}
}
