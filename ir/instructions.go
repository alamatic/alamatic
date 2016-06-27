package ir

type Instruction interface {
	Value

	Mnemonic() string
}

type BinaryOpCode string

const AddOp = BinaryOpCode("add")
const AndOp = BinaryOpCode("and")
const ConcatOp = BinaryOpCode("concat")
const DivideOp = BinaryOpCode("divide")
const EqualsOp = BinaryOpCode("equals")
const ExclusiveOrOp = BinaryOpCode("xor")
const GreaterThanEqualOp = BinaryOpCode("gte")
const GreaterThanOp = BinaryOpCode("gt")
const LessThanEqualOp = BinaryOpCode("lte")
const LessThanOp = BinaryOpCode("lt")
const ModuloOp = BinaryOpCode("modulo")
const MultiplyOp = BinaryOpCode("multiply")
const OrOp = BinaryOpCode("or")
const ShiftOp = BinaryOpCode("shift")
const SubtractOp = BinaryOpCode("subtract")

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

type LoadOp struct {
	Location Value
}

func (i *LoadOp) Mnemonic() string {
	return "load"
}

func (i *LoadOp) Arguments() []Value {
	return []Value{i.Location}
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

type StoreOp struct {
	Value    Value
	Location Value
}

func (i *StoreOp) Mnemonic() string {
	return "store"
}

func (i *StoreOp) Arguments() []Value {
	return []Value{i.Value, i.Location}
}
