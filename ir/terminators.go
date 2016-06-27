package ir

type Terminator interface {
	Instruction

	Successors() []*BasicBlock
}

type Jump struct {
	Target *BasicBlock
}

func (i *Jump) Mnemonic() string {
	return "jump"
}

func (i *Jump) Arguments() []Value {
	return []Value{i.Target}
}

func (i *Jump) Successors() []*BasicBlock {
	return []*BasicBlock{i.Target}
}

type Branch struct {
	Cond        Value
	TrueTarget  *BasicBlock
	FalseTarget *BasicBlock
}

func (i *Branch) Mnemonic() string {
	return "branch"
}

func (i *Branch) Arguments() []Value {
	return []Value{i.Cond, i.TrueTarget, i.FalseTarget}
}

func (i *Branch) Successors() []*BasicBlock {
	return []*BasicBlock{i.TrueTarget, i.FalseTarget}
}

type Return struct {
	Result Value
}

func (i *Return) Mnemonic() string {
	return "return"
}

func (i *Return) Arguments() []Value {
	return []Value{i.Result}
}

func (i *Return) Successors() []*BasicBlock {
	return []*BasicBlock{}
}
