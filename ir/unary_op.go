package ir

type UnaryOpType string

const (
	Not UnaryOpType = "not"

	Neg UnaryOpType = "neg" // negate

	Deref UnaryOpType = "deref" // dereference
)

type UnaryOp struct {
	register
	srcRange

	op  UnaryOpType
	val Value
}

func (i *UnaryOp) Mnemonic() string {
	return string(i.op)
}

func (i *UnaryOp) Operation() UnaryOpType {
	return i.op
}

func (i *UnaryOp) Operands(target []Value) []Value {
	return append(target, i.val)
}
