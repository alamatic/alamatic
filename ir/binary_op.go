package ir

type BinaryOpType string

const (
	Add BinaryOpType = "add" // add
	Sub BinaryOpType = "sub" // subtract
	Mul BinaryOpType = "mul" // multiply
	Div BinaryOpType = "div" // divide
	Mod BinaryOpType = "mod" // modulo

	And BinaryOpType = "and"
	Or  BinaryOpType = "or"
	Xor BinaryOpType = "xor"

	Cat BinaryOpType = "cat" // concatenate

	Eq  BinaryOpType = "eq"
	NE  BinaryOpType = "ne"
	LT  BinaryOpType = "lt"
	GT  BinaryOpType = "gt"
	LTE BinaryOpType = "lte"
	GTE BinaryOpType = "gte"
)

type BinaryOp struct {
	register
	srcRange

	op  BinaryOpType
	lhs Value
	rhs Value
}

func (i *BinaryOp) Mnemonic() string {
	return string(i.op)
}

func (i *BinaryOp) Operation() BinaryOpType {
	return i.op
}

func (i *BinaryOp) Operands(target []Value) []Value {
	target = append(target, i.lhs)
	target = append(target, i.rhs)
	return target
}
